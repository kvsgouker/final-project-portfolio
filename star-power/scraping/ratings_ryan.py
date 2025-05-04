"""
ratings_ryan_scraper.py

Scrapes and processes Nielsen SVOD ratings from RatingsRyan.com into structured CSV files.

This module handles three types of tables:
1. Summary links to Google Docs
2. Ratings by program or episode
3. Ratings by date

It includes redundant but stable HTML parsing logic — most repetition is due to structure variations.

Author: Kyle Salgado-Gouker
"""

import os
import pandas as pd
from bs4 import BeautifulSoup

from access.paths import (
    SVOD_SHEETS_DATA_DIRECTORY, SVOD_GOOGLEDOC_DATA_DIRECTORY,
    SVOD_DAYS_DATA_DIRECTORY, SVOD_PROGRAM_DATA_DIRECTORY, RATINGS_DATA_DIRECTORY
)
from config.settings import DOWNLOAD_RATINGS_SCRAPE_FODDER, BUILD_RATINGS_FROM_SCRAPING
from utils.utilities import show_df_info
from utils.web_utils import download_file


# --- Link Discovery ---
def extract_href_links_with_week_ending(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    week_links, program_links = [], []
    for table in soup.find_all('table'):
        headers = [th.text.strip() for th in table.find_all('th')]
        if 'Week Ending' in headers:
            week_links += [a['href'] for a in table.find_all('a', href=True)]
        if 'Program' in headers:
            program_links += [a['href'] for a in table.find_all('a', href=True)]
    return week_links, program_links


# --- Google Docs HTML Extraction ---
def extract_google_docs_iframe(soup, file_basename):
    """
    Extracts iframe-based embedded Google Docs from a RatingsRyan HTML soup and downloads them.

    Args:
        soup (BeautifulSoup): Parsed HTML soup object from the RatingsRyan page.
        file_basename (str): Base filename (excluding extension) used to name the saved Google Doc HTML.

    Notes:
        - Google Docs are typically embedded via <iframe> tags on RatingsRyan.
        - Saved files are stored in SVOD_GOOGLEDOC_DATA_DIRECTORY and suffixed with `.doc.html`.
    """
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if src:
            print("Found Google Doc in", file_basename)
            output_path = os.path.join(SVOD_GOOGLEDOC_DATA_DIRECTORY, f"{file_basename}.doc.html")
            download_file(src, output_path)


# --- Table Processor ---
def parse_waffle_table(file_path, expected_headers):
    with open(file_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    tables = soup.find_all('table', class_='waffle')
    data = []
    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            continue
        headers = [td.text.strip() for td in rows[0].find_all('td')]
        if headers != expected_headers:
            continue
        for row in rows[1:]:
            values = [td.text.strip() for td in row.find_all('td', class_='s1')]
            data.append(values)
    return data


# --- Generic Ratings Table Extractor ---
def parse_generic_rating_table(file_path, expected_headers, all_columns, drop_label='Average'):
    with open(file_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    tables = soup.find_all('table')
    data = []
    for table in tables:
        tbody = table.find('tbody')
        if not tbody:
            continue
        rows = tbody.find_all('tr')
        if len(rows) < 3:
            continue
        first_row = rows[0].text.strip()
        try:
            show = first_row.split('Season')[0].strip()
            season = first_row.split('Season ')[1].split(' ')[0]
        except Exception:
            try:
                show = first_row.split('(')[0].strip()
                season = 1
            except IndexError:
                continue

        for row in rows[2:]:
            cells = [td.text.strip() for td in row.find_all('td', recursive=False)]
            if not cells or cells[0] == drop_label:
                continue
            row_data = [show, season] + cells
            data.append(row_data[:len(all_columns)])
    return data


# --- Main Processing Function ---
def scrape_ratings_ryan():
    if DOWNLOAD_RATINGS_SCRAPE_FODDER:
        for url in pages_to_download:
            basename = url.split("/")[-1]
            download_file(url, os.path.join(SVOD_SHEETS_DATA_DIRECTORY, basename))

    if DOWNLOAD_RATINGS_SCRAPE_FODDER:
        hrefs, programs = [], []
        for file in os.listdir(SVOD_SHEETS_DATA_DIRECTORY):
            if file.endswith('.html'):
                with open(os.path.join(SVOD_SHEETS_DATA_DIRECTORY, file), encoding='utf-8') as f:
                    html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                extract_google_docs_iframe(soup, file.split('.')[0])
                w_links, p_links = extract_href_links_with_week_ending(html)
                hrefs += w_links
                programs += p_links

        for link in hrefs:
            download_file(link, os.path.join(SVOD_DAYS_DATA_DIRECTORY, link.split("/")[-1]))
        for link in programs:
            download_file(link, os.path.join(SVOD_PROGRAM_DATA_DIRECTORY, link.split("/")[-1]))

    if BUILD_RATINGS_FROM_SCRAPING:
        expected = ['Show', 'Platform', 'Week Ending', 'Minutes (Millions)']
        rows = []
        for file in os.listdir(SVOD_GOOGLEDOC_DATA_DIRECTORY):
            if file.endswith('.html'):
                rows += parse_waffle_table(os.path.join(SVOD_GOOGLEDOC_DATA_DIRECTORY, file), expected)
        svod_weekly_df = pd.DataFrame(rows, columns=expected)
        show_df_info(svod_weekly_df, "svod ratings")
        svod_weekly_df.to_csv(RATINGS_DATA_DIRECTORY + "/svod_ratings2.csv", index=False)
    else:
        svod_weekly_df = pd.read_csv(RATINGS_DATA_DIRECTORY + "/svod_ratings2.csv")

    if BUILD_RATINGS_FROM_SCRAPING:
        episode_cols = ['Show', 'Season', 'Episode Date', 'Viewers (millions)', '18-49 rating']
        episode_raw = []
        for file in os.listdir(SVOD_PROGRAM_DATA_DIRECTORY):
            if file.endswith('.html'):
                episode_raw += parse_generic_rating_table(os.path.join(SVOD_PROGRAM_DATA_DIRECTORY, file),
                                                          expected_headers=None,
                                                          all_columns=episode_cols)
        ratings_by_episode_df = pd.DataFrame(episode_raw, columns=episode_cols)
        ratings_by_episode_df.to_csv(RATINGS_DATA_DIRECTORY + "/programs_ratings.csv", index=False)
    else:
        ratings_by_episode_df = pd.read_csv(RATINGS_DATA_DIRECTORY + "/programs_ratings.csv")

    if BUILD_RATINGS_FROM_SCRAPING:
        daily_cols = ['Show', 'Channel', 'Viewers (millions)', '18-49 rating']
        daily_raw = []
        for file in os.listdir(SVOD_DAYS_DATA_DIRECTORY):
            if file.endswith('.html'):
                daily_raw += parse_generic_rating_table(os.path.join(SVOD_DAYS_DATA_DIRECTORY, file),
                                                        expected_headers=None,
                                                        all_columns=daily_cols)
        channel_daily_df = pd.DataFrame(daily_raw, columns=daily_cols)
        channel_daily_df.to_csv(RATINGS_DATA_DIRECTORY + "/svod_ratings.csv", index=False)
    else:
        channel_daily_df = pd.read_csv(RATINGS_DATA_DIRECTORY + "/svod_ratings.csv")

    return svod_weekly_df, ratings_by_episode_df, channel_daily_df


# --- List of Pages ---
pages_to_download = {
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-disney-originals.html",
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-amazon-prime-video.html",
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-hulu-originals.html",
    "https://www.ratingsryan.com/2023/03/nielsen-svod-ratings-apple.html",
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-netflix-originals.html",
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-netflix-originals_30.html",
    "https://www.ratingsryan.com/2022/01/nielsen-svod-ratings-netflix-originals.html",
    "https://www.ratingsryan.com/2023/01/nielsen-svod-ratings-netflix-originals.html",
    "https://www.ratingsryan.com/2024/02/nielsen-svod-ratings-netflix-originals.html",
    "https://www.ratingsryan.com/2021/12/nielsen-svod-ratings-acquired-programs.html",
    "https://www.ratingsryan.com/2022/07/nielsen-svod-ratings-movies-archive.html",
    "https://www.ratingsryan.com/2022/07/nielsen-svod-ratings-movies-archive_3.html",
    "https://www.ratingsryan.com/2023/01/nielsen-svod-ratings-movies-archive.html",
    "https://www.ratingsryan.com/2024/02/nielsen-svod-ratings-movies-archive.html",
    "https://www.ratingsryan.com/p/ratings-archive.html",
    "https://www.ratingsryan.com/p/a-ratings.html",
    "https://www.ratingsryan.com/p/abc-family-ratings.html",
    "https://www.ratingsryan.com/p/amc-ratings.html",
    "https://www.ratingsryan.com/p/bbca-ratings.html",
    "https://www.ratingsryan.com/p/bravo-ratings.html",
    "https://www.ratingsryan.com/p/cinemax-ratings.html",
    "https://www.ratingsryan.com/p/esquire-ratings.html",
    "https://www.ratingsryan.com/p/fx-ratings.html",
    "https://www.ratingsryan.com/p/fxx-ratings.html",
    "https://www.ratingsryan.com/p/hallmark-ratings.html",
    "https://www.ratingsryan.com/p/hbo-ratings.html",
    "https://www.ratingsryan.com/p/ifc-ratings.html",
    "https://www.ratingsryan.com/p/lifetime.html",
    "https://www.ratingsryan.com/p/miscellaneous-shows.html",
    "https://www.ratingsryan.com/p/mtv-ratings_28.html",
    "https://www.ratingsryan.com/p/pop-tvgn-ratings.html",
    "https://www.ratingsryan.com/p/showtime-ratings.html",
    "https://www.ratingsryan.com/p/starz-ratings.html",
    "https://www.ratingsryan.com/p/sundance-tv-ratings.html",
    "https://www.ratingsryan.com/p/syfy-ratings.html",
    "https://www.ratingsryan.com/p/tnt-ratings.html",
    "https://www.ratingsryan.com/p/tv-land-ratings.html",
    "https://www.ratingsryan.com/p/usa-ratings.html",
    "https://www.ratingsryan.com/p/vh1.html",
    "https://www.ratingsryan.com/p/wgna-ratings.html",
    "https://www.ratingsryan.com/p/2021-22-tv-season.html",
    "https://www.ratingsryan.com/p/2020-21-tv-season.html",
    "https://www.ratingsryan.com/p/summer-2020.html",
    "https://www.ratingsryan.com/p/fall-2018.html",
    "https://www.ratingsryan.com/p/2017-18-tv-season_14.html",
    "https://www.ratingsryan.com/p/2016-17-tv-season.html",
    "https://www.ratingsryan.com/p/2015-16-tv-season.html",
    "https://www.ratingsryan.com/p/2014-15-tv-season.html",
    "https://www.ratingsryan.com/p/2013-14-tv-season.html"
}


if __name__ == "__main__":
    svod_df, ep_df, day_df = scrape_ratings_ryan()
