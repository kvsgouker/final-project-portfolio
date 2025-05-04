"""
Project Name: Star Power
File: genres.py

Provides mappings between TMDB genre identifiers and human-readable labels.
Supports genre encoding for modeling and analysis pipelines.

Author: Kyle Salgado-Gouker

"""

import ast
from access.paths import ensure_directories_exist, ALL_DIRECTORIES


def get_genre_names(genre_ids):
    genre_names = []
    for genre_id in genre_ids:
        for genre in tmdb_genre_encoding:
            if genre["id"] == genre_id:
                genre_names.append(genre["name"])
                break
    return ", ".join(genre_names)


tmdb_genre_encoding = {
    10759: "Action & Adventure", 16: "Animation", 28: "Action", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 10762: "Kids",
    9648: "Mystery", 10763: "News", 10764: "Reality", 10765: "Sci-Fi & Fantasy",
    10766: "Soap", 10767: "Talk", 10768: "War & Politics", 37: "Western"
}

# Dynamically updated set of genre names
# Set to collect all genre names found across the dataset
found_genres = {
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama",
    "Family", "Fantasy", "Foreign", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western"
}


def extract_genres(genre_json_str):
    try:
        genres = ast.literal_eval(genre_json_str) if isinstance(genre_json_str, str) else []
        genre_names = [tmdb_genre_encoding.get(g['id'], g['name']) for g in genres if 'id' in g and 'name' in g]
        found_genres.update(genre_names)
        return genre_names
    except Exception:
        return []


def process_genres(df):
    # Apply genre extraction and collect found genres
    df['genre_names'] = df['genres'].apply(extract_genres)

    # One-hot encode
    for genre in sorted(found_genres):
        df[genre] = df['genre_names'].apply(lambda x: genre in x)

    return df


if __name__ == "__main__":
    ensure_directories_exist(ALL_DIRECTORIES)
    genre_ids = [18, 80]
    print(get_genre_names(genre_ids))  # Output: Drama, Crime
