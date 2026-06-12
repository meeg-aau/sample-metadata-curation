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

SMALL_ISLAND_CC = {
    "BV",  # Bouvet Island
    "KY",  # Cayman Islands
    "CK",  # Cook Islands
    "CX",  # Christmas Island
    "CC",  # Cocos (Keeling) Islands
    "FK",  # Falkland Islands
    "FO",  # Faroe Islands
    "GI",  # Gibraltar
    "GG",  # Guernsey
    "HM",  # Heard Island and McDonald Islands
    "IM",  # Isle of Man
    "JE",  # Jersey
    "MO",  # Macao
    "MV",  # Maldives
    "MH",  # Marshall Islands
    "NR",  # Nauru
    "NU",  # Niue
    "NF",  # Norfolk Island
    "MP",  # Northern Mariana Islands
    "PW",  # Palau
    "PN",  # Pitcairn
    "SH",  # Saint Helena
    "PM",  # Saint Pierre and Miquelon
    "SM",  # San Marino
    "ST",  # Sao Tome and Principe
    "SC",  # Seychelles
    "SG",  # Singapore
    "TK",  # Tokelau
    "TO",  # Tonga
    "TC",  # Turks and Caicos Islands
    "TV",  # Tuvalu
    "UM",  # US Minor Outlying Islands
    "VU",  # Vanuatu
    "WF",  # Wallis and Futuna
}

# Territories that Natural Earth maps to their parent country's ISO code
TERRITORY_TO_PARENT_CC = {
    # France
    "GF": "FR",  # French Guiana
    "GP": "FR",  # Guadeloupe
    "MQ": "FR",  # Martinique
    "RE": "FR",  # Reunion
    "YT": "FR",  # Mayotte
    "PM": "FR",  # Saint Pierre and Miquelon
    "BL": "FR",  # Saint Barthelemy
    "MF": "FR",  # Saint Martin (French part)
    "NC": "FR",  # New Caledonia
    "PF": "FR",  # French Polynesia
    "TF": "FR",  # French Southern and Antarctic Lands
    "WF": "FR",  # Wallis and Futuna
    # United Kingdom
    "AI": "GB",  # Anguilla
    "BM": "GB",  # Bermuda
    "IO": "GB",  # British Indian Ocean Territory
    "VG": "GB",  # British Virgin Islands
    "KY": "GB",  # Cayman Islands
    "FK": "GB",  # Falkland Islands
    "GI": "GB",  # Gibraltar
    "GG": "GB",  # Guernsey
    "IM": "GB",  # Isle of Man
    "JE": "GB",  # Jersey
    "MS": "GB",  # Montserrat
    "PN": "GB",  # Pitcairn Islands
    "SH": "GB",  # Saint Helena, Ascension and Tristan da Cunha
    "GS": "GB",  # South Georgia and South Sandwich Islands
    "TC": "GB",  # Turks and Caicos Islands
    # United States
    "AS": "US",  # American Samoa
    "GU": "US",  # Guam
    "MH": "US",  # Marshall Islands (Compact of Free Association)
    "FM": "US",  # Micronesia (Compact of Free Association)
    "MP": "US",  # Northern Mariana Islands
    "PW": "US",  # Palau (Compact of Free Association)
    "PR": "US",  # Puerto Rico
    "UM": "US",  # United States Minor Outlying Islands
    "VI": "US",  # United States Virgin Islands
    # Netherlands
    "AW": "NL",  # Aruba
    "BQ": "NL",  # Bonaire, Sint Eustatius and Saba
    "CW": "NL",  # Curacao
    "SX": "NL",  # Sint Maarten (Dutch part)
    # Denmark
    "FO": "DK",  # Faroe Islands
    "GL": "DK",  # Greenland
    # Norway
    "BV": "NO",  # Bouvet Island
    "SJ": "NO",  # Svalbard and Jan Mayen
    # Australia
    "CC": "AU",  # Cocos (Keeling) Islands
    "CX": "AU",  # Christmas Island
    "HM": "AU",  # Heard Island and McDonald Islands
    "NF": "AU",  # Norfolk Island
    # New Zealand
    "CK": "NZ",  # Cook Islands
    "NU": "NZ",  # Niue
    "TK": "NZ",  # Tokelau
    # Finland
    "AX": "FI",  # Aaland Islands
    # China
    "HK": "CN",  # Hong Kong
    "MO": "CN",  # Macao
    # Spain
    "EA": "ES",  # Ceuta and Melilla
    "IC": "ES",  # Canary Islands
    # Portugal
    "AC": "PT",  # Ascension Island (note: also SH/GB)
    # Morocco (disputed)
    "EH": "MA",  # Western Sahara
}
