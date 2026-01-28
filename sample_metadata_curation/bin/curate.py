import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import reverse_geocode

from .constants import LOCATION_KEYS, MISSING_VALUES, REVERSE_GEOCODER_MISSING_CC
from .sample_parser import load_json, parse_arguments

"""
regex for lat lon e.g.
match = 55.62115 N 8.2849 E
lat = 55.62115
lat_dir = N
lon = 8.2849
lon_dir = E
"""
LATLON_COORD_RE = re.compile(
    r"""
    ^\s*
    (?P<lat>[-+]?\d+(?:[.,]\d+)?)\s*(?P<lat_dir>[NS])?
    [\s,;/\-]+
    (?P<lon>[-+]?\d+(?:[.,]\d+)?)\s*(?P<lon_dir>[EW])?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

REJECTED_LOCATION_CHARACTERS = set("@#$%^*=+<>[]{}|\\~")


def reverse_country_code(latitude: float, longitude: float) -> Optional[str]:
    try:
        hit = reverse_geocode.get((latitude, longitude))
        if not hit:
            return None
        return hit.get("country_code")
    except AssertionError:
        return None


class SampleCurator:
    def __init__(
        self,
        resources_dir: Optional[Path] = None,
        biome_keys: Optional[List[str]] = None,
    ):
        if resources_dir is None:
            resources_dir = Path(__file__).parent.parent / "resources"

        self.mapping_csv = resources_dir / "country_to_cc_mapping.csv"
        self.oceans_txt = resources_dir / "oceans_and_seas.txt"
        self.name_to_cc, self.name_to_canonical = self.load_country_mapping()
        self.oceans_and_seas = self.load_oceans_and_seas()
        self.biome_keys = (
            [self.normalize_key(k) for k in biome_keys] if biome_keys else []
        )

    def load_oceans_and_seas(self) -> set:
        oceans = set()
        if self.oceans_txt.exists():
            with self.oceans_txt.open(newline="", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        oceans.add(name)
        return oceans

    @staticmethod
    def normalize_key(key: str) -> str:
        """
        simplify special characters in key names
        """
        s = str(key).strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)  # non-alphanumerics -> underscores
        s = re.sub(r"_+", "_", s)  # collapse multiple underscores
        s = s.strip("_")  # trim leading/trailing underscores
        return s

    def standardise_keys(self, sample_json: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Convert BioSamples JSON sections 'characteristics' and 'structured data'
        into a simple dict:
          normalized_key -> first item's 'text' (for characteristics)
                            or 'value' (for structured data)
        """
        out = {}

        # 1. Process characteristics
        chars = sample_json.get("characteristics") or {}
        for key, items in chars.items():
            norm_key = self.normalize_key(key)
            if isinstance(items, list) and items:
                first = items[0]
                val = first.get("text") if isinstance(first, dict) else str(first)
                out[norm_key] = val
            else:
                out[norm_key] = None

        # 2. Process structuredData
        structured_data = sample_json.get("structuredData") or []
        for entry in structured_data:
            content_list = entry.get("content") or []
            for content in content_list:
                for key, val_obj in content.items():
                    norm_key = self.normalize_key(key)
                    if isinstance(val_obj, dict):
                        val = val_obj.get("value")
                        if val is not None:
                            out[norm_key] = str(val)
                    elif val_obj is not None:
                        out[norm_key] = str(val_obj)
        return out

    @staticmethod
    def _apply_direction(value: float, direction: Optional[str]) -> float:
        if not direction:
            return value
        d = direction.upper()
        if d in ("S", "W"):
            return -abs(value)
        return abs(value)  # N/E

    def _parse_single_coord(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        s = str(value).strip()
        m = re.match(r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*([NSEW])?\s*$", s, re.IGNORECASE)
        if not m:
            return None
        num = float(m.group(1).replace(",", "."))
        dir_ = m.group(2)
        return self._apply_direction(num, dir_) if dir_ else num

    @staticmethod
    def _first_present_key(d: Dict[str, Any], keys: List[str]) -> Optional[str]:
        for k in keys:
            if k in d and d[k] not in (None, ""):
                if str(d[k]).lower() not in MISSING_VALUES:
                    return k
        return None

    @staticmethod
    def sanity_check_location(
        location: Optional[str], latitude: Optional[float], longitude: Optional[float]
    ) -> bool:
        if location is None:
            return False

        s = str(location).strip()
        if s.lower() in MISSING_VALUES:
            return False

        # Too short/too long - not sure about this one
        if len(s) < 2 or len(s) > 200:
            return False

        for ch in s:
            # no numbers
            if ch.isdigit():
                return False
            if ch in REJECTED_LOCATION_CHARACTERS:
                return False

        # Reject lots of repeated characters (often random)
        if re.search(r"(.)\1\1\1", s):  # 4 of the same char in a row
            return False

        return True

    def load_country_mapping(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        name_to_cc = {}
        name_to_canonical = {}

        with self.mapping_csv.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                input_name, canonical_name, cc = row[0], row[1], row[2]
                name_to_cc[input_name] = cc
                name_to_canonical[input_name] = canonical_name
                # Also index by canonical name to ensure it's always found
                if canonical_name not in name_to_cc:
                    name_to_cc[canonical_name] = cc
                if canonical_name not in name_to_canonical:
                    name_to_canonical[canonical_name] = canonical_name
        return name_to_cc, name_to_canonical

    def infer_reported_country_code(
        self,
        reported_location: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Check for location based on INSDC controlled vocab
        and try to get ISO 2 digit country code
        """
        if not reported_location:
            return None, None, None

        loc = reported_location.strip()

        # exact match to ENA/INSDC label
        if loc in self.name_to_cc:
            region_cc = self.name_to_cc.get(loc)
            region = loc
            locality = None
            return region, locality, region_cc

        if loc in self.oceans_and_seas:
            return loc, None, None

        """
        INSDC location format
        Value format “<geo_loc_name>[:<region>][, <locality>]” where
        geographic location name (geo_loc_name) is any value from the
        controlled vocabulary

        Example

        /geo_loc_name=”Canada:Vancouver”
        /geo_loc_name=”France:Cote d’Azur, Antibes”
        /geo_loc_name=”Atlantic Ocean:Charlie Gibbs Fracture Zone”
        """
        if ":" in loc:
            region = loc.split(":")[0].strip()
            if region in self.name_to_cc:
                region_cc = self.name_to_cc.get(region)
                locality = loc.split(":")[1].strip()
                return region, locality, region_cc
            if region in self.oceans_and_seas:
                locality = loc.split(":")[1].strip()
                return region, locality, None
        return None, None, None

    def geo_consistency_check(
        self,
        reported_location: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> Dict[str, Any]:
        """
        Check if reported location matches reverse geocoder result.
        Several levels of reporting to account for mismatches in data sources
        """
        out = {
            "geo_check_status": "SKIP",
            "geo_check_reason": None,
            "reported_country_code": None,
            "reverse_country_code": None,
            "region": None,
            "locality": None,
        }

        region, locality, reported_cc = self.infer_reported_country_code(
            reported_location
        )
        out["reported_country_code"] = reported_cc
        out["region"] = region
        out["locality"] = locality

        if region in self.oceans_and_seas:
            out["geo_check_status"] = "PASS"
            out["geo_check_reason"] = "ocean_or_sea"
            return out

        if latitude is None or longitude is None:
            out["geo_check_status"] = "SKIP"
            out["geo_check_reason"] = "no_coordinates"
            return out

        reverse_cc = reverse_country_code(latitude, longitude)
        out["reverse_country_code"] = reverse_cc

        if not reported_cc:
            out["geo_check_status"] = "SKIP"
            out["geo_check_reason"] = "no_reported_country_code"
            return out

        # reverse geocoder couldn't determine
        if not reverse_cc:
            out["geo_check_status"] = "WARN"
            out["geo_check_reason"] = "reverse_geocoder_no_result"
            return out

        # reverse geocoder is missing some ISO codes
        if reported_cc in REVERSE_GEOCODER_MISSING_CC:
            out["geo_check_status"] = "WARN"
            out["geo_check_reason"] = "reported_cc_not_supported_by_reverse_geocoder"
            return out

        if reverse_cc == reported_cc:
            out["geo_check_status"] = "PASS"
            out["geo_check_reason"] = "match"
        else:
            out["geo_check_status"] = "FAIL"
            out["geo_check_reason"] = "country_mismatch"

        return out

    def curate_sample(self, sample_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a BioSamples JSON dictionary and returns a cleaned dictionary
        with extracted region, locality, latitude, longitude and reasons
        for pass or failed sanity check
        """
        cleaned_dict = self.standardise_keys(sample_json)

        result = {
            "accession": sample_json.get("accession"),
            "location": None,
            "latitude": None,
            "longitude": None,
        }

        lat = None
        lon = None

        # try combined lat_lon
        lat_lon_key = self._first_present_key(cleaned_dict, LOCATION_KEYS["lat_lon"])
        if lat_lon_key:
            lat_lon_str = str(cleaned_dict[lat_lon_key]).strip()
            m = LATLON_COORD_RE.match(lat_lon_str)
            if m:
                lat = self._apply_direction(
                    float(m.group("lat").replace(",", ".")), m.group("lat_dir")
                )
                lon = self._apply_direction(
                    float(m.group("lon").replace(",", ".")), m.group("lon_dir")
                )

        # Individual fields if not found yet
        if lat is None:
            lat_key = self._first_present_key(cleaned_dict, LOCATION_KEYS["lat"])
            if lat_key:
                lat = self._parse_single_coord(cleaned_dict[lat_key])

        if lon is None:
            lon_key = self._first_present_key(cleaned_dict, LOCATION_KEYS["lon"])
            if lon_key:
                lon = self._parse_single_coord(cleaned_dict[lon_key])

        # Validate ranges and try switching if invalid otherwise set both as None
        if lat is not None and lon is not None:
            is_valid = abs(lat) <= 90 and abs(lon) <= 180
            if is_valid:
                result["latitude"] = lat
                result["longitude"] = lon
            else:
                # Try switching
                if abs(lon) <= 90 and abs(lat) <= 180:
                    result["latitude"] = lon
                    result["longitude"] = lat
                else:
                    result["latitude"] = None
                    result["longitude"] = None

        loc_key = self._first_present_key(cleaned_dict, LOCATION_KEYS["location"])
        if loc_key:
            is_location = self.sanity_check_location(
                cleaned_dict[loc_key], result["latitude"], result["longitude"]
            )
            if is_location:
                result["location"] = cleaned_dict[loc_key]
            else:
                result["location"] = None

        for key, value in cleaned_dict.items():
            if (
                key not in LOCATION_KEYS["lat_lon"]
                and key not in LOCATION_KEYS["location"]
                and key not in LOCATION_KEYS["lat"]
                and key not in LOCATION_KEYS["lon"]
            ):
                result[key] = value

        # Biome extraction
        if self.biome_keys:
            biome_values = []
            for bk in self.biome_keys:
                if bk in cleaned_dict:
                    biome_values.append(cleaned_dict.get(bk))
            if biome_values:
                result["biome"] = ";".join(biome_values)

        geo = self.geo_consistency_check(
            result["location"], result["latitude"], result["longitude"]
        )
        result.update(geo)

        # replace user supplied location with a curated region
        if geo.get("geo_check_status") == "FAIL":
            result["region"] = None
        result.pop("location", None)

        return result


def curate_biosample(
    input_data: Any, biome_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Curate one biosample
    Input can be a BioSamples JSON dict, a JSON string, or a path to a JSON file.
    """
    if isinstance(input_data, (str, os.PathLike)):
        sample_json = load_json(str(input_data))
    else:
        sample_json = input_data

    if not sample_json:
        return {}

    curator = SampleCurator(biome_keys=biome_keys)
    return curator.curate_sample(sample_json)


def main():
    args = parse_arguments()
    biome_keys = args.biome.split(",") if args.biome else None
    result = curate_biosample(args.sample_json, biome_keys=biome_keys)
    if result:
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
