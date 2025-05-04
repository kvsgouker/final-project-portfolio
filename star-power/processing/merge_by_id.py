"""
Project Name: Star Power
File: merge_by_id.py

Merge TMDB with IMDB series data.

Author: Kyle Salgado-Gouker
"""

import re
from fuzzywuzzy import process, fuzz
from utils.film_log import FilmLog
from utils.utilities import pretty_print_df, show_df_info


def find_best_match(title, main_df):
    # Normalize the incoming title
    norm_title = title.strip().lower()

    # Exact match first
    main_df['normalized_title'] = main_df['Title'].str.lower().str.strip()
    if norm_title in main_df['normalized_title'].values:
        return main_df.loc[main_df['normalized_title'] == norm_title, 'IMDb Series ID'].iloc[0]

    # Avoid substring matches if there are fewer than two words
    if len(norm_title.split()) >= 2:
        # Substring matches: Use literal string comparison instead of regex
        try:
            matches = main_df[main_df['normalized_title'].str.contains(re.escape(norm_title), na=False, regex=True)]
            if not matches.empty:
                return matches['IMDb Series ID'].iloc[0]

            # Reverse substring match: checking if any title in main_df is a substring of the transaction title
            reverse_matches = main_df[main_df['normalized_title'].apply(lambda x: norm_title in x)]
            if not reverse_matches.empty:
                return reverse_matches['IMDb Series ID'].iloc[0]
        except re.error:
            print(f"Regex error with title: {title}")

    # Fuzzy matching as a fallback
    best_match = process.extractOne(norm_title, main_df['normalized_title'].tolist(), scorer=fuzz.ratio)
    if best_match and best_match[1] > 80:  # setting a threshold of 80%
        matched_title = best_match[0]
        return main_df.loc[main_df['normalized_title'] == matched_title, 'IMDb Series ID'].iloc[0]

    return None


def apply_imdb_id_to_df(transaction_df, main_df):
    # Mapping for title to IMDb ID
    title_to_imdb_id = {title: find_best_match(title, main_df) for title in transaction_df['Title'].unique()}

    # Apply the IMDb ID to each row based on the title
    transaction_df['IMDb Series ID'] = transaction_df['Title'].map(title_to_imdb_id)


def debug_pre_merge(valid_id_df, nielsen_ratings_df, svod_ratings_df, program_ratings_df):
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(valid_id_df, "Validated TV Series DataFrame Filtered from TMDB"))
    headers = ['ID', 'Title', 'Seasons', 'Episodes', 'Votes', 'Average', 'First Aired', 'Last Aired', 'Status',
               'IMDb Series ID', 'Type']
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, pretty_print_df(valid_id_df, rows=10,
                    interesting_columns=['id', 'Title', 'number_of_seasons', 'number_of_episodes', 'vote_count',
                                         'vote_average', 'first_air_date', 'last_air_date', 'status', 'IMDb Series ID',
                                         'type'],
                    headers=headers))

    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(nielsen_ratings_df, "Nielsen Viewers"))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(svod_ratings_df, "Video on Demand"))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(program_ratings_df, "Archive Program Ratings"))


def merge_by_id(valid_id_df, nielsen_ratings_df, svod_ratings_df, program_ratings_df):
    # debug before to see the data changing.
    debug_pre_merge(valid_id_df, nielsen_ratings_df, svod_ratings_df, program_ratings_df)

    # Drop rows where 'Title' is NaN in the program_ratings_df
    program_ratings_df.dropna(subset=['Title'], inplace=True)

    # Debug: Checking for NaN values again
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, program_ratings_df['Title'].isna().sum())  # This should print 0, indicating no NaN values

    # Apply the imdb id to a copy of the data frames.
    valid_id_copy_df = valid_id_df.copy()
    nielsen_ratings_copy_df = nielsen_ratings_df.copy()
    svod_ratings_copy_df = svod_ratings_df.copy()
    program_ratings_copy_df = program_ratings_df.copy()

    # Eliminate leading and trailing whitespace. Convert to lower-case.
    valid_id_copy_df['normalized_title'] = valid_id_copy_df['Title'].str.lower().str.strip()

    # Apply imdb id to each transaction dataframe
    for df in [nielsen_ratings_copy_df, svod_ratings_copy_df, program_ratings_copy_df]:
        apply_imdb_id_to_df(df, valid_id_copy_df)

    # Cleanup after the operation by removing the column.
    valid_id_copy_df.drop('normalized_title', axis=1, inplace=True)
    return nielsen_ratings_copy_df, svod_ratings_copy_df, program_ratings_copy_df, valid_id_copy_df


