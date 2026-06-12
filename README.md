# BioSample Metadata Curation

A Python package for curating and cleaning BioSample metadata, specifically focusing on location and coordinate (latitude/longitude) normalization.

## Features

- **Location Cleaning**: Validates and normalizes geographic location names.
- **Coordinate Parsing**: Extracts latitude and longitude from various formats, including combined `lat_lon` strings.
- **Coordinate Validation**: Checks for valid latitude (-90 to 90) and longitude (-180 to 180) ranges.
- **Automatic Switching**: Intelligent swapping of latitude and longitude if they are provided in the wrong order but fall within valid ranges when swapped.
- **Flexible Input**: Supports BioSample JSON data as either a string or a local file path, or a directory containing multiple JSON files.
- **Batch Curation**: Processes multiple BioSample JSON files in a single command.
- **Structured Output**: Saves curated metadata as either TSV or JSON.
- **BiosSample Download Support**: Downloads BioSample JSON records from a list of BioSample accessions.
- **Download and Curate Workflow**: Allows downloading BioSample JSON records and immediately curating them in the same workflow.

## Source Data
The folder "resources" contains country codes from one of the sources used by INSDC https://www.cia.gov/the-world-factbook/references/country-data-codes/

## Installation

### For Users

To install the package in your environment:

```bash
pip install .
setup-sample-resources
```

### For Developers

To install with development tools (Black, isort, Flake8, pytest):

```bash
pip install -e ".[dev]"
setup-sample-resources
```

## Usage

### Command Line Interface

The package provides two main command-line tools:

1. **`curate-sample`**: Curates BioSample metadata from a JSON file or a directory.

<<<<<<< HEAD
2. **`setup-sample-resources`**: Fetches and prepares external resources required by the package.
   ```bash
   setup-sample-resources
   ```

Or using a JSON string:
=======
>>>>>>> 666e69b (README modified with the new features.)

```bash
curate-sample --sample_json path/to/sample.json
```
  
2. **`setup-sample-resources`**: Fetches and prepares external resources (this runs automatically during installation).


```bash
setup-sample-resources
```

Depending on the installed version, the package may also provide options to download BioSample JSON records from alist of BioSample accessions and curate them directly after download.

### Curating Multiple BioSample JSON Files

To curate all JSON files inside a directory:

```bash
curate-sample --json-dir path/to/json_directory/
```

A typical input directory may look like:

```bash
json_directory/
├── SAMN39868869.json
├── SAMN39868870.json
├── SAMN39868871.json
└── ...
```

### Saving Curated Output

Curated metadata can be saved as either TSV or JSON.

#### Saving Output as TSV

```bash
curate-sample \ 
--sample-json path/to/sample.json \ 
--output-tsv curated_metadata.tsv
```

or a directory of JSON files:

```bash
curate-sample \ 
--sample-json path/to/json_directory/ \ 
--output-tsv curated_metadata.tsv 
```

#### Save Output as JSON

```bash
curate-sample \
  --sample-json path/to/sample.json \
  --output-json curated_metadata.json \
```

For a directory of JSON files:

```bash
curate-sample \
  --sample-json path/to/json_directory/ \
  --output-json curated_metadata.json \
```

The TSV output is useful for manual inspection, spreadsheets, and downstream database integration. The JSON output preserves a structured format that can be used in automated pipelines.

### Downloading and Curating BioSamples in One Workflow

Biosample JSON records can be downloaded from a list of accessions and curated immediately after download. 

The input list should contain one BioSample accession per line:

```bash
SAMN39868869
SAMN39868870
SAMN39868871
```

Example file:

```bash
biosample_accessions.txt
```

Example of complete workflow command:

Download and Save Curated Output as TSV

```bash
curate-sample \
  --biosample-list biosample_accessions.txt \
  --download-json-outdir path/to/downloaded_biosample_jsons/ \
  --output-json curated_metadata.json \
  --output-tsv curated_metada.tsv
```

This will create a directory containing the downloaded JSON records:

```bash
downloaded_biosample_jsons/ 
├── SAMN39868869.json 
├── SAMN39868870.json 
├── SAMN39868871.json 
└── ...
```

This command will:

1. Read BioSample accession from `biosample_accessions.txt`
2. Download the corresponding BioSample JSON records
3. Save the original JSON files in `downloaded_biosample_jsons/`
4. Curate metadata
5. Save the curated metadata as `curated_metadata.json` and `curated_metadata.tsv`.

### As a Library

You can also use the curation logic in your own Python scripts. The `curate_biosample` function is flexible and accepts a dictionary, a JSON string, or a path to a JSON file:

```python
from sample_metadata_curation import curate_biosample

# Option 1: Use a dictionary
sample_data = {
    "accession": "SAMN39868869",
    "characteristics": {
        "geo_loc_name": [{"text": "Denmark"}],
        "lat_lon": [{"text": "55.62115 N 8.2849 E"}]
    }
}
result = curate_biosample(sample_data)

# Option 2: Use a JSON string
json_string = '{"accession": "SAMN39868869", ...}'
result = curate_biosample(json_string)

# Option 3: Use a path to a JSON file
result = curate_biosample("path/to/sample.json")

print(result)
# Output: {'accession': 'SAMN39868869', 'location': 'Denmark', 'latitude': 55.62115, 'longitude': 8.2849, 'coord_precision_deg': 0.0001}
```


coord_precision_deg is an estimate of the coordinate precision in degrees, where approximately: 1.0 ≈ 111km, 0.1 ≈ 11km, 0.01 ≈ 1km, 0.001 ≈ 111m, 0.0001 ≈ 11m.


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
