"""
Project Name: Star Power
File: imdb_scraper.py

Includes scraper for series and film pages
Author: Kyle Salgado-Gouker.
"""

#### New Algorithm for IMDb Page Fetch
import json
import os
import random
import time
import urllib

import pandas as pd
from bs4 import BeautifulSoup

from access.paths import RATINGS_DATA_DIRECTORY, DATA_DIRECTORY, MOVIE_HTML_DIRECTORY, MOVIE_CONTENT_HTML_DIRECTORY, \
    ensure_directories_exist, ALL_DIRECTORIES
from processing.merge_imdb_cache import IMDbCache
from utils.film_log import FilmLog
from utils.utilities import pretty_print_df, show_df_info
from utils.web_utils import fetch_url_with_retry, download_file
import re

DO_IMDB_MOVIE_PAGE_DOWNLOAD = False

def find_tv_series(title):
    encoded_title = urllib.parse.quote(title.lower().strip())
    page_to_download = f"https://www.imdb.com/find?q={encoded_title}&s=tt&ttype=tv&ref_=fn_tv"
    response = fetch_url_with_retry(page_to_download)
    return response


def extract_tv_title_info_from_html(title, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    if script_tag:
        data = json.loads(script_tag.string)
        results = data.get('props', {}).get('pageProps', {}).get('titleResults', {}).get('results', [])
        if results:
            return {'IMDb Series ID': results[0].get('id'), 'Title Type': results[0].get('titleTypeText')}
        else:
            print("No results found for", title)
    else:
        print("Script tag with the ID '__NEXT_DATA__' not found for", title)
    return {'IMDb Series ID': None, 'Title Type': None}


def get_series_imdb_info(title):
    imdb_html_response = find_tv_series(title)
    if imdb_html_response:
        series_info = extract_tv_title_info_from_html(title, imdb_html_response.content)
        if series_info is None:
            return {'IMDb Series ID': None, 'Title Type': None}
        return series_info
    else:
        return {'IMDb Series ID': None, 'Title Type': None}

def get_series_imdb_info_with_cache(title):
    cache = IMDbCache.get_instance()
    title_key = title.lower().strip()
    if title in cache:
        return cache[title]
    FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"{title} not found")
    imdb_info = get_series_imdb_info(title)
    cache[title] = imdb_info
    return imdb_info

def apply_imdb_info(row):
    result = get_series_imdb_info_with_cache(row['Title'])
    return pd.Series([result['IMDb Series ID'], result['Title Type']])

def generate_valid_series_dataset(shows_with_gt_5_ratings_df):

    #### Add New Columns to DF
    # Apply the caching function to DataFrame and create new columns
    shows_with_gt_5_ratings_df[['IMDb Series ID', 'Title Type']] = shows_with_gt_5_ratings_df.apply(apply_imdb_info, axis=1)
    #### Write CSV File - Intermediate Step
    tmdb_tv_updated_dataset_file = RATINGS_DATA_DIRECTORY + "/TMDB_tv_dataset_v4.csv"
    shows_with_gt_5_ratings_df.to_csv(tmdb_tv_updated_dataset_file, index=False)

    #### Fix Missing IDs
    # Filter rows where 'IMDb Series ID' is either NaN, None, or an empty string
    missing_id_df = shows_with_gt_5_ratings_df[shows_with_gt_5_ratings_df['IMDb Series ID'].isna() | (shows_with_gt_5_ratings_df['IMDb Series ID'] == '')]

    # Show titles with missing imdb id.
    FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, missing_id_df['Title'])

    cache = IMDbCache.get_instance()
    for title in missing_id_df['Title']:
        title_key = title.lower().strip()
        cache.delete(title_key)

    shows_with_gt_5_ratings_df[['IMDb Series ID', 'Title Type']] = shows_with_gt_5_ratings_df.apply(apply_imdb_info, axis=1)

    # Filter rows where 'IMDb Series ID' is either NaN, None, or an empty string
    missing_id_df = shows_with_gt_5_ratings_df[shows_with_gt_5_ratings_df['IMDb Series ID'].isna() | (shows_with_gt_5_ratings_df['IMDb Series ID'] == '')]

    # Show the DataFrame titles with missing 'IMDb Series ID'
    FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, missing_id_df['Title'])

    # Filter out rows with missing 'IMDb Series ID'
    valid_id_df = shows_with_gt_5_ratings_df[shows_with_gt_5_ratings_df['IMDb Series ID'].notna() & (shows_with_gt_5_ratings_df['IMDb Series ID'] != '')]

    valid_id_dataset_file = RATINGS_DATA_DIRECTORY + "/TMDB_tv__valid_id_dataset.csv"
    valid_id_df.to_csv(valid_id_dataset_file, index=False)

    FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, show_df_info(valid_id_df, "Validated TV Series DataFrame Filtered from TMDB"))
    headers = ['ID', 'Title', 'Seasons', 'Episodes', 'Votes', 'Average', 'First Aired', 'Last Aired', 'Status', 'IMDb Series ID', 'Type']
    FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, pretty_print_df(valid_id_df, rows=10,
                    interesting_columns = ['id', 'Title', 'number_of_seasons', 'number_of_episodes', 'vote_count', 'vote_average', 'first_air_date', 'last_air_date', 'status', 'IMDb Series ID', 'type'],
                   headers = headers))
    return valid_id_df


