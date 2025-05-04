"""
Project Name: Star Power
File: rt_scraper.py

Scrapes rotten tomatoes pages.

Author: Kyle Salgado-Gouker
"""

from urllib.parse import urlencode

import pandas as pd
import requests
from bs4 import BeautifulSoup

from access.paths import MOVIE_DATA_DIRECTORY
from utils.film_log import FilmLog
from utils.utilities import show_df_info, pretty_print_df
from utils.web_utils import fetch_url_with_retry


def fetch_movie_url_from_rotten_tomatoes(title, release_date):
    try:
        # Properly encode the search parameters
        params = {'search': title}
        query_string = urlencode(params)
        search_url = f"https://www.rottentomatoes.com/search?{query_string}"

        response = fetch_url_with_retry(search_url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            media_rows = soup.find_all('search-page-media-row', {'releaseyear': str(release_date)[:4]}) if pd.notna(
                release_date) else soup.find_all('search-page-media-row')

            for media_row in media_rows:
                link = media_row.find('a', {'data-qa': 'info-name'})
                if link and title.lower() in link.text.lower():
                    print("Found URL:", link['href'], "for", title)
                    return link['href']

            # If no match by release year, take the first match if release date is missing
            if not pd.notna(release_date):
                first_link = soup.find('a', {'data-qa': 'info-name'})
                if first_link:
                    print("Fallback URL:", first_link['href'], "for", title)
                    return first_link['href']

    except requests.RequestException as e:
        print(f"Failed to fetch or parse data for title {title}: {e}")

    return None


def update_franchise_members_rt_columns(franchise_members_df):

    rt_urls = {title: fetch_movie_url_from_rotten_tomatoes(title,
            franchise_members_df[franchise_members_df['Release'] == title]['release_date'].iloc[0]
            if not franchise_members_df[franchise_members_df['Release'] == title]['release_date'].isna().any() else None)
               for title in franchise_members_df['Release'].unique()}


    # Map back the URLs to the original dataframe
    franchise_members_df['Rotten Tomatoes URL'] = franchise_members_df['Release'].apply(lambda x: rt_urls.get(x))

    # Convert release_date to datetime for filtering
    franchise_members_df['release_date'] = pd.to_datetime(franchise_members_df['release_date'], errors='coerce')
    franchise_members_df['year'] = franchise_members_df['release_date'].dt.year

    franchise_members_df.to_csv(MOVIE_DATA_DIRECTORY + "/franchise_members_new2.csv", index=False)
    return franchise_members_df


def filter_franchise_members_to_date_range(franchise_members_df, begin_date = '2018-01-01', end_date = '2024-12-31'):
    filtered_franchise_members_df = franchise_members_df[
        (franchise_members_df['release_date'] >= begin_date) &
        (franchise_members_df['release_date'] <= end_date)
    ]

    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING,
                                    show_df_info(filtered_franchise_members_df, "Filtered Franchise Members"))
    FilmLog.get_shared_logger().log(FilmLog.MERGE_LOGGING,
                                    pretty_print_df(filtered_franchise_members_df, rows=10))
    return filtered_franchise_members_df

