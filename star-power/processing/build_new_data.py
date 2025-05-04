"""
Project Name: Star Power
File: build_new_data.py

Experiment to use daily TMDB download, gather data from IMDB, and build Star Power without credits.csv.
Todo: This file is a work-in-progress for a 1.2m record run.

Author: Kyle Salgado-Gouker

"""

import os
import pandas as pd

from access.paths import DATA_DIRECTORY, FILM_INFORMATION_DIRECTORY, MOVIES_METADATA_FILE
from access.table_access import load_tmdb_movie_metadata
from utils.utilities import show_df_info, pretty_print_df


# === Constants ===
# weight sum = 6
ACTOR_WEIGHTS = [1.0, 0.8, 0.5, 0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1]
CREW_ROLE_WEIGHTS = {
    "Director": 0.9,
    "Producer": 0.4,
    "Executive Producer": 0.6,
    "Screenplay": 0.4
}
# just a sample of consumer price index.
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

content_modeling_cols = [
    'Sex - Report Count', 'Violence - Report Count', 'Profanity - Report Count',
    'Drugs - Report Count', 'Intense - Report Count'
]


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

if __name__ == '__main__':
    print("Current directory:", os.getcwd())

    CREDITS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "credits.csv")
    KEYWORDS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "keywords.csv")
    LINKS_SMALL_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "links_small.csv")
    LINKS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "links.csv")
    MOVIES_METADATA_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "movies_metadata.csv")
    TMDB_MOVIES_METADATA_FILE = os.path.join(DATA_DIRECTORY, "TMDB_movie_dataset_v11.csv")
    RATINGS_SMALL_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "ratings_small.csv")
    RATINGS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "ratings.csv")
    IMDB_MOVIE_METADATA_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_metadata.csv")
    IMDB_MOVIE_CONTENT_WARNING_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_content_warnings.csv")
    STAR_POWER_DATA_FILE = os.path.join(DATA_DIRECTORY, "star_power.csv")
    MERGED_STAR_POWER_INTERMEDIATE_FILE = os.path.join(DATA_DIRECTORY, "merged_star_power.csv")
    DATA_TO_MODEL_FILE = os.path.join(DATA_DIRECTORY, "data_to_model.csv")

    credits_df = pd.read_csv(CREDITS_FILE)
    keywords_df = pd.read_csv(KEYWORDS_FILE)
    links_small_df = pd.read_csv(LINKS_SMALL_FILE)
    links_df = pd.read_csv(LINKS_FILE)
    ratings_small_df = pd.read_csv(RATINGS_SMALL_FILE)
    ratings_df = pd.read_csv(RATINGS_FILE)

    # Old film metadata (from Kaggle project)
    movie_metadata_df = pd.read_csv(MOVIES_METADATA_FILE)
    print(show_df_info(movie_metadata_df, "TMDB Movie Metadata"))

    # TMDB metadata access.
    tmdb_movie_metadata_df = load_tmdb_movie_metadata(TMDB_MOVIES_METADATA_FILE)
    print(show_df_info(tmdb_movie_metadata_df, "TMDB Movie Metadata"))

    tmdb_movie_metadata_above_ten_votes_df = tmdb_movie_metadata_df[tmdb_movie_metadata_df['vote_count'] > 10]
    print("Number of records with more than 10 votes: ", len(tmdb_movie_metadata_above_ten_votes_df))
    print("Revenue > $1000000: ", len(tmdb_movie_metadata_df[tmdb_movie_metadata_df['revenue'] > 1000000]))
    print("Budget > $1000000: ", len(tmdb_movie_metadata_df[tmdb_movie_metadata_df['budget'] > 1000000]))

    tmdb_subset_metadata_df = tmdb_movie_metadata_df[
        (tmdb_movie_metadata_df['vote_count'] > 10) &
        (tmdb_movie_metadata_df['revenue'] > 1000000) &
        (tmdb_movie_metadata_df['budget'] > 1000000)
        ]

    print("Number of records with all criteria: ", len(tmdb_subset_metadata_df))

    data_to_model_df = pd.read_csv(DATA_TO_MODEL_FILE)

    missing_imdb_ids = tmdb_subset_metadata_df[
        ~tmdb_subset_metadata_df['imdb_id'].isin(data_to_model_df['imdb_id'])
    ]['imdb_id'].dropna().unique().tolist()

    print("This is the number of records to read from IMDB: ", len(missing_imdb_ids))

