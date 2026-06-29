import csv
import io
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree

import pandas as pd
import pyreadr
import requests

from sample_metadata_curation.constants import (
    MISSING_COUNTRY_MAPPING,
    MISSING_VALUES,
    NON_COUNTRIES,
)

logging.basicConfig(level=logging.INFO)
logging = logging.getLogger()


ENA_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/ERC000011?download=true"
COORDINATE_CLEANER_URL = (
    "https://raw.githubusercontent.com/ropensci/CoordinateCleaner/"
    "master/data/countryref.rda"
)
ROR_ZENODO_CONCEPT_ID = "6347574"


def get_ror_download_url() -> str:
    r = requests.get(
        f"https://zenodo.org/api/records?q=conceptrecid:"
        f"{ROR_ZENODO_CONCEPT_ID}&sort=mostrecent&size=1"
    )
    r.raise_for_status()
    files = r.json()["hits"]["hits"][0]["files"]
    return next(f["links"]["self"] for f in files if f["key"].endswith(".zip"))


NATURAL_EARTH_URL = (
    "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip"
)


def get_checklist_countries():
    try:
        logging.info("Downloading ENA country list...")
        response_ena = requests.get(ENA_URL)
        logging.info("Downloading CoordinateCleaner country reference...")
        response_cc = requests.get(COORDINATE_CLEANER_URL)
        logging.info("Fetching latest ROR download URL...")
        ror_url = get_ror_download_url()
        logging.info(f"Downloading ROR institution data from {ror_url}...")
        response_ror = requests.get(ror_url)
        logging.info("Downloading Natural Earth country boundaries...")
        response_ne = requests.get(NATURAL_EARTH_URL)
        return (
            response_ena.text,
            response_cc.content,
            response_ror.content,
            response_ne.content,
        )
    except Exception as e:
        logging.error(f"Error downloading country lists: {e}")
        raise


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
    df = result["countryref"]

    df = df[["iso2", "centroid.lon", "centroid.lat", "capital.lon", "capital.lat"]]

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
        if not csv_files:
            raise ValueError(
                f"No CSV file found in ROR zip. Files present: {z.namelist()}"
            )
        if len(csv_files) > 1:
            raise ValueError(f"Multiple CSV files found in ROR zip: {csv_files}")
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


def save_natural_earth(ne_bytes: bytes, output_path: Path) -> None:
    """
    Save Natural Earth zip directly to resources — geopandas reads it natively.
    """
    with open(output_path, "wb") as f:
        f.write(ne_bytes)
    logging.info(f"Natural Earth boundaries saved to {output_path}")


def create_final_cc_mapping(
    ena_countries: List[str],
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
            final_mapping[original_country] = [country, cc]
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

    ena_xml, cc_rda, ror_bytes, ne_bytes = get_checklist_countries()

    ena_countries = parse_ena_xml(ena_xml)
    logging.info(f"{len(ena_countries)} countries found in ENA checklist")
    iso_cc = parse_iso_country_codes(country_codes)

    final_mapping_path = resource_dir / "country_to_cc_mapping.csv"
    oceans_and_seas_path = resource_dir / "oceans_and_seas.txt"
    centroids_and_capitals_path = resource_dir / "country_centroids_and_capitals.csv"

    final_mapping, oceans_and_seas = create_final_cc_mapping(ena_countries, iso_cc)

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
    natural_earth_path = resource_dir / "ne_countries.zip"
    save_natural_earth(ne_bytes, natural_earth_path)
    logging.info("Mapping complete")


if __name__ == "__main__":
    main()
