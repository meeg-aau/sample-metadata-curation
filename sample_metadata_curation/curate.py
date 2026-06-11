import json
import os
import sys
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from sample_metadata_curation.biome import BiomeCurator
from sample_metadata_curation.location import LocationCurator
from sample_metadata_curation.sample_parser import (
    load_json,
    parse_arguments,
    standardise_keys,
)


class SampleCurator:
    def __init__(
        self,
        resources_dir: Optional[Path] = None,
        biome_keys: Optional[List[str]] = None,
    ):
        if resources_dir is None:
            resources_dir = Path(__file__).parent / "resources"

        self.location_curator = LocationCurator(resources_dir=resources_dir)
        self.biome_curator = BiomeCurator(biome_keys=biome_keys)

    def curate_sample(self, sample_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a BioSamples JSON dictionary and returns a cleaned dictionary
        with extracted region, locality, latitude, longitude and reasons
        for pass or failed sanity check
        """
        cleaned_dict = standardise_keys(sample_json)

        accession = sample_json.get("accession")
        result = self.location_curator.curate_location(
            cleaned_dict, accession=accession
        )

        for key, value in cleaned_dict.items():
            if key not in result and key != "accession":
                from .constants import LOCATION_KEYS

                if (
                    key not in LOCATION_KEYS["lat_lon"]
                    and key not in LOCATION_KEYS["location"]
                    and key not in LOCATION_KEYS["lat"]
                    and key not in LOCATION_KEYS["lon"]
                ):
                    result[key] = value

        # Biome extraction
        biome_result = self.biome_curator.curate_biome(cleaned_dict)
        result.update(biome_result)

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


def save_curated_json(result, output_path):
    """
    Save curated matadata as a JSON file.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)

def save_curated_tsv(result, output_path):
    """
    Save curated metadata as a TSV file.

    If a single sample dictionary os provided, it is converted to a one-row table. 
    If a list of dictionaries is provided, all observed keys are used as columns.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(result, dict):
        rows = [result]
    else:
        rows = result

    if not rows:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("")
            return

    fieldnames = sorted({key for row in rows for key in row.keys()})

    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_arguments()
    biome_keys = args.biome.split(",") if args.biome else None
    
    if args.sample_json:
        result = curate_biosample(args.sample_json, biome_keys=biome_keys)

        if not result:
            sys.exit(1)

        if args.output_json:
            save_curated_json(result, args.output_json)
            print(f"Curated metadata saved to: {args.output_json}")

        if args.output_tsv:
            save_curated_tsv(result, args.output_tsv)
            print(f"Curated metadata TSV saved to: {args.output_tsv}")

        if not args.output_json and not args.output_tsv:
            print(json.dumps(result, indent=2, ensure_ascii=False))
       
        return 

    if args.json_dir:
        json_dir = Path(args.json_dir)

        if not json_dir.exists():
            print(f"ERROR: JSON directory not found: {json_dir}", file=sys.stderr)

        json_files = sorted(json_dir.glob("*.json"))

        if not json_files:
            print(f"ERROR: no .json files found in {json_dir}", file=sys.stderr)
            sys.exists(1)

        results = []

        for json_file in json_files:
            result = curate_biosample(str(json_file), biome_keys=biome_keys)

            if result:
                results.append(result)

        if args.output_json:
            save_curated_json(results, args.output_json)
            print(f"Curated metadata saved to: {args.output_json}")
        if args.output_tsv:
            save_curated_tsv(results, args.output_tsv)
            print(f"Curated metadata TSV saved to: {args.output_tsv}")

        if not args.output_json and not args.output_tsv:
            print(json.dumps(results, indent=2, ensure_ascii=False))

        return

    print(
        "ERROR: provide either --sample-json or --json-dir",
        file=sys.stderr,
    )
    sys.exit(1)   
  


if __name__ == "__main__":
    main()
