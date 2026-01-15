import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

from .constants import LOCATION_KEYS, MISSING_VALUES
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


class SampleCurator:
    """
    Independent curator for BioSamples JSON data.
    Extracts and cleans location, latitude, and longitude.
    """

    def __init__(self):
        pass

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
        print(m.groups())
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
    def sanity_check_location(value: Optional[str]) -> bool:
        if value is None:
            return False

        s = str(value).strip()
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

    def curate_sample(self, sample_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a BioSamples JSON dictionary and returns a cleaned dictionary
        with extracted location, latitude, and longitude.
        """
        cleaned_dict = self.standardise_keys(sample_json)

        result = {
            "accession": sample_json.get("accession"),
            "location": None,
            "latitude": None,
            "longitude": None,
        }

        loc_key = self._first_present_key(cleaned_dict, LOCATION_KEYS["location"])
        if loc_key:
            is_location = self.sanity_check_location(cleaned_dict[loc_key])
            if is_location:
                result["location"] = cleaned_dict[loc_key]
            else:
                result["location"] = None

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

        for key, value in cleaned_dict.items():
            if (
                key not in LOCATION_KEYS["lat_lon"]
                and key not in LOCATION_KEYS["location"]
                and key not in LOCATION_KEYS["lat"]
                and key not in LOCATION_KEYS["lon"]
            ):
                result[key] = value
        return result


def curate_biosample(input_data: Any) -> Dict[str, Any]:
    """
    Helper function to curate a single biosample.
    Input can be a BioSamples JSON dict, a JSON string, or a path to a JSON file.
    """
    if isinstance(input_data, (str, os.PathLike)):
        sample_json = load_json(str(input_data))
    else:
        sample_json = input_data

    if not sample_json:
        return {}

    curator = SampleCurator()
    return curator.curate_sample(sample_json)


def main():
    args = parse_arguments()
    result = curate_biosample(args.sample_json)
    if result:
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
