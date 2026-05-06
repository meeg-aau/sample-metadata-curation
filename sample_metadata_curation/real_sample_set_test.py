import random
import time

import pandas as pd
import requests

from sample_metadata_curation.curate import curate_biosample

random.seed(43)
organism_types = [
    '"soil metagenome"[Organism]',
    '"marine metagenome"[Organism]',
    '"freshwater metagenome"[Organism]',
    '"air metagenome"[Organism]',
    '"sediment metagenome"[Organism]',
    '"plant metagenome"[Organism]',
    '"wastewater metagenome"[Organism]',
]

accessions = []
for organism in organism_types:
    response = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={
            "db": "biosample",
            "term": f'"lat lon"[All Fields] AND {organism}',
            "retmax": 1000,  # fetch more so we can pick randomly
            "retmode": "json",
        },
    )
    ids = response.json()["esearchresult"]["idlist"]
    # Pick 10 random IDs from each organism type
    sampled_ids = random.sample(ids, min(10, len(ids)))

    summary_response = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={
            "db": "biosample",
            "id": ",".join(sampled_ids),
            "retmode": "json",
        },
    )
    summary_data = summary_response.json()
    for uid in sampled_ids:
        if uid in summary_data["result"]:
            accessions.append(summary_data["result"][uid]["accession"])
    time.sleep(0.4)

print(f"Found {len(accessions)} accessions: {accessions}")

# Step 2: Fetch and curate each one
results = []
for acc in accessions:
    response = requests.get(f"https://www.ebi.ac.uk/biosamples/samples/{acc}")
    if response.status_code == 200:
        data = response.json()
        result = curate_biosample(data)
        results.append(result)
        print(f"✓ {acc}")
    else:
        print(f"✗ {acc}: {response.status_code}")
    time.sleep(0.4)

# Step 3: Save to CSV
df = pd.DataFrame(results)
df.to_csv("curated_real_samples_test.csv", index=False)
print(f"\nSaved {len(df)} samples to curated_real_samples_test.csv")
print("\n=== Summary ===")
print(f"Total samples: {len(df)}")

print("\nGeo check status:")
status_counts = df["geo_check_status"].value_counts()
for status, count in status_counts.items():
    print(f"  {status}: {count} ({count/len(df)*100:.1f}%)")

print("\nGeo check reason:")
reason_counts = df["geo_check_reason"].value_counts()
for reason, count in reason_counts.items():
    print(f"  {reason}: {count} ({count/len(df)*100:.1f}%)")

reversed_count = df["coordinates_reversed"].sum()
print(f"\nCoordinates reversed: {reversed_count} ({reversed_count/len(df)*100:.1f}%)")
