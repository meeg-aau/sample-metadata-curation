import json
import re
import sys
from typing import Any, Dict, List, Optional

from .constants import LOCATION_KEYS, MISSING_VALUES
from .sample_parser import load_json, parse_arguments

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
        Convert a characteristic key into a consistent snake_case key.
        """
        s = str(key).strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)  # non-alphanumerics -> underscores
        s = re.sub(r"_+", "_", s)  # collapse multiple underscores
        s = s.strip("_")  # trim leading/trailing underscores
        return s

    def flatten_characteristics(
        self, sample_json: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        """
        Convert BioSamples 'characteristics' into a simple dict:
          normalized_key -> first item's 'text'
        """
        chars = sample_json.get("characteristics") or {}
        out: Dict[str, Optional[str]] = {}

        for key, items in chars.items():
            norm_key = self.normalize_key(key)
            if isinstance(items, list) and items:
                first = items[0]
                val = first.get("text") if isinstance(first, dict) else str(first)
                out[norm_key] = val
            else:
                out[norm_key] = None

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
        flat_attrs = self.flatten_characteristics(sample_json)

        result = {
            "accession": sample_json.get("accession"),
            "location": None,
            "latitude": None,
            "longitude": None,
        }

        loc_key = self._first_present_key(flat_attrs, LOCATION_KEYS["location"])
        if loc_key:
            is_location = self.sanity_check_location(flat_attrs[loc_key])
            if is_location:
                result["location"] = flat_attrs[loc_key]
            else:
                result["location"] = None

        lat = None
        lon = None

        # try combined lat_lon
        lat_lon_key = self._first_present_key(flat_attrs, LOCATION_KEYS["lat_lon"])
        if lat_lon_key:
            lat_lon_str = str(flat_attrs[lat_lon_key]).strip()
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
            lat_key = self._first_present_key(flat_attrs, LOCATION_KEYS["lat"])
            if lat_key:
                lat = self._parse_single_coord(flat_attrs[lat_key])

        if lon is None:
            lon_key = self._first_present_key(flat_attrs, LOCATION_KEYS["lon"])
            if lon_key:
                lon = self._parse_single_coord(flat_attrs[lon_key])

        # Validate ranges and try switching if invalid
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
        return result


def curate_biosample(sample_json: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to curate a single biosample."""
    curator = SampleCurator()
    return curator.curate_sample(sample_json)


def main():
    args = parse_arguments()
    sample_json = load_json(args.sample_json)
    if sample_json:
        result = curate_biosample(sample_json)
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
