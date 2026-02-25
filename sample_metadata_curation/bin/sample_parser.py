import argparse
import json
import os
import re
from pathlib import Path


def normalize_key(key: str) -> str:
    """
    simplify special characters in key names
    """
    s = str(key).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)  # non-alphanumerics -> underscores
    s = re.sub(r"_+", "_", s)  # collapse multiple underscores
    s = s.strip("_")  # trim leading/trailing underscores
    return s


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--sample_json",
        required=True,
        help="BioSample API JSON output or path to JSON file",
    )
    parser.add_argument(
        "-cc",
        "--country_codes",
        required=False,
        default=Path(__file__).parent.parent
        / "resources"
        / "country_to_cc_mapping.csv",
    )
    parser.add_argument(
        "-b",
        "--biome",
        required=False,
        help="Comma separated list of keys to extract as biome",
    )
    return parser.parse_args()


def load_json(input_data: str):
    if os.path.isfile(input_data):
        with open(input_data, "r") as f:
            return json.load(f)
    try:
        return json.loads(input_data)
    except json.JSONDecodeError:
        print("Error: Input is neither a valid file path nor a valid JSON string.")
        return None
