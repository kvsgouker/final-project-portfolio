"""
Project Name: Star Power
File: imdb_tmdb_bridge.py

Downloads important data from IMDB film pages.


Author: Kyle Salgado-Gouker
"""

import os
import pandas as pd
from access.paths import DATA_DIRECTORY, MOVIES_METADATA_FILE
import unicodedata
import re

from utils.film_log import FilmLog


# Table uses an old star_power.csv file.
# This can be built by turning off extended fields in star_power.csv.

def resolve_imdb_person_id(row):
    imdb_id = str(row['imdb_id']).strip()
    name = str(row['name']).strip().lower()

    key = (imdb_id, name)
    result = imdb_lookup.get(key, None)

    # log results
    if result:
        # msg = f"KEY={key} --> {result.get('imdb_id')}"
        # FilmLog.get_file_logger().log(FilmLog.BRIDGE_LOGGING, msg)
        return result.get("imdb_id", None)
    else:
        # msg = f"❌ No match for key: {key}"
        # FilmLog.get_file_logger().log(FilmLog.BRIDGE_LOGGING, msg)
        return None



def clean_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    # Normalize Unicode (e.g., remove accents), lowercase, strip punctuation/spaces
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')  # Drop accents
    name = re.sub(r"[^\w\s]", "", name)  # Remove punctuation
    return name.strip().lower()


