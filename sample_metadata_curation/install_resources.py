import csv
import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Set, Tuple
from xml.etree import ElementTree

import pandas as pd
import pyreadr
import requests

from sample_metadata_curation.constants import (
    MISSING_COUNTRY_MAPPING,
    MISSING_VALUES,
    NON_COUNTRIES,
    REVERSE_GEOCODER_MISSING_CC,
)

logging.basicConfig(level=logging.INFO)
logging = logging.getLogger()


ENA_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/ERC000011?download=true"
RG_URL = (
    "https://raw.githubusercontent.com/thampiman/reverse-geocoder/master"
    "/reverse_geocoder/rg_cities1000.csv"
)
COORDINATE_CLEANER_URL = (
    "https://github.com/ropensci/CoordinateCleaner/raw/"
    "9195fb64154dd20a921a412b5e4d24cc18d3803c/data/countryref.rda"
)
ROR_URL = (
    "https://zenodo.org/records/19576723/files/v2.6-2026-04-14-ror-data.zip?download=1"
)


def get_checklist_countries():
    """
    INSDC list of accepted names
    """
    try:
        logging.info("Downloading ENA country list...")
        response_ena = requests.get(ENA_URL)
        logging.info("Downloading RG country list...")
        response_rg = requests.get(RG_URL)
        logging.info("Downloading CoordinateCleaner country reference...")
        response_cc = requests.get(COORDINATE_CLEANER_URL)
        logging.info("Downloading ROR institution data...")
        response_ror = requests.get(ROR_URL)
        return (
            response_ena.text,
            response_rg.text,
            response_cc.content,
            response_ror.content,
        )
    except Exception as e:
        logging.error(f"Error downloading country lists: {e}")


def parse_ena_xml(ena_xml: str) -> List[str]:
    """
    Parse the ENA checklist XML to extract countries and seas.
    """
    try:
        root = ElementTree.fromstring(ena_xml)
        countries = []

        # Find the field 'geographic_location_country_andor_sea'
        for field in root.findall(".//FIELD"):
            name_elem = field.find("NAME")
            if (
                name_elem is not None
                and name_elem.text == "geographic_location_country_andor_sea"
            ):
                # Extract all VALUE tags from TEXT_CHOICE_FIELD
                for value_elem in field.findall(".//TEXT_VALUE/VALUE"):
                    if value_elem.text:
                        val = value_elem.text.strip()
                        if val.lower() not in MISSING_VALUES:
                            countries.append(val)
                break

        return sorted(list(set(countries)))
    except Exception as e:
        logging.error(f"Error parsing ENA XML: {e}")
        return []


def parse_rg_country_codes(rg: str) -> Set[str]:
    """
    Parse countries included in reverse_geocoder
    """
    rg_cc_unique = set()
    for line in rg.splitlines()[1:]:
        cc = line.split(",")[-1]
        rg_cc_unique.add(cc)
    return rg_cc_unique


def parse_iso_country_codes(iso_cc: Path) -> Dict[str, Tuple[str, str]]:
    """
    Parse ISO countries and 2 letter codes
    """
    df = pd.read_csv(iso_cc)
    df.columns = [c.strip() for c in df.columns]

    subset = df[["Name", "ISO 3166", "Comment"]]

    mapping = {
        row["Name"]: (row["ISO 3166"], row["Comment"]) for _, row in subset.iterrows()
    }

    return mapping


def parse_coordinate_cleaner_ref(rda_bytes: bytes) -> pd.DataFrame:
    """
    Parse CoordinateCleaner countryref.rda and return a DataFrame
    with centroid and capital coordinates per country.
    """
    result = pyreadr.read_r(io.BytesIO(rda_bytes))
    df = result[list(result.keys())[0]]

    # Select and rename relevant columns
    df = df[["iso3", "centroid.lon", "centroid.lat", "capital.lon", "capital.lat"]]

    return df


def parse_ror_institutions(ror_bytes: bytes) -> pd.DataFrame:
    """
    Parse ROR data dump and return a DataFrame with institution
    name, country code, and coordinates.
    """
    # ROR data dump is a zip file containing a CSV
    with zipfile.ZipFile(io.BytesIO(ror_bytes)) as z:
        # Find the CSV file inside the zip
        csv_files = [f for f in z.namelist() if f.endswith(".csv")]
        logging.info(f"Files in ROR zip: {z.namelist()}")
        with z.open(csv_files[0]) as f:
            df = pd.read_csv(f)

    df = df[
        [
            "names.types.ror_display",
            "locations.geonames_details.country_code",
            "locations.geonames_details.lat",
            "locations.geonames_details.lng",
        ]
    ].rename(
        columns={
            "names.types.ror_display": "institution_name",
            "locations.geonames_details.country_code": "country_code",
            "locations.geonames_details.lat": "latitude",
            "locations.geonames_details.lng": "longitude",
        }
    )
    df = df.dropna(subset=["latitude", "longitude"])
    return df


