import argparse
import json
import os
from pathlib import Path


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
        required=True,
        default=Path(__file__).parent.parent
        / "resources"
        / "country_to_cc_mapping.csv",
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