def find_tv_series_episode_page(imdb_id, season=1):
    page_to_request = f"https://www.imdb.com/title/{imdb_id}/episodes/?season={season}&ref_=ttep_ep_sn_nx"
    response = fetch_url_with_retry(page_to_request)
    return response.content if response else None


def get_tv_series_episodes(imdb_id, series_title):
    season_count = 1
    episodes_data = []

    print("Processing Series: ", series_title)

    while True:
        html_content = find_tv_series_episode_page(imdb_id, season_count)
        if not html_content:
            print(f"No content returned for {series_title} Season {season_count}")
            break

        soup = BeautifulSoup(html_content, 'html.parser')
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if not script_tag:
            print(f"No relevant script tag found for {series_title} Season {season_count}")
            break  # Stop if no relevant script tag is found

        data = json.loads(script_tag.string)

        # Check if each key exists in the JSON structure
        if 'props' in data and 'pageProps' in data['props'] and 'contentData' in data['props']['pageProps']:
            section = data['props']['pageProps']['contentData'].get('section')
            if section:
                season_list = section.get('seasons', [])
                episode_list = section.get('episodes', {}).get('items', [])
            else:
                print(f"No 'section' found in JSON data for {series_title} Season {season_count}")
                break
        else:
            print(f"JSON structure does not contain expected keys for {series_title} Season {season_count}")
            break

        if not episode_list:
            print(f"No episodes found for {series_title} Season {season_count}")
        else:
            for episode in episode_list:
                release_date = episode.get('releaseDate')
                if release_date:
                    formatted_release_date = "{}-{}-{}".format(release_date.get('year'), release_date.get('month'),
                                                               release_date.get('day'))
                else:
                    formatted_release_date = None  # Use None if release date is missing

                episodes_data.append({
                    "IMDb Series ID": imdb_id,
                    "IMDb Episode ID": episode['id'],
                    "type": episode['type'],
                    "season": season_count,
                    "episode": episode['episode'],
                    "title": episode['titleText'],
                    "releaseDate": formatted_release_date,
                    "releaseYear": episode.get('releaseYear'),
                    "rating": episode.get('aggregateRating', None),
                    "voteCount": episode.get('voteCount', 0)  # Default to 0 if no votes
                })

        season_count += 1
        if season_count > len(season_list):
            break

    return pd.DataFrame(episodes_data)


def episode_query_test(imdb_id = 'tt0903747'):
    # Example use case
    episode_df = get_tv_series_episodes(imdb_id, "Breaking Bad")
    show_df_info(episode_df, "Episodes")
    pretty_print_df(episode_df, rows=10)
    return episode_df


def concatenate_episodes(dataframes, titles):
    # Standardize columns and data types
    columns = ["IMDb Series ID", "IMDb Episode ID", "type", "season", "episode",
               "title", "releaseDate", "releaseYear", "rating", "voteCount"]
    dtypes = {
        "IMDb Series ID": "string",
        "IMDb Episode ID": "string",
        "type": "string",
        "season": "Int64",  # Use nullable integer type
        "episode": "Int64",  # Use nullable integer type
        "title": "string",
        "releaseDate": "string",
        "releaseYear": "Int64",  # Use nullable integer type
        "rating": "float",
        "voteCount": "Int64"  # Use nullable integer type
    }

    standardized_dfs = []
    for df, title in zip(dataframes, titles):
        if not df.empty:
            # Ensure the DataFrame has all the necessary columns with correct dtypes
            for col in columns:
                if col not in df.columns:
                    df[col] = pd.Series(dtype=dtypes[col])
                else:
                    df[col] = df[col].astype(dtypes[col])
            standardized_dfs.append(df)
        else:
            print(f"Empty or all-NA DataFrame found for series: {title}")

    if not standardized_dfs:
        return pd.DataFrame(columns=columns)

    # Concatenate all standardized DataFrames into one
    all_episodes_df = pd.concat(standardized_dfs, ignore_index=True)
    return all_episodes_df


