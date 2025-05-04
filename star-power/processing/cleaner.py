"""
Project Name: Star Power
File: cleaner.py

Cleans IMDB data for tv series.


Author: Kyle Salgado-Gouker
"""

import json
import urllib

import pandas as pd
from bs4 import BeautifulSoup

from access.paths import RATINGS_DATA_DIRECTORY, MOVIE_DATA_DIRECTORY, MOVIE_YEARS_DATA_DIRECTORY, \
    MOVIE_AUDIENCE_DATA_DIRECTORY
from utils.utilities import show_df_info, pretty_print_df
from utils.web_utils import fetch_url_with_retry


#### First attempt to get the ID from IMDb.

# * works
# * has too many failures because it only finds 'TV Series'
# * next iteration corrects this issue but works from a saved cache


def find_tv_series(title):
    encoded_title = urllib.parse.quote(title.lower().strip())
    page_to_download = f"https://www.imdb.com/find?q={encoded_title}&s=tt&ttype=tv&ref_=fn_tv"
    response = fetch_url_with_retry(page_to_download)
    return response


def extract_id_from_html(title, html_content):
    # Load and parse the HTML file
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the <script> tag with the specific ID
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    if script_tag:
        # Parse the JSON content within the <script> tag
        data = json.loads(script_tag.string)

        # Extract the results from the JSON structure
        results = data.get('props', {}).get('pageProps', {}).get('titleResults', {}).get('results', [])
        if results:
            for result in results:
                title_type = result.get('titleTypeText')
                # Check if the result is a TV series
                if title_type == "TV Series":
                    result_id = result.get('id')
                    # print("TV Series ID:", result_id)
                    return result_id  # Stops after finding the first TV series ID
            print("No TV series found in the results for ", title)
        else:
            print("No results found  for ", title)
    else:
        print("Script tag with the ID '__NEXT_DATA__' not found for ", title)
    return None


def get_series_imdb_id(title):
    imdb_html_response = find_tv_series(title)
    if imdb_html_response:
        series_id = extract_id_from_html(title, imdb_html_response.content)
        return series_id
    else:
        return None


def load_and_view_input_dataframes():
    tv_series_file = RATINGS_DATA_DIRECTORY + "/TV Series.csv"
    tmdb_tv_file = RATINGS_DATA_DIRECTORY + "/TMDB_tv_dataset_v3.csv"

    tmdb_tv_df = pd.read_csv(tmdb_tv_file)
    show_df_info(tmdb_tv_df, "tmdb tv info")

    pretty_print_df(tmdb_tv_df, rows=25,
                    interesting_columns=['id', 'name', 'number_of_seasons', 'number_of_episodes', 'vote_count',
                                         'vote_average', 'first_air_date', 'last_air_date', 'status',
                                         'episode_run_time'])

    tv_series_df = pd.read_csv(tv_series_file)
    show_df_info(tv_series_df, "tv series info")

    pretty_print_df(tv_series_df, rows=25, interesting_columns=['Series Title', 'Release Year', 'Runtime', 'Rating'])

    # file names of spreadsheets.
    nielsen_ratings_file = RATINGS_DATA_DIRECTORY + "/tv_ratings2.csv"
    svod_ratings_file = RATINGS_DATA_DIRECTORY + "/svod_ratings2.csv"
    program_ratings_file = RATINGS_DATA_DIRECTORY + "/programs_ratings.csv"
    tmdb_tv_dataset_file = RATINGS_DATA_DIRECTORY + "/TMDB_tv_dataset_v3.csv"
    tmdb_tv_updated_dataset_file = RATINGS_DATA_DIRECTORY + "/TMDB_tv_dataset_v4.csv"

    tv_series_file = RATINGS_DATA_DIRECTORY + "/TV Series.csv"
    tmdb_movie_database_file = MOVIE_DATA_DIRECTORY + "/" + "TMDB_movie_dataset_v11.csv"
    movies_by_year_file = MOVIE_YEARS_DATA_DIRECTORY + "/movies_by_year3.csv"
    movie_audience_file = MOVIE_AUDIENCE_DATA_DIRECTORY + "/movies_audiences.csv"
    franchise_members_file = MOVIE_DATA_DIRECTORY + "/" + "franchise_members.csv"
    branch_members_file = MOVIE_DATA_DIRECTORY + "/" + "brand_members.csv"

    # read spreadsheets
    nielsen_ratings_df = pd.read_csv(nielsen_ratings_file)
    svod_ratings_df = pd.read_csv(svod_ratings_file)
    program_ratings_df = pd.read_csv(program_ratings_file)
    tmdb_tv_df = pd.read_csv(tmdb_tv_dataset_file)
    tv_series_df = pd.read_csv(tv_series_file)
    movies_by_year_df = pd.read_csv(movies_by_year_file)
    movies_audiences_df = pd.read_csv(movie_audience_file)
    franchise_members_df = pd.read_csv(franchise_members_file)
    brand_members_df = pd.read_csv(branch_members_file)

    show_df_info(nielsen_ratings_df, "Nielsen Viewers")
    show_df_info(svod_ratings_df, "Video on Demand")
    show_df_info(program_ratings_df, "Archive Program Ratings")

    tmdb_movie_df = pd.read_csv(tmdb_movie_database_file)
    show_df_info(tmdb_tv_df, "TMDB tv database")

    show_df_info(tv_series_df, "tv series info")
    show_df_info(tmdb_movie_df, "films data base")
    show_df_info(movies_by_year_df, "films by year")
    show_df_info(movies_audiences_df, "film audience numbers")
    show_df_info(franchise_members_df, "franchise releases")
    show_df_info(brand_members_df, "brand releases")

    pretty_print_df(nielsen_ratings_df, rows=10)
    pretty_print_df(svod_ratings_df, rows=10)
    pretty_print_df(program_ratings_df, rows=10)
    pretty_print_df(tmdb_tv_df, rows=25,
                    interesting_columns=['id', 'name', 'number_of_seasons', 'number_of_episodes', 'vote_count',
                                         'vote_average', 'first_air_date', 'last_air_date', 'status',
                                         'episode_run_time'])
    pretty_print_df(tv_series_df, rows=25, interesting_columns=['Series Title', 'Release Year', 'Runtime', 'Rating'])
    pretty_print_df(tmdb_movie_df, rows=10,
                    interesting_columns=['id', 'title', 'vote_count', 'vote_average', 'release_date', 'revenue',
                                         'budget',
                                         'runtime'])
    pretty_print_df(movies_by_year_df, rows=10,
                    interesting_columns=['Film ID', 'Release', 'Budget', 'Release Date', 'Domestic', 'International',
                                         'Worldwide'])
    pretty_print_df(movies_audiences_df, rows=10)
    pretty_print_df(franchise_members_df, rows=15)
    pretty_print_df(brand_members_df, rows=15)

    show_df_info(movies_by_year_df, "films by year")


