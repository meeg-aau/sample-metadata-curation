MISSING_VALUES = {
    "not provided",
    "not collected",
    "unavailable",
    "not applicable",
    "restricted access",
    "missing",
    "-",
    "n/a",
    "null",
    "na",
    "",
}

LOCATION_KEYS = {
    "lat_lon": ["lat_lon"],
    "lat": ["lat", "geographic_location_latitude", "latitude_start", "latitude_end"],
    "lon": ["lon", "geographic_location_longitude", "longitude_start", "longitude_end"],
    "location": [
        "geo_loc_name",
        "geographic_location_country_and_or_sea",
        "geographic_location_country_and_or_sea_region",
        "geographic_location_region_and_locality",
        "marine_region",
    ],
}


ENVIRONMENT_KEYS = [
    "env_material",
    "sample_type",
    "env_biome",
    "isolation_source",
    "analyte_type",
    "env_broad_scale",
    "env_local_scale",
    "env_medium",
    "environment_biome",
    "environment_feature",
    "gold_ecosystem_classification",
    "broad_scale_environmental_context",
    "local_environmental_context",
    "environmental_medium",
]


DATE_KEYS = [
    "collection_date",
    "event_date_time_start",
    "event_date_time_end",
]


OTHER_KEYS = [
    "host",
    "ph",
    "depth",
    "temp",
    "temperature",
    "rel_to_oxygen",
    "geographic_location_depth",
    "chlorophyll",
    "isol_growth_condt",
    "salinity",
    "turbidity",
    "dissolved_solids",
    "conductivity",
    "dissolved_oxygen",
]

CHECKLIST = [
    "ncbi_package",
    "ena_checklist",
    "ncbi_submission_package",
    "biosamplemodel",
]
