"""
Project Name: Star Power
File: settings.py

Global settings for imdb, ryans ratings and other webscraped sites.


Author: Kyle Salgado-Gouker

"""
import pandas as pd

# for webscraping ratings and downloading sheets from google doc (costly in time)
DOWNLOAD_SHEETS = False

# for webscraping ratings and downloading sheets from google doc (costly in time)
BUILD_RATINGS_FROM_SHEETS = False

# download html ratings for scraping
DOWNLOAD_RATINGS_SCRAPE_FODDER = False

# for webscraping other data
BUILD_RATINGS_FROM_SCRAPING = False

# download html movie years
DOWNLOAD_MOVIE_YEARS = True

# download html movie audience
DOWNLOAD_MOVIE_AUDIENCE = True

SKIP_TO_MODELING = True

# download episode pages from imdb for scraping
GET_EPISODE_PAGES = False

# download content advisories from imdb
BUILD_CONTENT_FROM_SCRAPING = False

GET_SERIES_RUNS = False

CREATE_MISSING_SERIES_DATAFRAME = False


# === Constants ===
# weight sum = 6
ACTOR_WEIGHTS = [1.0, 0.8, 0.5, 0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1]
CREW_ROLE_WEIGHTS = {
    "Director": 0.9,
    "Producer": 0.4,
    "Executive Producer": 0.6,
    "Screenplay": 0.4
}

# consumer price index.
CPI_DATA = {
    1913: 9.9, 1920: 20.0, 1930: 16.7, 1940: 14.0, 1950: 24.1, 1960: 29.6,
    1970: 38.8, 1980: 82.4, 1990: 130.7, 2000: 172.2, 2010: 218.1,
    2020: 258.8, 2021: 270.9, 2022: 292.7, 2023: 303.3
}
CPI_INDEX = pd.Series(CPI_DATA).sort_index().interpolate(method='linear')
BASE_CPI = CPI_INDEX[2023]

# Modeling columns for general model
general_modeling_columns = ['log_budget_adj', 'sp_sum_previous_mean',
     'log_sum_prev_revenue_mean', 'log_mean_prev_revenue_mean', 'log_mean_prev_budget_mean',
     'rev_to_budget_ratio', 'rev_per_prev_sp', 'release_year']

general_modeling_columns_plus = general_modeling_columns.append("has_collection")

content_modeling_cols = [
    'Sex - Report Count', 'Violence - Report Count', 'Profanity - Report Count',
    'Drugs - Report Count', 'Intense - Report Count'
]

# --- Switches to control star power execution.
# some of these take a long time.
# Turn off to avoid rebuilding.
PREPARE_DATA = False
# Save time by avoiding huge search.
DO_GRID_SEARCH = False
# Do Star Power Rebuild
DO_STAR_POWER_REBUILD = False
# IMDB MetaData
USE_IMDB_METADATA = False
# debugging
DEBUG_IMDB_BRIDGE = False
# randomized grid
USE_RANDOMIZED_GRID = False

