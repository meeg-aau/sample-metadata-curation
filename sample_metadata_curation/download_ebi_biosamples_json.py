#!/usr/bin/env python3

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def read_accessions(input_file):
    """
    Read one BioSample accession per line.

    Empty lines and lines starting with # are ignored.
    """

    accessions = []

    with open(input_file, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            accessions.append(line)

    return accessions


def download_biosample_json(accession, timeout=60):
    """
    Download one BioSample record from the EBI BioSamples API.
    """

    url = f"https://www.ebi.ac.uk/biosamples/samples/{accession}.json"

    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def save_json(data, output_path):
    """
    Save JSON with indentation and UTF-8 encoding.
    """

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Download raw EBI BioSamples JSON records "
            "from a list of BioSample accessions."
        )
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Text file with one BioSample accession per line.",
    )

    parser.add_argument(
        "-o",
        "--outdir",
        default="raw_json",
        help="Output directory for downloaded JSON files. Default: raw_json",
    )

    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Delay between requests in seconds. Default: 0.2",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing JSON files.",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    input_file = Path(args.input)
    outdir = Path(args.outdir)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    outdir.mkdir(parents=True, exist_ok=True)

    accessions = read_accessions(input_file)

    if not accessions:
        print(f"No accessions found in {input_file}")
        return

    print(f"Found {len(accessions)} accessions.")
    print(f"Saving JSON files to: {outdir}")

    downloaded = 0
    skipped = 0
    failed = 0

    for accession in accessions:
        output_path = outdir / f"{accession}.json"

        if output_path.exists() and not args.overwrite:
            print(f"[SKIP] {accession}: file already exists")
            skipped += 1
            continue

        print(f"[GET]  {accession}")

        try:
            sample_json = download_biosample_json(accession)
            save_json(sample_json, output_path)
            downloaded += 1

        except urllib.error.HTTPError as error:
            print(f"[FAIL] {accession}: HTTP {error.code}")
            failed += 1

        except urllib.error.URLError as error:
            print(f"[FAIL] {accession}: {error}")
            failed += 1

        except json.JSONDecodeError:
            print(f"[FAIL] {accession}: response was not valid JSON")
            failed += 1

        time.sleep(args.sleep)

    print()
    print("Done.")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")


if __name__ == "__main__":
    main()