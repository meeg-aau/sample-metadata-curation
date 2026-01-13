# BioSample Metadata Curation

A Python package for curating and cleaning BioSample metadata, specifically focusing on location and coordinate (latitude/longitude) normalization.

## Features

- **Location Cleaning**: Validates and normalizes geographic location names.
- **Coordinate Parsing**: Extracts latitude and longitude from various formats, including combined `lat_lon` strings.
- **Coordinate Validation**: Checks for valid latitude (-90 to 90) and longitude (-180 to 180) ranges.
- **Automatic Switching**: Intelligent swapping of latitude and longitude if they are provided in the wrong order but fall within valid ranges when swapped.
- **Flexible Input**: Supports BioSample JSON data as either a string or a local file path.

## Installation

### For Users

To install the package in your environment:

```bash
pip install .
```

### For Developers

To install with development tools (Black, isort, Flake8, pytest):

```bash
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

The package provides a `curate-sample` command after installation:

```bash
curate-sample --sample_json path/to/sample.json
```

Or using a JSON string:

```bash
curate-sample --sample_json '{"accession": "SAMN...", "characteristics": {...}}'
```

### As a Library

You can also use the curation logic in your own Python scripts:

```python
from sample_metadata_curation.bin.curate import curate_biosample

sample_data = {
    "accession": "SAMN39868869",
    "characteristics": {
        "geo_loc_name": [{"text": "Denmark"}],
        "lat_lon": [{"text": "55.62115 N 8.2849 E"}]
    }
}

result = curate_biosample(sample_data)
print(result)
# Output: {'accession': 'SAMN39868869', 'location': 'Denmark', 'latitude': 55.62115, 'longitude': 8.2849}
```

## Development

### Linting and Formatting

We use `black`, `isort`, and `flake8` to maintain code quality.

```bash
black .
isort .
flake8 .
```

### Testing

Run the test suite using `pytest`:

```bash
pytest
```

### Pre-commit Hooks

To ensure all code meets quality standards before committing, install the pre-commit hooks:

```bash
pre-commit install
```

## CI/CD

This project uses GitHub Actions for continuous integration. Every push and pull request to the `main` branch triggers:
- Linting checks (Black, isort, Flake8)
- Automated testing (pytest)