def create_final_cc_mapping(
    ena_countries: List[str],
    rg_cc: Set[str],
    iso_cc: Dict[str, Tuple[str, str]],
) -> tuple[Dict[str, list], List[str]]:

    final_mapping = {}
    oceans_and_seas = []

    for country in ena_countries:
        if "Ocean" in country or "Sea" in country:
            oceans_and_seas.append(country)
            continue

        # Explicit exclusions: not countries
        if country in NON_COUNTRIES:
            oceans_and_seas.append(country)
            continue

        # original - South Korea, country = Korea, South (as per ISO)
        original_country = country
        if country not in iso_cc:
            iso_country = MISSING_COUNTRY_MAPPING.get(country, None)
            if iso_country:
                country = iso_country
            else:
                logging.warning(
                    f"Warning: country {country} not found in ISO country codes mapping"
                )
                continue

        iso_code, comment = iso_cc[country]

        # Normal case: ISO code exists
        if iso_code != "-" and isinstance(iso_code, str) and iso_code.strip():
            cc = iso_code.split("|")[0].strip()
            if cc in rg_cc or cc in REVERSE_GEOCODER_MISSING_CC:
                final_mapping[original_country] = [country, cc]
            else:
                logging.warning(
                    f"Warning: ISO code {cc} for {country} "
                    "not found in reverse_geocoder"
                )
            continue

        # Sometimes mapped to another country code with string:
        # "ISO includes with ...{country}"
        reference_country_string = comment

        # Skip cases with no comment NaN
        if (
            not isinstance(reference_country_string, str)
            or not reference_country_string.strip()
        ):
            logging.warning(
                f"Warning: no reference comment for country {country} "
                "(ISO code is '-')"
            )
            continue

        reference_country = (
            reference_country_string.replace("ISO includes with ", "")
            .replace("the ", "")
            .strip()
        )

        if reference_country not in iso_cc:
            try:
                reference_country = MISSING_COUNTRY_MAPPING[reference_country]
            except KeyError:
                logging.warning(
                    f"Warning: reference country {reference_country} "
                    f"not found in ISO mapping (from {country})"
                )
                continue

        ref_iso_code, _ref_comment = iso_cc[reference_country]
        if (
            not isinstance(ref_iso_code, str)
            or not ref_iso_code.strip()
            or ref_iso_code == "-"
        ):
            logging.warning(
                f"Warning: reference country {reference_country} "
                f"has no usable ISO code (from {country})"
            )
            continue

        cc = ref_iso_code.split("|")[0].strip()
        if cc in rg_cc or cc in REVERSE_GEOCODER_MISSING_CC:
            final_mapping[original_country] = [reference_country, cc]
        else:
            logging.warning(
                f"Warning: reference ISO code {cc} for {reference_country} "
                f"not found in reverse_geocoder (from {country})"
            )

    return final_mapping, oceans_and_seas


def main():

    logging.info("Running geographical mapping setup...")

    resource_dir = Path(__file__).parent / "resources"

    if not resource_dir.exists():
        logging.error(f"Resource directory {resource_dir} does not exist. Exiting...")
        return

    country_codes = resource_dir / "country-codes.csv"
    if not country_codes.exists():
        logging.error(f"country-codes.csv not found in {resource_dir}. Exiting...")
        return

    ena_xml, rg_csv, cc_rda, ror_bytes = get_checklist_countries()

    ena_countries = parse_ena_xml(ena_xml)
    logging.info(f"{len(ena_countries)} countries found in ENA checklist")
    rg_cc = parse_rg_country_codes(rg_csv)
    iso_cc = parse_iso_country_codes(country_codes)

    final_mapping_path = resource_dir / "country_to_cc_mapping.csv"
    oceans_and_seas_path = resource_dir / "oceans_and_seas.txt"
    centroids_and_capitals_path = resource_dir / "country_centroids_and_capitals.csv"

    final_mapping, oceans_and_seas = create_final_cc_mapping(
        ena_countries, rg_cc, iso_cc
    )

    # Ensure all missing country mappings are included
    for original, mapped in MISSING_COUNTRY_MAPPING.items():
        if original not in final_mapping and mapped in final_mapping:
            final_mapping[original] = final_mapping[mapped]

    with open(final_mapping_path, "w") as f:
        writer = csv.writer(f)
        for key, value in final_mapping.items():
            writer.writerow([key, value[0], value[1]])
    with open(oceans_and_seas_path, "w") as f:
        f.writelines("\n".join(oceans_and_seas))

    centroids_df = parse_coordinate_cleaner_ref(cc_rda)
    centroids_df.to_csv(centroids_and_capitals_path, index=False)
    logging.info(
        f"{len(centroids_df)} centroid/capital records saved to "
        f"{centroids_and_capitals_path}"
    )

    institutions_path = resource_dir / "research_institutions.csv"
    institutions_df = parse_ror_institutions(ror_bytes)
    institutions_df.to_csv(institutions_path, index=False)
    logging.info(
        f"{len(institutions_df)} institution records saved to {institutions_path}"
    )

    logging.info("Mapping complete")


if __name__ == "__main__":
    main()
