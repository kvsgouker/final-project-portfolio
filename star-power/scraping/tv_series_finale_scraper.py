"""
tv_series_finale_scraper.py

Downloads and parses TV ratings data from tvseriesfinale.com and linked Google Sheets.
Produces a cleaned dataframe of Nielsen ratings and viewer stats.

Be careful!!!

HTML parsing in this module is sensitive to small layout changes on the tvseriesfinale site.
Use caution if updating parsing logic.

Author: Kyle Salgado-Gouker
"""

import os
import re
import pandas as pd
from bs4 import BeautifulSoup

from access.paths import (
    RATINGS_LINK_FILE, TV_SERIES_PAGE_DIRECTORY, RATINGS_DATA_DIRECTORY, RATING_SHEETS_DATA_DIRECTORY
)
from config.settings import SKIP_TO_MODELING, DOWNLOAD_SHEETS, BUILD_RATINGS_FROM_SHEETS
from utils.utilities import show_df_info, word_to_number
from utils.web_utils import download_file, fetch_url_with_retry


# --- Helper: Extract real URL from Google's redirect wrapper ---
def extract_correct_url(href):
    match = re.search(r'(?<=q=)(https?://[^&]+)', href)
    return match.group(0) if match else None


# --- Helper: Convert 'season one' → 1 ---
def extract_season_number(season_string):
    if season_string.lower().startswith("season "):
        part = season_string[7:].strip().lower()
        try:
            return int(part)
        except ValueError:
            return word_to_number.get(part, None)
    return None


# --- Download and store a single Google Sheet page ---
def download_season_html_file(show_name, season, google_docs_link):
    html_output_filename = os.path.join(RATING_SHEETS_DATA_DIRECTORY, f"{show_name}_{season}_sheet.html")
    if not os.path.exists(html_output_filename):
        response = fetch_url_with_retry(google_docs_link['href'])
        if response:
            with open(html_output_filename, "w", encoding='utf-8') as f:
                print("Writing", html_output_filename)
                f.write(response.text)
    else:
        print(f"Already downloaded {html_output_filename}")


# --- Download ratings list and all associated Google Sheets ---
def download_google_sheets():
    if not DOWNLOAD_SHEETS:
        return pd.read_csv(RATINGS_DATA_DIRECTORY + "/tv_shows.csv")

    main_url = "https://tvseriesfinale.com"
    download_file(main_url, RATINGS_LINK_FILE)

    soup = BeautifulSoup(open(RATINGS_LINK_FILE, encoding='utf-8').read(), 'html.parser')
    tv_shows = []

    for ul in soup.find_all('ul', id=re.compile(r'p2-tv-show-list-\\w+')):
        for li in ul.find_all('li'):
            href_tag = li.find('a', href=True)
            if href_tag:
                href = href_tag['href']
                tv_shows.append(href)
                filename = href.replace(main_url + "/tv-show/", "").replace("/", "")
                download_file(href, os.path.join(TV_SERIES_PAGE_DIRECTORY, f"{filename}.html"))

    shows_df = pd.read_csv(RATINGS_DATA_DIRECTORY + "/tv_shows.csv")
    shows_df['Href'] = shows_df['Href'].apply(extract_correct_url)
    shows_df.to_csv(RATINGS_DATA_DIRECTORY + "/tv_shows2.csv", index=False)

    google_docs = []
    for _, row in shows_df.iterrows():
        print("Fetching:", row['Show Name'], "Season:", row['Season'])
        response = fetch_url_with_retry(row['Href'])
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            gdoc_link = soup.find('a', href=re.compile(r'google.com/spreadsheets'))
            google_docs.append(gdoc_link['href'] if gdoc_link else None)
            if gdoc_link:
                download_season_html_file(row['Show Name'], row['Season'], gdoc_link)
        else:
            google_docs.append(None)

    shows_df['Google Docs'] = google_docs
    shows_df.to_csv(RATINGS_DATA_DIRECTORY + "/tv_shows3.csv", index=False)
    return shows_df


# --- Process downloaded Google Sheet HTML files into a DataFrame ---
def build_ratings_from_sheets():
    if not BUILD_RATINGS_FROM_SHEETS:
        return pd.read_csv(RATINGS_DATA_DIRECTORY + "/tv_ratings.csv")

    records = []

    for file in os.listdir(RATING_SHEETS_DATA_DIRECTORY):
        if file.endswith('sheet.html'):
            with open(os.path.join(RATING_SHEETS_DATA_DIRECTORY, file), encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                show = file.split("_")[0]
                season = file.split("_")[1].split("_")[0]

                for row in soup.find_all('tr'):
                    cols = [td.get_text(strip=True) for td in row.find_all('td')]
                    if len(cols) not in (7, 8):
                        continue

                    record = {
                        'Show Name': show,
                        'Season': season,
                        'Day of Week': cols[0],
                        'Air Date': cols[1],
                        'Episode': '',
                        '18-49 Demo': '',
                        'Demo Change': '',
                        'Viewers (millions)': '',
                        'Viewers Change': ''
                    }

                    try:
                        if len(cols) == 8:
                            if cols[7] == "":
                                record.update({
                                    'Episode': cols[2] or cols[3],
                                    '18-49 Demo': cols[3 if cols[2] == "" else 4],
                                    'Demo Change': cols[4 if cols[2] == "" else 5],
                                    'Viewers (millions)': cols[6],
                                    'Viewers Change': cols[6 if cols[2] == "" else 7]
                                })
                            else:
                                record.update({
                                    'Episode': cols[3],
                                    '18-49 Demo': cols[4],
                                    'Demo Change': cols[5],
                                    'Viewers (millions)': cols[6],
                                    'Viewers Change': cols[7]
                                })
                        else:  # len == 7
                            if cols[2] == "":
                                record.update({
                                    'Episode': cols[3],
                                    '18-49 Demo': cols[4],
                                    'Demo Change': '',
                                    'Viewers (millions)': cols[6],
                                    'Viewers Change': ''
                                })
                            else:
                                record.update({
                                    'Episode': cols[2],
                                    '18-49 Demo': cols[3],
                                    'Demo Change': cols[4],
                                    'Viewers (millions)': cols[5],
                                    'Viewers Change': cols[6]
                                })
                        records.append(record)
                    except Exception as e:
                        print(f"Error processing row in {file}: {e}")

    df = pd.DataFrame(records)

    df = df.dropna(subset=['Air Date'])
    df = df.drop(columns=['Demo Change', 'Viewers Change'], errors='ignore')
    df['Air Date'] = pd.to_datetime(df['Air Date'], errors='coerce')
    df = df.dropna(subset=['Air Date', 'Viewers (millions)'])

    df['Season'] = df['Season'].apply(extract_season_number).fillna(9).astype(int)
    show_df_info(df, "ratings")
    df.to_csv(RATINGS_DATA_DIRECTORY + "/tv_ratings2.csv", index=False)
    return df


# --- Entry point wrapper ---
def scrate_tv_series_finale():
    if SKIP_TO_MODELING:
        return pd.read_csv(RATINGS_DATA_DIRECTORY + "/tv_ratings.csv")
    download_google_sheets()
    return build_ratings_from_sheets()


if __name__ == '__main__':
    df = scrate_tv_series_finale()
    show_df_info(df, "ratings")
