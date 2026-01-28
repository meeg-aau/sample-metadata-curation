# test_parser.py
import pytest

from sample_metadata_curation.bin.curate import curate_biosample

FIXTURE_PATH = "tests/fixtures/test.json"


def test_curate_biosample_full():
    result = curate_biosample(FIXTURE_PATH)
    assert result["accession"] == "SAMN39868869"
    assert result["region"] == "Denmark"
    assert result["latitude"] == 55.62115
    assert result["longitude"] == 8.2849

    assert result["01_mfd_sampletype"] == "Soil"
    assert result["project_identifier"] == "P08_1"
    assert result["extraction_method"] == "PowerSoil-Pro-HT"

    assert result["geo_check_status"] == "PASS"
    assert result["geo_check_reason"] == "match"


@pytest.mark.parametrize(
    "lat_lon_str, expected_lat, expected_lon",
    [
        ("55.62115 N 8.2849 E", 55.62115, 8.2849),
        ("34.0522N 118.2437W", 34.0522, -118.2437),
        ("12.345 S 45.678 E", -12.345, 45.678),
        ("55.62115 8.2849", 55.62115, 8.2849),
        ("-33.8688 151.2093", -33.8688, 151.2093),
    ],
)
def test_parse_lat_lon_combined(lat_lon_str, expected_lat, expected_lon):
    sample = {"characteristics": {"lat_lon": [{"text": lat_lon_str}]}}
    result = curate_biosample(sample)
    assert result["latitude"] == pytest.approx(expected_lat, abs=1e-6)
    assert result["longitude"] == pytest.approx(expected_lon, abs=1e-6)


def test_parse_separate_lat_lon():
    sample = {
        "characteristics": {
            "geographic_location_latitude": [{"text": "55.62115"}],
            "geographic_location_longitude": [{"text": "8.2849"}],
        }
    }
    result = curate_biosample(sample)
    assert result["latitude"] == 55.62115
    assert result["longitude"] == 8.2849


@pytest.mark.parametrize(
    # invalid options
    "lat_lon_str",
    [
        "NA",
        "not provided",
        "unknown",
        "55 N 200 E",
        "",
        None,
    ],
)
def test_parse_lat_lon_combined_invalid_returns_none(lat_lon_str):
    sample = {"characteristics": {"lat_lon": [{"text": lat_lon_str}]}}
    result = curate_biosample(sample)
    assert result["latitude"] is None
    assert result["longitude"] is None


def test_parse_lat_lon_switched():
    # Case where lat/lon are swapped: lat=91 (invalid as lat), lon=8 (valid as lat)
    # Swapped: lat=8, lon=91 -> both valid
    sample = {"characteristics": {"lat_lon": [{"text": "91 N 8 E"}]}}
    result = curate_biosample(sample)
    assert result["latitude"] == 8.0
    assert result["longitude"] == 91.0


@pytest.mark.parametrize(
    "region_str",
    [
        "not provided",
        "NA",
        "AAAAAAAA",
        "a1b2c3d4",
        "a1b2c3d4",
    ],
)
def test_invalid_region_returns_none(region_str):
    sample = {"characteristics": {"geo_loc_name": [{"text": region_str}]}}
    result = curate_biosample(sample)
    assert result["region"] is None


@pytest.mark.parametrize(
    "location_str, lat_lon_str, expected_region, expected_locality, "
    "expected_geo_match, expected_geo_match_reason",
    [
        (
            "Denmark",
            "55.62115 N 8.2849 E",
            "Denmark",
            None,
            "PASS",
            "match",
        ),  # Matching
        (
            "India",
            "55.62115 N 8.2849 E",
            None,
            None,
            "FAIL",
            "country_mismatch",
        ),  # Non-matching
        (
            "United States",
            "40.7128 N 74.0060 W",
            "United States",
            None,
            "PASS",
            "match",
        ),  # Matching
        (
            "Denmark",
            "40.7128 N 74.0060 W",
            None,
            None,
            "FAIL",
            "country_mismatch",
        ),  # Non-matching
        (
            "United Kingdom: England",
            "51.5074 N 0.1278 W",
            "United Kingdom",
            "England",
            "PASS",
            "match",
        ),  # Matching with locality
        (
            "United States Minor Outlying Islands:Baker Island",
            "0.1947, -176.4794",
            "United States Minor Outlying Islands",
            "Baker Island",
            "WARN",
            "reported_cc_not_supported_by_reverse_geocoder",
        ),
        (
            "Atlantic Ocean:Charlie Gibbs Fracture Zone",
            "52.45, -35.08",
            "Atlantic Ocean",
            "Charlie Gibbs Fracture Zone",
            "PASS",
            "ocean_or_sea",
        ),
    ],
)
def test_coordinate_region_match(
    location_str,
    lat_lon_str,
    expected_region,
    expected_locality,
    expected_geo_match,
    expected_geo_match_reason,
):
    sample = {
        "characteristics": {
            "geo_loc_name": [{"text": location_str}],
            "lat_lon": [{"text": lat_lon_str}],
        }
    }
    result = curate_biosample(sample)
    assert result["region"] == expected_region
    assert result["locality"] == expected_locality
    assert result["geo_check_status"] == expected_geo_match
    assert result["geo_check_reason"] == expected_geo_match_reason


def test_biome_extraction():
    biome_keys = [
        "01_mfd_sampletype",
        "02_mfd_areatype",
        "03_mfd_hab1",
        "04_mfd_hab2",
        "05_mfd_hab3",
    ]
    result = curate_biosample(FIXTURE_PATH, biome_keys=biome_keys)
    expected_biome = (
        "Soil;Natural;Bogs, mires and fens;Calcareous fens;Petrifying springs"
    )
    assert result.get("biome") == expected_biome