def filter_tv_shows_main_file(nielsen_ratings_df, svod_ratings_df,
                              program_ratings_df, valid_id_df):
    # copy the data frame first.
    tv_shows_main_df = valid_id_df.copy()  # Copy of the main dataframe

    # collect unique titles.
    unique_titles = []

    # Collect unique titles from each transaction dataframe
    for df in [nielsen_ratings_df, svod_ratings_df, program_ratings_df]:
        unique_titles.extend(df['Title'].unique())  # Use extend to add elements to the list

    # Convert the list to a set to get unique titles
    unique_titles = set(unique_titles)

    # Filter the returned data to include only rows with titles that are in unique_titles
    tv_shows_main_df = tv_shows_main_df[tv_shows_main_df['Title'].isin(unique_titles)]

    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING,
                                    show_df_info(tv_shows_main_df, "Filtered TV Series Across Ratings Data"))

    headers = ['ID', 'Title', 'Seasons', 'Episodes', 'Votes', 'Average', 'First Aired', 'Last Aired', 'Status', 'IMDb Series ID', 'Type']
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, pretty_print_df(tv_shows_main_df, rows=20,
                    interesting_columns = ['id', 'Title', 'number_of_seasons', 'number_of_episodes', 'vote_count', 'vote_average', 'first_air_date', 'last_air_date', 'status', 'IMDb Series ID', 'type'],
                    headers = headers))

    return tv_shows_main_df


def filter_by_imdb_series_id(imdb_series_id, nielsen_ratings_df, svod_ratings_df, program_ratings_df):
    nielsen_subset_df = nielsen_ratings_df[nielsen_ratings_df['IMDb Series ID'] == imdb_series_id].copy()
    svod_subset_df = svod_ratings_df[svod_ratings_df['IMDb Series ID'] == imdb_series_id].copy()
    program_ratings_subset_df = program_ratings_df[program_ratings_df['IMDb Series ID'] == imdb_series_id].copy()
    return nielsen_subset_df, svod_subset_df, program_ratings_subset_df


def test_show_rating_info(nielsen_ratings_df, svod_ratings_df, program_ratings_df, show_id = 'tt0944947'):
    nielsen_subset_df, svod_subset_df, program_ratings_subset_df = filter_by_imdb_series_id(nielsen_ratings_df,
                                                                                            svod_ratings_df,
                                                                                            program_ratings_df,
                                                                                            show_id)

    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(nielsen_subset_df, "Nielsen Data"))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(svod_subset_df, "SVOD Data"))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, show_df_info(program_ratings_subset_df,
                                                                        "Archive Ratings Data"))

    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, pretty_print_df(nielsen_subset_df))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, pretty_print_df(svod_subset_df))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, pretty_print_df(program_ratings_subset_df))



def check_pre_merge_subset(df, hint):
    # Group by 'IMDb Series ID' and aggregate unique titles
    title_group = df.groupby('IMDb Series ID')['Title'].unique()

    # Convert unique titles to a DataFrame with a count of titles per IMDb Series ID
    title_count = title_group.apply(lambda titles: len(titles)).reset_index(name='Unique Title Count')

    # Filter to find IMDb IDs associated with more than one unique title
    multiple_titles = title_count[title_count['Unique Title Count'] > 1]

    # Display the results
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, multiple_titles)

    # Optionally, to see the specific titles for these problematic IDs
    problematic_ids = multiple_titles['IMDb Series ID']
    detailed_view = df[df['IMDb Series ID'].isin(problematic_ids)]
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING, detailed_view[['IMDb Series ID', 'Title']].drop_duplicates())


def patch_game_on(nielsen_ratings_df):
    # Update the 'IMDb Series ID' for rows with 'Title' exactly matching 'game on'
    nielsen_ratings_df.loc[nielsen_ratings_df['Title'].str.lower() == 'game on', 'IMDb Series ID'] = 'tt0111976'

    # Verify the update
    print(nielsen_ratings_df[nielsen_ratings_df['Title'].str.lower() == 'game on'][['Title', 'IMDb Series ID']])
    return nielsen_ratings_df


def check_pre_merge(nielsen_subset_df, svod_subset_df, program_ratings_subset_df):
    check_pre_merge_subset(nielsen_subset_df, "Nielsen Data - check pre merge")
    check_pre_merge_subset(svod_subset_df, "SVOD Data - check pre merge")
    check_pre_merge_subset(program_ratings_subset_df, "Program Ratings Data - check pre merge")

