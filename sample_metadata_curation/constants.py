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
    "missing: control sample",
    "missing: data agreement established pre-2023",
    "missing: endangered species",
    "missing: human-identifiable",
    "missing: lab stock",
    "missing: sample group",
    "missing: synthetic construct",
    "missing: third party data",
}

LOCATION_KEYS = {
    "lat_lon": ["lat_lon"],
    "lat": ["lat", "geographic_location_latitude", "latitude_start", "latitude_end"],
    "lon": ["lon", "geographic_location_longitude", "longitude_start", "longitude_end"],
    "location": [
        "geo_loc_name",
        "geographic_location_country_and_or_sea",
        "geographic_location_country_and_or_sea_region",
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

MISSING_COUNTRY_MAPPING = {
    "Bahamas": "Bahamas, The",
    "Gambia": "Gambia, The",
    "Cape Verde": "Cabo Verde",
    "Czech Republic": "Czechia",
    "Democratic Republic of the Congo": "Congo, Democratic Republic of the",
    "Republic of the Congo": "Congo, Republic of the",
    "North Korea": "Korea, North",
    "South Korea": "Korea, South",
    "Turkey": "Turkey (Turkiye)",
    "Viet Nam": "Vietnam",
    "USA": "United States",
    "Myanmar": "Burma",
    "Saint Helena": "Saint Helena, Ascension, and Tristan da Cunha",
    "Cocos Islands": "Cocos (Keeling) Islands",
    "US Minor Outlying Islands": "United States Minor Outlying Islands",
    # INSDC contains State of Palestine but is not in ISO codes
    "State of Palestine": "West Bank",
    # Map French scattered islands to France
    "Bassas da India": "France",
    "Europa Island": "France",
    "Glorioso Islands": "France",
    "Juan de Nova Island": "France",
    "Tromelin Island": "France",
}

# Islands in INSDC list which are not ISO countries
NON_COUNTRIES = {
    "Borneo",
    "Line Islands",
    "Kerguelen Archipelago",
    "Paracel Islands",
    "Spratly Islands",
}

# Places that are "countries" in INSDC but not reverse_geocoder
REVERSE_GEOCODER_MISSING_CC = {
    "UM",  # United States Minor Outlying Islands
    "BV",  # Bouvet Island
    "HM",  # Heard Island and McDonald Islands
}
