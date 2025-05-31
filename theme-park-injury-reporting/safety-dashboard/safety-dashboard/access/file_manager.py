"""
Project Name: Star Power
File: file_manager.py
Purpose: Handle loading, verifying, and optionally downloading core dataframes used in the Star Power project.

Author: Kyle Salgado-Gouker

"""

import re
import pandas as pd
from utils.utilities import show_df_info, pretty_print_df
from utils.web_utils import download_file


def get_initial_dataframes():
    """
    Downloads core ratings and TV metadata files if SKIP_TO_MODELING is False,
    then loads and returns them as pandas DataFrames.

    Returns:
        Tuple of four DataFrames:
            - nielsen_ratings_df
            - svod_ratings_df
            - archive_ratings_df
            - tmdb_tv_df
    """
    if not SKIP_TO_MODELING:
        download_file(NIELSEN_RATINGS_URL, NIELSEN_RATINGS_FILE)
        download_file(SVOD_MEASURE_URL, SVOD_MEASURE_FILE)
        download_file(ARCHIVE_RATINGS_URL, ARCHIVE_RATINGS_FILE)
        download_file(ORIGINAL_TMDB_DATASET_URL, TMDB_SERIES_MAIN_FILE_V3)

        nielsen_ratings_df = pd.read_csv(NIELSEN_RATINGS_FILE)
        svod_ratings_df = pd.read_csv(SVOD_MEASURE_FILE)
        archive_ratings_df = pd.read_csv(ARCHIVE_RATINGS_FILE)
        tmdb_tv_df = pd.read_csv(TMDB_SERIES_MAIN_FILE_V3)

        show_df_info(nielsen_ratings_df, "Nielsen Viewers")
        show_df_info(svod_ratings_df, "Video on Demand")
        show_df_info(archive_ratings_df, "Archive Program Ratings")
        show_df_info(tmdb_tv_df, "TMDB")

        pretty_print_df(nielsen_ratings_df, rows=10)
        pretty_print_df(svod_ratings_df, rows=10)
        pretty_print_df(archive_ratings_df, rows=10)
        pretty_print_df(tmdb_tv_df.iloc[:, :4], rows=10)

    return nielsen_ratings_df, svod_ratings_df, archive_ratings_df, tmdb_tv_df


def print_matching_records(name, nielsen_ratings_df, svod_ratings_df, program_ratings_df):
    """
    Searches for matching show names in each of the three dataframes and prints them.

    Args:
        name (str): Substring to match against show titles.
        nielsen_ratings_df (DataFrame): Nielsen Viewers dataset.
        svod_ratings_df (DataFrame): SVOD (Streaming Video On Demand) dataset.
        program_ratings_df (DataFrame): Archived ratings dataset.
    """
    if 'Show Name' in nielsen_ratings_df.columns:
        nielsen_matches = nielsen_ratings_df[nielsen_ratings_df['Show Name'].str.contains(name, case=False, na=False)]
        print("\nMatching records in Nielsen Viewers:")
        print(nielsen_matches)

    if 'Show' in svod_ratings_df.columns:
        vod_matches = svod_ratings_df[svod_ratings_df['Show'].str.contains(name, case=False, na=False)]
        print("\nMatching records in Video on Demand:")
        print(vod_matches)

    if 'Show' in program_ratings_df.columns:
        archive_matches = program_ratings_df[program_ratings_df['Show'].str.contains(name, case=False, na=False)]
        print("\nMatching records in Archive Program Ratings:")
        print(archive_matches)


def test_initial_dataframes():
    """
    Test utility to verify that dataframes are loaded and records can be looked up by name.
    """
    nielsen_ratings_df, svod_ratings_df, program_ratings_df, tmdb_df = get_initial_dataframes()
    given_name = "Girl Code"
    print_matching_records(given_name, nielsen_ratings_df, svod_ratings_df, program_ratings_df)


def sanitize_filename(filename):
    """
    Removes or replaces invalid characters in a filename string for compatibility with most filesystems.

    Args:
        filename (str): Raw filename string.

    Returns:
        str: Sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


if __name__ == "__main__":
    get_initial_dataframes()