if __name__ == '__main__':

    print("Current directory:", os.getcwd())

    IMDB_MOVIE_METADATA_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_metadata.csv")
    IMDB_MOVIE_CONTENT_WARNING_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_content_warnings.csv")
    STAR_POWER_DATA_FILE = os.path.join(DATA_DIRECTORY, "star_power.csv")

    movies_metadata_dtypes = {
        "adult": "boolean",
        "belongs_to_collection": "string",
        "budget": "Int64",
        "genres": "string",
        "homepage": "string",
        "id": "string",
        "imdb_id": "string",
        "original_language": "string",
        "original_title": "string",
        "overview": "string",
        "popularity": "float64",
        "poster_path": "string",
        "production_companies": "string",
        "production_countries": "string",
        "release_date": "string",
        "revenue": "Int64",
        "runtime": "float64",
        "spoken_languages": "string",
        "status": "string",
        "tagline": "string",
        "title": "string",
        "video": "boolean",
        "vote_average": "float64",
        "vote_count": "Int64"
    }

    movies_metadata_df = pd.read_csv(
        MOVIES_METADATA_FILE
    )

    # Build dtypes for actor columns
    actor_dtypes = {
                       f"actor_name_{i}": "string" for i in range(1, 11)
                   } | {
                       f"actor_imdb_order_{i}": "Int64" for i in range(1, 11)
                   } | {
                       f"actor_imdb_id_{i}": "string" for i in range(1, 11)
                   } | {
                       f"character_{i}": "string" for i in range(1, 11)
                   }

    # Static columns
    metadata_dtypes = {
        "imdb_id": "string",
        "genres": "string",
        "certificate": "string",
        "imdb_budget": "string",
        "imdb_domestic_revenue": "string",
        "imdb_worldwide_revenue": "string",
        "runtime": "string",
        "color": "string",
        "sound_mix": "string",
        "aspect_ratio": "string",
        "release_date": "string",
        "country_of_origin": "string",
        "language": "string"
    }

    imdb_movie_metadata_df = pd.read_csv(
        IMDB_MOVIE_METADATA_FILE,
        dtype=metadata_dtypes | actor_dtypes
    )

    # All category-level vote and report counts
    vote_cols = {
        f"{cat} - {level} Votes": "Int64"
        for cat in ["Sex", "Violence", "Profanity", "Drugs", "Intense"]
        for level in ["None", "Mild", "Moderate", "Severe"]
    }
    report_cols = {
        f"{cat} - Report Count": "Int64"
        for cat in ["Sex", "Violence", "Profanity", "Drugs", "Intense"]
    }

    content_warning_dtypes = {
                                 "IMDB ID": "string",
                                 "Parental Descriptions": "string"
                             } | vote_cols | report_cols

    imdb_movie_content_warning_df = pd.read_csv(
        IMDB_MOVIE_CONTENT_WARNING_FILE,
        dtype=content_warning_dtypes
    )

    # Fill NA for string fields
    string_cols = [col for col in imdb_movie_metadata_df.columns if imdb_movie_metadata_df[col].dtype.name == "string"]
    imdb_movie_metadata_df[string_cols] = imdb_movie_metadata_df[string_cols].fillna("")

    # Fill NA for integer fields (nullable Int64)
    int_cols = [col for col in imdb_movie_metadata_df.columns if "actor_imdb_order_" in col]
    imdb_movie_metadata_df[int_cols] = imdb_movie_metadata_df[int_cols].fillna(0).astype("int64")

    # imdb_movie_content_warning_df.fillna("", inplace=True)

    # print(show_df_info(movies_metadata_df, "Film Metadata"))

    # Get subset of film data.
    selected_movie_fields = [
        'id',  # TMDB Film ID
        'budget',
        'imdb_id',  # IMDB Film ID
        'popularity',
        'release_date',
        'revenue',
        'title',
        'vote_average',
        'vote_count'
    ]

    # Work on a copy of the film metadata.
    film_metadata_subset_df = movies_metadata_df[selected_movie_fields].copy()
    # Rename its id field for consistency (and merge).
    film_metadata_subset_df.rename(columns={
        'id': 'tmdb_id'
    }, inplace=True)

    # debugging: show value_counts() that are greater than 1.
    # print(show_df_info(film_metadata_subset_df, "Film Metadata Subset"))
    dupe_counts = film_metadata_subset_df['tmdb_id'].value_counts()
    # print(dupe_counts[dupe_counts > 1])

    # drop duplicates (saving the highest vote_count and (then) popularity entry)
    film_metadata_subset_df = (
        film_metadata_subset_df
        .sort_values(['vote_count', 'popularity'], ascending=False)
        .drop_duplicates(subset='tmdb_id', keep='first')
    )

    # This gives us a clean TMDB → IMDb map
    tmdb_to_imdb_map = dict(zip(film_metadata_subset_df['tmdb_id'], film_metadata_subset_df['imdb_id']))
    old_star_power_df = pd.read_csv(STAR_POWER_DATA_FILE)

    # Merge IMDb IDs into star_power_df
    old_star_power_df['tmdb_id'] = old_star_power_df['tmdb_id'].astype(str)
    old_star_power_df['imdb_id'] = old_star_power_df['tmdb_id'].map(tmdb_to_imdb_map)

    # Create a lookup dict of (imdb_id, lowercase_name) → cast metadata
    imdb_lookup = {}

    for _, row in imdb_movie_metadata_df.iterrows():
        # Get film row
        imdb_id = row['imdb_id']
        # Get all actors in film cast list.
        for i in range(1, 11):
            name = row[f'actor_name_{i}'].strip().lower()
            if not name:
                continue
            person_data = {
                "imdb_order": row[f"actor_imdb_order_{i}"],
                "imdb_id": row[f"actor_imdb_id_{i}"],
                "character": row[f"character_{i}"]
            }
            # so the key is film id (imdb_id) and name.
            imdb_lookup[(imdb_id, name)] = person_data

    old_star_power_df['imdb_person_id'] = old_star_power_df.apply(resolve_imdb_person_id, axis=1)
    unmatched = old_star_power_df[old_star_power_df['imdb_person_id'].isnull()]

    # Drop rows without a resolved imdb_person_id
    matched_df = old_star_power_df.dropna(subset=['imdb_person_id'])

    # Get number of unique IMDb film IDs with at least one matched person
    unique_matched_films = matched_df['imdb_id'].nunique()

    print(f"Successfully bridged IMDb films: {unique_matched_films}")

    matched_df.to_csv(os.path.join(DATA_DIRECTORY, "bridge_lookup_table.csv"), index=False)
