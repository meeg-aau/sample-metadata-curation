import argparse
import json
import os


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--sample_json",
        required=True,
        help="BioSample API JSON output or path to JSON file",
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
