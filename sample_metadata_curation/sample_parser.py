import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


def normalise_key(key: str) -> str:
    """
    simplify special characters in key names
    """
    s = str(key).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)  # non-alphanumerics -> underscores
    s = re.sub(r"_+", "_", s)  # collapse multiple underscores
    s = s.strip("_")  # trim leading/trailing underscores
    return s


def standardise_keys(sample_json: Dict[str, Any]) -> Dict[str, Optional[str]]:
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
        norm_key = normalise_key(key)
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
                norm_key = normalise_key(key)
                if isinstance(val_obj, dict):
                    val = val_obj.get("value")
                    if val is not None:
                        out[norm_key] = str(val)
                elif val_obj is not None:
                    out[norm_key] = str(val_obj)
    return out


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-j",
        "--sample-json",
        required=False,
        help="BioSample API JSON output or path to JSON file",
    )

    parser.add_argument(
        "--json-dir",
        required=False,
        help="Directory containing raw BioSamples JSON files to curate in batch.",
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

    parser.add_argument(
        "--output-json",
        required=False,
        help="Optional path to save the curated metadata as a JSON file"
    )

    parser.add_argument(
        "--output-tsv",
        required=False,
        help="Optional path to save the curated metada as a TSV file."
    )

    parser.add_argument(
        "--biosample-list",
        required=False,
        help="Text file with one BioSample accession per line to download and curate.",
    )

    parser.add_argument(
        "--download-json-outdir",
        required=False,
        help=(
            "Directory where downloaded raw EBI BioSamples JSON files wil be saved."
            "Required when using --biosample-list"
        )
    ),

    parser.add_argument(
        "--overwrite-downloads",
        action="store_true",
        help="Overwrite existing downloaded raw BioSamples JSON files."
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
