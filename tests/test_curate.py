# test_parser.py
import pytest

from sample_metadata_curation.bin.curate import curate_biosample

FIXTURE_PATH = "tests/fixtures/test.json"


def test_curate_biosample_full():
    result = curate_biosample(FIXTURE_PATH)
    assert result["accession"] == "SAMN39868869"
    assert result["location"] == "Denmark"
    assert result["latitude"] == 55.62115
    assert result["longitude"] == 8.2849

    assert result["01_mfd_sampletype"] == "Soil"
    assert result["project_identifier"] == "P08_1"
    assert result["extraction_method"] == "PowerSoil-Pro-HT"


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
    "location_str",
    [
        "not provided",
        "NA",
        "AAAAAAAA",
        "a1b2c3d4",
        "a1b2c3d4",
    ],
)
def test_invalid_location_returns_none(location_str):
    sample = {"characteristics": {"geo_loc_name": [{"text": location_str}]}}
    result = curate_biosample(sample)
    assert result["location"] is None