def clean_ratings(nielsen_ratings_df, svod_ratings_df, program_ratings_df):
    #### Normalize Column Names for Title
    nielsen_ratings_df = nielsen_ratings_df.rename(columns={'Show Name': 'Title'})
    svod_ratings_df = svod_ratings_df.rename(columns={'Show': 'Title'})
    program_ratings_df = program_ratings_df.rename(columns={'Show': 'Title'})
    return nielsen_ratings_df, svod_ratings_df, program_ratings_df


def clean_and_filter_tmdb(tmdb_tv_df):
    tmdb_tv_df = tmdb_tv_df.rename(columns={'name': 'Title'})
    # #### More Cleanup
    # * Drop Rows without Homepage
    # * Prepare Title Field with '' instead of NaN

    # Dropping rows where the 'homepage' column is NaN or an empty string
    tmdb_tv_df.dropna(subset=['homepage'], inplace=True)
    tmdb_tv_df = tmdb_tv_df[tmdb_tv_df['homepage'].str.strip() != '']

    # Now, update the 'Title' column for any potential NaN values to avoid errors during the IMDb ID fetching process
    tmdb_tv_df['Title'] = tmdb_tv_df['Title'].fillna('')

    #### Must Have More Than One Vote (eliminates garbage)

    # Filter out rows where 'vote_count' is less than 1
    tmdb_tv_df = tmdb_tv_df[tmdb_tv_df['vote_count'] >= 1]

    show_df_info(tmdb_tv_df, "tv series after filtering")

    #### Subset of 5 votes or more.

    tmdb_tv_df_vt_ge_5 = tmdb_tv_df.copy()
    tmdb_tv_df_vt_ge_5 = tmdb_tv_df_vt_ge_5[tmdb_tv_df_vt_ge_5['vote_count'] >= 5]
    show_df_info(tmdb_tv_df_vt_ge_5, "tv series >= 5 after filtering")

    pretty_print_df(tmdb_tv_df_vt_ge_5, rows=50, interesting_columns = ['id', 'Title', 'number_of_seasons', 'number_of_episodes', 'vote_count', 'vote_average', 'first_air_date', 'last_air_date', 'status', 'episode_run_time'])
    return tmdb_tv_df, tmdb_tv_df_vt_ge_5