def imdb_series_scraping(tv_shows_main_df):
    # Collecting episodes data
    all_episodes = []
    series_titles = []

    for idx, row in tv_shows_main_df.iterrows():
        series_title = row['Title']
        series_imdb_id = row['IMDb Series ID']
        episode_df = get_tv_series_episodes(series_imdb_id, series_title)
        all_episodes.append(episode_df)
        series_titles.append(series_title)

    all_episodes_df = concatenate_episodes(all_episodes, series_titles)

    show_df_info(all_episodes_df, "Episodes")
    pretty_print_df(all_episodes_df, rows=100)

    all_episodes_df.to_csv(DATA_DIRECTORY + "/episode_info.csv", index = False)
    return all_episodes_df


def parse_movie_page(imdb_id, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    movie_data = {'imdb_id': imdb_id}

    # Top Cast extraction
    cast_section = soup.select('div[data-testid="title-cast-item"]')
    top_cast = []

    imdb_cast_map = {}

    for imdb_order, cast_item in enumerate(cast_section[:10]):  # Limit to 10 here
        actor_link = cast_item.select_one('a[data-testid="title-cast-item__actor"]')
        character_tag = cast_item.select_one('ul li a span')

        if actor_link:
            actor = actor_link.get_text(strip=True)
            character = character_tag.get_text(strip=True) if character_tag else ""

            # Extract IMDb person ID from href
            href = actor_link.get('href', '')
            match = re.search(r'/name/(nm\d+)/', href)
            imdb_id = match.group(1) if match else None

            top_cast.append((actor, imdb_order, imdb_id, character))

            # Build cast map for merging
            imdb_cast_map[actor.lower()] = {
                "imdb_name": actor,
                "imdb_order": imdb_order,
                "imdb_id": imdb_id,
                "character": character
            }

    # Pad to 10 if fewer found
    while len(top_cast) < 10:
        top_cast.append(("", "", "", ""))

    # Flatten into movie_data
    for idx, (actor, imdb_order, imdb_id, character) in enumerate(top_cast, start=1):
        movie_data[f'actor_name_{idx}'] = actor
        movie_data[f'actor_imdb_order_{idx}'] = imdb_order
        movie_data[f'actor_imdb_id_{idx}'] = imdb_id
        movie_data[f'character_{idx}'] = character

    # Genre
    genre_section = soup.select('div[data-testid="interests"] span.ipc-chip__text')
    movie_data['genres'] = ", ".join(
        genre_tag.get_text(strip=True) for genre_tag in genre_section
    ) if genre_section else ""

    # Certificate
    details_section = soup.select('section[data-testid="Title-details"] li')

    certificate_text = None

    for item in details_section:
        button = item.select_one('button')
        if button and button.get_text(strip=True) == 'Certificate':
            cert_li = item.select_one('div ul li')
            if cert_li:
                certificate_text = cert_li.get_text(strip=True)
                if certificate_text and ':' in certificate_text:
                    movie_data['certificate'] = certificate_text.split(':', 1)[1].strip()
                else:
                    movie_data['certificate'] = certificate_text
            break

    movie_data['certificate'] = 'Unknown'

    # Box Office
    box_office = {}
    budget_tag = soup.find('li', attrs={'data-testid': 'title-boxoffice-budget'})
    gross_us_tag = soup.find('li', attrs={'data-testid': 'title-boxoffice-grossdomestic'})
    gross_worldwide_tag = soup.find('li', attrs={'data-testid': 'title-boxoffice-cumulativeworldwidegross'})

    if budget_tag:
        movie_data['imdb_budget'] = budget_tag.find('span', class_='ipc-metadata-list-item__list-content-item').text
    if gross_us_tag:
        movie_data['imdb_domestic_revenue'] = gross_us_tag.find('span',
                                                          class_='ipc-metadata-list-item__list-content-item').text
    if gross_worldwide_tag:
        movie_data['imdb_worldwide_revenue'] = gross_worldwide_tag.find('span',
                                                                 class_='ipc-metadata-list-item__list-content-item').text

    # Technical Specs
    runtime_tag = soup.find('li', attrs={'data-testid': 'title-techspec_runtime'})
    color_tag = soup.find('li', attrs={'data-testid': 'title-techspec_color'})
    sound_tag = soup.find('li', attrs={'data-testid': 'title-techspec_soundmix'})
    aspect_tag = soup.find('li', attrs={'data-testid': 'title-techspec_aspectratio'})

    movie_data['runtime'] = runtime_tag.find('div',
                                             class_='ipc-metadata-list-item__content-container').text if runtime_tag else None
    movie_data['color'] = color_tag.find('div',
                                         class_='ipc-metadata-list-item__content-container').text if color_tag else None
    movie_data['sound_mix'] = sound_tag.find('div',
                                             class_='ipc-metadata-list-item__content-container').text if sound_tag else None
    movie_data['aspect_ratio'] = aspect_tag.find('div',
                                                 class_='ipc-metadata-list-item__content-container').text if aspect_tag else None

    # Release Details
    release_tag = soup.find('li', attrs={'data-testid': 'title-details-releasedate'})
    country_tag = soup.find('li', attrs={'data-testid': 'title-details-origin'})
    language_tag = soup.find('li', attrs={'data-testid': 'title-details-languages'})

    movie_data['release_date'] = release_tag.find('a').text if release_tag and release_tag.find('a') else None
    movie_data['country_of_origin'] = country_tag.find('a').text if country_tag and country_tag.find('a') else None
    movie_data['language'] = language_tag.find('a').text if language_tag and language_tag.find('a') else None

    # print(imdb_id, movie_data)

    return movie_data


def parse_movie_content_page(imdb_id, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Define the categories
    categories = {
        "Sex & Nudity": "Sex",
        "Violence & Gore": "Violence",
        "Profanity": "Profanity",
        "Alcohol, Drugs & Smoking": "Drugs",
        "Frightening & Intense Scenes": "Intense"
    }

    severity_levels = ["None", "Mild", "Moderate", "Severe"]
    content_warnings = {
        short: {level: 0 for level in severity_levels} | {"Report Count": 0}
        for short in categories.values()
    }
    descriptions = []

    # ----- 1. Try JSON-based parsing first -----
    parents_guide_data = None
    for script in soup.find_all('script', type='application/ld+json'):
        if script.string and '"@type":"ParentsGuide"' in script.string:
            try:
                parents_guide_data = json.loads(script.string)
                break
            except Exception:
                continue

    if parents_guide_data:
        if 'parentsGuideCategorySummaries' in parents_guide_data:
            for entry in parents_guide_data['parentsGuideCategorySummaries']:
                label = entry.get('category', {}).get('displayName', '').strip()
                severity = entry.get('severity', 'None').capitalize()
                short_category = categories.get(label)
                if short_category and severity in severity_levels:
                    content_warnings[short_category][severity] += 1

        if 'parentsGuideItems' in parents_guide_data:
            for item in parents_guide_data['parentsGuideItems']:
                label = item.get('category', {}).get('displayName', '').strip()
                text = item.get('content', '').strip()
                short_category = categories.get(label)
                if text and short_category:
                    descriptions.append([imdb_id, short_category[0], text])
                    content_warnings[short_category]["Report Count"] += 1

    else:
        # ----- 2. Fallback: HTML-based parsing -----
        for section in soup.select("section.ipc-page-section"):
            heading = section.find("h3")
            if not heading:
                continue

            heading_text = heading.get_text(strip=True)
            short_category = categories.get(heading_text)
            if not short_category:
                continue

            # Find severity
            severity_tag = section.find("div", class_="ipc-signpost__text")
            severity = severity_tag.get_text(strip=True) if severity_tag else "None"
            if severity in severity_levels:
                content_warnings[short_category][severity] += 1

            # Find detailed descriptions
            for div in section.select("div.ipc-html-content"):
                description = div.get_text(strip=True)
                if description:
                    descriptions.append([imdb_id, short_category[0], description])
                    content_warnings[short_category]["Report Count"] += 1

    # ----- Build DataFrames -----
    warning_data = {
        "IMDB ID": imdb_id,
        **{f"{cat} - {sev} Votes": count
           for cat, data in content_warnings.items()
           for sev, count in data.items() if sev != "Report Count"},
        **{f"{cat} - Report Count": data["Report Count"]
           for cat, data in content_warnings.items()}
    }

    description_json_str = json.dumps(descriptions, ensure_ascii=False)
    warning_data['Parental Descriptions'] = description_json_str

    return warning_data


def download_movie_pages(imdb_id):
    files_downloaded = 0
    page_to_request = f"https://www.imdb.com/title/{imdb_id}"
    page_filename = os.path.join(MOVIE_HTML_DIRECTORY, f"{imdb_id}.html")
    if not os.path.exists(page_filename):
        files_downloaded += 1
        download_file(page_to_request, page_filename, False)
    page_to_request = f"https://www.imdb.com/title/{imdb_id}/parentalguide/"
    page_filename = os.path.join(MOVIE_CONTENT_HTML_DIRECTORY, f"{imdb_id}_parentalguide.html")
    if not os.path.exists(page_filename):
        files_downloaded += 1
        download_file(page_to_request, page_filename, False)
    return files_downloaded


def process_movie_page(imdb_id):
    page_filename = os.path.join(MOVIE_HTML_DIRECTORY, f"{imdb_id}.html")
    all_movie_data = []
    with open(page_filename, encoding='utf-8') as f:
        content = f.read()
        movie_data = parse_movie_page(imdb_id, content)
        all_movie_data.append(movie_data)
    return pd.DataFrame(all_movie_data)


def process_movie_content_page(imdb_id):
    page_filename = os.path.join(MOVIE_CONTENT_HTML_DIRECTORY, f"{imdb_id}_parentalguide.html")
    all_movie_content_warnings = []
    with open(page_filename, encoding='utf-8') as f:
        content = f.read()
        content_warnings = parse_movie_content_page(imdb_id, content)
        all_movie_content_warnings.append(content_warnings)
    return pd.DataFrame(all_movie_content_warnings)


# This function processes all the related pages

def parse_imdb_movie_pages(imdb_id):
	imdb_movie_metadata_df = process_movie_page(imdb_id)
	imdb_movie_content_warnings_df = process_movie_content_page(imdb_id)
	return imdb_movie_metadata_df, imdb_movie_content_warnings_df


if __name__ == "__main__":
    ensure_directories_exist(ALL_DIRECTORIES)

    # Load master imdb id list
    financial_grouped_with_titles_df = pd.read_csv(os.path.join(DATA_DIRECTORY, "financial_film_grouped_with_titles.csv"))

    # Step 1: Download all pages
    if DO_IMDB_MOVIE_PAGE_DOWNLOAD:
        movie_records_downloaded = 0
        for idx, row in financial_grouped_with_titles_df.iterrows():
            imdb_id = str(row['imdb_id']).zfill(7)  # Zero-pad if needed to match IMDb URL
            movie_records_downloaded += download_movie_pages(imdb_id)
            if movie_records_downloaded > 0 and movie_records_downloaded % 10 == 0:
                sleep_duration = random.uniform(5, 12)  # random float between 5 and 12
                print(f"{movie_records_downloaded} films downloaded. Sleeping for {sleep_duration:.2f} seconds to be polite...")
                time.sleep(sleep_duration)

    # Prepare collectors
    all_metadata = []
    all_content_warnings = []
    all_content_descriptions = []

    # Step 2: Parse all pages

    movies_processed = 0

    for idx, row in financial_grouped_with_titles_df.iterrows():
        imdb_id = str(row['imdb_id']).zfill(7)

        try:
            # imdb_movie_metadata_df, imdb_movie_content_warnings_df = parse_imdb_movie_pages(imdb_id)
            imdb_movie_metadata_df = parse_imdb_movie_pages(imdb_id)
            all_metadata.append(imdb_movie_metadata_df)
            # all_content_warnings.append(imdb_movie_content_warnings_df)
            movies_processed += 1
            if movies_processed % 50 == 0:
                print(f"{movies_processed} films processed.")


        except Exception as e:
            print(f"Failed parsing IMDb ID {imdb_id}: {e}")

    # Final assembly
    all_imdb_movie_metadata_df = pd.concat(all_metadata, ignore_index=True)
    all_imdb_movie_content_warnings_df = pd.concat(all_content_warnings, ignore_index=True)

    # Save results if desired
    all_imdb_movie_metadata_df.to_csv(os.path.join(DATA_DIRECTORY, 'all_imdb_movie_metadata.csv'), index=False)
    all_imdb_movie_content_warnings_df.to_csv(os.path.join(DATA_DIRECTORY, 'all_imdb_movie_content_warnings.csv'),
                                              index=False)
