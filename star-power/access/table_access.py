import pandas as pd


def load_tmdb_movie_metadata(filepath):
    """
    Load the TMDb movie metadata file with proper data types.
    Returns a pandas DataFrame.
    """
    dtypes = {
        "id": "Int64",
        "title": "string",
        "vote_average": "float32",
        "vote_count": "Int32",
        "status": "string",
        "revenue": "Int64",
        "runtime": "float32",
        "adult": "boolean",
        "backdrop_path": "string",
        "budget": "Int64",
        "homepage": "string",
        "imdb_id": "string",
        "original_language": "string",
        "original_title": "string",
        "overview": "string",
        "popularity": "float32",
        "poster_path": "string",
        "tagline": "string",
        "genres": "string",  # could be parsed into lists later
        "production_companies": "string",
        "production_countries": "string",
        "spoken_languages": "string",
        "keywords": "string"
    }

    parse_dates = ["release_date"]

    df = pd.read_csv(filepath, dtype=dtypes, parse_dates=parse_dates, keep_default_na=False, na_values=[""])
    return df


def load_movies_metadata(csv_path):
    """
    Load TMDB movies metadata with appropriate dtype handling.

    Args:
        csv_path (str): Path to the movies_metadata.csv file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with proper dtypes.
    """
    # Define dtypes
    dtypes = {
        "adult": "boolean",
        "belongs_to_collection": "string",
        "budget": "Int64",
        "genres": "string",
        "homepage": "string",
        "id": "string",  # keep as string to preserve leading zeroes
        "imdb_id": "string",
        "original_language": "string",
        "original_title": "string",
        "overview": "string",
        "popularity": "float64",
        "poster_path": "string",
        "production_companies": "string",
        "production_countries": "string",
        "release_date": "string",  # parse separately if needed
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

    # Read CSV
    df = pd.read_csv(csv_path, dtype=dtypes, low_memory=False)

    # Fill missing string values
    string_cols = [col for col, dt in dtypes.items() if dt == "string"]
    df[string_cols] = df[string_cols].fillna("")

    return df


def load_star_power(csv_path):
    """
    Load the star_power.csv file with proper dtypes.

    Args:
        csv_path (str): Path to the star_power.csv file.

    Returns:
        pd.DataFrame: DataFrame with cleaned and typed star power data.
    """
    dtypes = {
        "tmdb_id": "string",
        "person_id": "string",
        "name": "string",
        "character": "string",
        "imdb_order": "float64",
        "tmdb_weight": "float64",
        "imdb_weight": "float64",
        "is_actor": "boolean",
        "is_director": "boolean",
        "is_producer": "boolean",
        "is_executive_producer": "boolean",
        "is_screenplay": "boolean",
        "weight": "float64",
        "delta_weight": "float64"
    }

    df = pd.read_csv(csv_path, dtype=dtypes)

    # Fill string columns if needed
    string_cols = [col for col, dt in dtypes.items() if dt == "string"]
    df[string_cols] = df[string_cols].fillna("")

    return df
