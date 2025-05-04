"""
Project Name: Star Power
File: star_power.py

Loads the data files, performs merges, executes correlation and regression analysis.
Generates report and plots.

Author: Kyle Salgado-Gouker
"""

import ast
from collections import defaultdict

import numpy as np
import pandas as pd

from access.paths import *
from access.paths import DATA_DIRECTORY, MOVIES_METADATA_FILE
from access.table_access import load_star_power
from analysis.genres import process_genres, tmdb_genre_encoding, found_genres
from analysis.plotting import regression_visualisations
from config.settings import ACTOR_WEIGHTS, CREW_ROLE_WEIGHTS, CPI_INDEX, BASE_CPI, general_modeling_columns, \
    content_modeling_cols, PREPARE_DATA, USE_IMDB_METADATA, DO_STAR_POWER_REBUILD, DEBUG_IMDB_BRIDGE
from processing.modeling import do_all_starpower_correlation_transformations, model_regressions
from utils.utilities import show_df_info, pretty_print_df


def parse_star_power_alt(credits_df, tmdb_to_imdb_map, imdb_lookup):
    combined = defaultdict(lambda: {
        "roles": set(),
        "tmdb_weight": 0.0,
        "imdb_weight": 0.0,
        "name": "",
        "character": "",
        "imdb_order": None
    })

    # One-time name lookup dict
    imdb_name_lookup = defaultdict(dict)
    for (imdb_id, name), data in imdb_lookup.items():
        imdb_name_lookup[imdb_id][name] = data

    print(f"Processing total of {len(credits_df)} credits.")
    for idx, (_, row) in enumerate(credits_df.iterrows(), start=1):
        if idx % 100 == 0:
            print(f"[parse_star_power_alt] Processed {idx} records...")

        tmdb_id = str(row["id"])
        all_cast_crew_set = set()

        imdb_id = tmdb_to_imdb_map.get(tmdb_id)
        imdb_cast_map = {
            name_key: data
            for (film_id, name_key), data in imdb_lookup.items()
            if film_id == imdb_id
        }

        try:
            cast = ast.literal_eval(row["cast"])
            for tmdb_order, member in enumerate(cast):
                person_id = str(member.get("id"))
                name = member.get("name", "").lower()

                if not person_id or (person_id, "Actor") in all_cast_crew_set:
                    continue
                all_cast_crew_set.add((person_id, "Actor"))

                key = (tmdb_id, person_id)
                combined[key]["roles"].add("Actor")
                combined[key]["name"] = member.get("name", "")

                # Try fast match by IMDb ID → name
                matched = imdb_cast_map.get(name)

                # Try fallback dictionary-based lookup
                if not matched:
                    matched = imdb_name_lookup.get(imdb_id, {}).get(name)

                tmdb_weight = ACTOR_WEIGHTS[tmdb_order] if tmdb_order < len(ACTOR_WEIGHTS) else ACTOR_WEIGHTS[-1]

                if matched:
                    order = int(matched["imdb_order"])
                    weight = ACTOR_WEIGHTS[order] if order < len(ACTOR_WEIGHTS) else ACTOR_WEIGHTS[-1]
                    combined[key]["imdb_weight"] += weight
                    combined[key]["tmdb_weight"] = tmdb_weight
                    combined[key]["character"] = matched["character"]
                    combined[key]["imdb_order"] = order
                else:
                    combined[key]["tmdb_weight"] = tmdb_weight
        except Exception:
            pass

        # === Crew remains unchanged ===
        try:
            crew = ast.literal_eval(row['crew'])
            role_counts = defaultdict(int)
            for member in crew:
                role = member.get("job")
                if role in CREW_ROLE_WEIGHTS:
                    role_counts[role] += 1

            for member in crew:
                role = member.get("job")
                person_id = str(member.get('id'))
                if not person_id or (person_id, role) in all_cast_crew_set:
                    continue
                all_cast_crew_set.add((person_id, role))

                if role not in CREW_ROLE_WEIGHTS:
                    continue
                key = (tmdb_id, person_id)
                combined[key]["roles"].add(role)
                base_weight = CREW_ROLE_WEIGHTS[role]
                adjusted_weight = base_weight / role_counts[role]
                combined[key]["tmdb_weight"] += adjusted_weight
                combined[key]["imdb_weight"] += adjusted_weight
                combined[key]["name"] = member.get("name")
        except Exception:
            pass

    # === Final output ===
    records = []
    for (tmdb_id, person_id), entry in combined.items():
        roles = entry["roles"]
        records.append({
            "tmdb_id": tmdb_id,
            "person_id": person_id,
            "name": entry["name"],
            "character": entry["character"],
            "imdb_order": entry["imdb_order"],
            "tmdb_weight": entry["tmdb_weight"],
            "imdb_weight": entry["imdb_weight"],
            "is_actor": "Actor" in roles,
            "is_director": "Director" in roles,
            "is_producer": "Producer" in roles,
            "is_executive_producer": "Executive Producer" in roles,
            "is_screenplay": "Screenplay" in roles
        })

    return pd.DataFrame(records).drop_duplicates(subset=["tmdb_id", "person_id"], keep="first")


def parse_star_power(credits_df):

    combined = defaultdict(lambda: {
        "roles": set(),
        "weight": 0.0,
        "name": None,
    })

    for _, row in credits_df.iterrows():
        tmdb_id = str(row['id'])
        all_cast_crew_set = set()

        # === Parse and deduplicate Cast ===
        try:
            cast = ast.literal_eval(row['cast'])
            for i, member in enumerate(cast[:len(ACTOR_WEIGHTS)]):
                person_id = str(member.get('id'))
                if not person_id:
                    continue
                role = "Actor"
                if not person_id or (person_id, role) in all_cast_crew_set:
                    continue
                all_cast_crew_set.add((person_id, role))
                key = (tmdb_id, person_id)
                combined[key]["roles"].add("Actor")

                weight = ACTOR_WEIGHTS[i]
                combined[key]["weight"] += weight
                combined[key]["name"] = member.get("name")
        except Exception:
            pass

        # === Parse and deduplicate Crew ===
        try:
            crew = ast.literal_eval(row['crew'])
            role_counts = defaultdict(int)
            for member in crew:
                role = member.get("job")
                if role in CREW_ROLE_WEIGHTS:
                    role_counts[role] += 1

            for member in crew:
                role = member.get("job")
                person_id = str(member.get('id'))
                if not person_id or (person_id, role) in all_cast_crew_set:
                    continue
                all_cast_crew_set.add((person_id, role))

                if role not in CREW_ROLE_WEIGHTS:
                    continue
                key = (tmdb_id, person_id)
                combined[key]["roles"].add(role)
                base_weight = CREW_ROLE_WEIGHTS[role]
                adjusted_weight = base_weight / role_counts[role]
                combined[key]["weight"] += adjusted_weight
                combined[key]["name"] = member.get("name")
        except Exception:
            pass

    # === Build final dataframe ===
    records = []

    for (tmdb_id, person_id), entry in combined.items():
        roles = entry["roles"]

        records.append({
            "tmdb_id": tmdb_id,
            "person_id": person_id,
            "name": entry["name"],
            "weight": entry["weight"],
            "is_actor": "Actor" in roles,
            "is_director": "Director" in roles,
            "is_producer": "Producer" in roles,
            "is_executive_producer": "Executive Producer" in roles,
            "is_screenplay": "Screenplay" in roles
        })

    weighted_credits_df = pd.DataFrame(records)

    # Drop duplicate tmdb_id + person_id combinations
    weighted_credits_df = weighted_credits_df.drop_duplicates(subset=["tmdb_id", "person_id"], keep="first")
    return weighted_credits_df


# === Star Power Calculation ===
def calculate_sp(df):
    return df['weight'] * np.log1p(df['vote_count']) * df['vote_average']


def calculate_prev_sp(df, num_previous=3):
    """
    Calculates previous sp using shifted weight, vote_count, and vote_average columns.

    Returns:
        pd.DataFrame: The original df with prev_{n}_sp columns and sp_sum_previous.
    """
    for n in range(1, num_previous + 1):
        df[f'prev_{n}_sp'] = (
            df[f'prev_{n}_weight'] *
            np.log1p(df[f'prev_{n}_vote_count']) *
            df[f'prev_{n}_vote_average']
        )

    df['sp_sum_previous'] = df[[f'prev_{n}_sp' for n in range(1, num_previous + 1)]].sum(axis=1)
    return df


def shift_columns_by_person(df, columns, num_previous=3):
    """
    Shifts specified columns by person_id to capture historical data.

    Returns:
        pd.DataFrame: A dataframe with added shifted columns.
    """
    shifted_df = df.copy()
    for n in range(1, num_previous + 1):
        shifted = df.groupby('person_id')[columns].shift(n)
        shifted.columns = [f'prev_{n}_{col}' for col in columns]
        shifted_df = pd.concat([shifted_df, shifted], axis=1)
    return shifted_df


def smart_fill(df, sp_cols):
    global_avg = df[sp_cols].stack().mean()
    for col in sp_cols:
        df[col] = df.groupby('person_id')[col].transform(
            lambda x: x.fillna(x.mean() if not pd.isna(x.mean()) else global_avg)
        )
    return df


# === Inflation Adjustment ===
def adjust_for_inflation(df, cpi_index=CPI_INDEX, base_cpi=BASE_CPI):
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year
    # Interpolate the CPI series to fill missing years
    full_cpi = CPI_INDEX.reindex(range(df['release_year'].min(), df['release_year'].max() + 1))
    full_cpi = full_cpi.interpolate(method='linear')
    df['cpi'] = df['release_year'].map(full_cpi)
    df['budget_adj'] = df['budget'] * (base_cpi / df['cpi'])
    df['revenue_adj'] = df['revenue'] * (base_cpi / df['cpi'])
    return df


# Grouping by film.
def group_by_film(df):
    """
    Aggregate sp at the film level by:
    - Summing the individual sp values
    - Averaging or summing prior sp per person
    Ensures consistency in how sp and past sp are aggregated.

    Args:
        df (pd.DataFrame): The full cast/crew + metadata per film

    Returns:
        pd.DataFrame: Aggregated film-level metrics
    """
    film_agg = df.groupby('tmdb_id').agg({
        'sp': 'sum',
        'budget_adj': 'first',
        'revenue_adj': 'first',
        'sp_sum_previous': 'sum',
        'weight': 'sum'
    }).reset_index()

    film_agg['log_budget_adj'] = np.log1p(film_agg['budget_adj'])
    film_agg['log_revenue_adj'] = np.log1p(film_agg['revenue_adj'])
    return film_agg




def extract_tmdb_genres(row):
    try:
        genres_list = ast.literal_eval(row) if isinstance(row, str) else []
        genre_names = []
        for genre in genres_list:
            genre_id = genre.get('id')
            genre_name = genre.get('name')
            if genre_id not in tmdb_genre_encoding and genre_name:
                tmdb_genre_encoding[genre_id] = genre_name  # Add missing genres
            if genre_id in tmdb_genre_encoding:
                genre_names.append(tmdb_genre_encoding[genre_id])
                found_genres.add(tmdb_genre_encoding[genre_id])
        return genre_names
    except Exception:
        return []


def merge_content_warnings(merged_df, content_warning_df):
    """
    Merge content warning severity data into the main dataset and compute severity factors.
    """

    # Normalize IMDb ID for merge
    content_warning_df = content_warning_df.rename(columns={"IMDB ID": "imdb_id"})
    content_warning_df['imdb_id'] = content_warning_df['imdb_id'].str.strip()

    print(show_df_info(content_warning_df, "Content Warnings"))

    # Merge IMDb content warnings
    merged = merged_df.merge(content_warning_df, on="imdb_id", how="left")

    # Define severity weights
    severity_weights = {"Mild": 1, "Moderate": 8, "Severe": 64}
    categories = ["Sex", "Violence", "Profanity", "Drugs", "Intense"]

    # Compute severity factors
    for cat in categories:
        factor_col = f"{cat.lower()}_factor"
        try:
            merged[factor_col] = (
                severity_weights["Severe"] * merged[f"{cat} - Severe Votes"].fillna(0) +
                severity_weights["Moderate"] * merged[f"{cat} - Moderate Votes"].fillna(0) +
                severity_weights["Mild"] * merged[f"{cat} - Mild Votes"].fillna(0)
            ).astype("Int64")
        except KeyError as e:
            print(f"Warning: Missing column for category {cat}. Skipping.")
            merged[factor_col] = pd.NA

    return merged


def build_star_power(force_data_rebuild=PREPARE_DATA, force_credits_rebuild=DO_STAR_POWER_REBUILD):
    credits_df = pd.read_csv(CREDITS_FILE)

    # Old film metadata (from Kaggle project)
    movies_metadata_df = pd.read_csv(MOVIES_METADATA_FILE)
    print(show_df_info(movies_metadata_df, "TMDB Movie Metadata"))

    # IMDB metadata construction.
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

    # print(show_df_info(credits_df, "Film Credits"))
    # print(show_df_info(keywords_df, "Film Keywords"))
    # print(show_df_info(links_small_df, "Film Links"))
    # print(show_df_info(links_df, "Film Links"))
    # print(show_df_info(movies_metadata_df, "Film Metadata"))
    # print(show_df_info(ratings_small_df, "Film Ratings (small)"))
    # print(show_df_info(ratings_df, "Film Ratings"))

    # print(pretty_print_df_with_json(credits_df, rows=10))

    # Get subset of film data.
    selected_movie_fields = [
        'belongs_to_collection',
        'budget',  # a film generally must have a revenue of twice budget to break even.
        'genres',
        'homepage',
        'id',  # tmdb film id is a key field.
        'imdb_id',
        'original_language',
        'popularity',  # can't really use (post data, keeping it here as a potential target)
        'release_date',  # for month and year
        'revenue',
        'title',
        'vote_average',
        'vote_count'
    ]

    if force_data_rebuild:
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

        # Build a simple TMDB → IMDb map
        tmdb_to_imdb_map = dict(zip(film_metadata_subset_df['tmdb_id'], film_metadata_subset_df['imdb_id']))

        # Create a lookup dict of (imdb_id, lowercase_name) → cast metadata
        # This allows the star power to be parsed from the credits.
        # Optimizes the process by matching actor names limited in scope to a given film.
        imdb_lookup = {}

        for _, row in imdb_movie_metadata_df.iterrows():
            imdb_id = row['imdb_id']
            for i in range(1, 11):
                name = row[f'actor_name_{i}'].strip().lower()
                if not name:
                    continue
                person_data = {
                    "imdb_order": row[f"actor_imdb_order_{i}"],
                    "imdb_id": row[f"actor_imdb_id_{i}"],
                    "character": row[f"character_{i}"]
                }
                imdb_lookup[(imdb_id, name)] = person_data

        # Parse credits to get star powers from contributors (cast and crew, director, producer, and screenwriter).
        if force_credits_rebuild:
            # removing USE_IMDB_METADATA eliminates the Content Advisories and cross check of billing order.
            if USE_IMDB_METADATA:
                star_power_df = parse_star_power_alt(credits_df, tmdb_to_imdb_map, imdb_lookup)
                star_power_df['weight'] = star_power_df['imdb_weight']

                # Compare TMDB vs IMDb weights
                star_power_df["delta_weight"] = star_power_df["imdb_weight"] - star_power_df["tmdb_weight"]

                # Summary stats
                if DEBUG_IMDB_BRIDGE:
                    print(star_power_df["delta_weight"].describe())

                # Optionally flag switched lead roles
                switched = star_power_df[
                    (star_power_df["imdb_order"] == 0) & (star_power_df["tmdb_weight"] < star_power_df["imdb_weight"])
                    ]
                print(f"Lead role reassigned in {len(switched)} cases.")

            else:
                star_power_df = parse_star_power(credits_df)
            star_power_df.to_csv(STAR_POWER_DATA_FILE, index=False)
        else:
            star_power_df = load_star_power(STAR_POWER_DATA_FILE)

        # star_power dataframe has one record per contributor (cast/crew or both) with roles encoded in booleans.
        # debug before merge (no duplicates)
        assert film_metadata_subset_df['tmdb_id'].duplicated().sum() == 0, "Duplicates before merge!"

        # Guarantee tmdb_id is a string in both dataframes
        star_power_df['tmdb_id'] = star_power_df['tmdb_id'].astype(str)
        film_metadata_subset_df['tmdb_id'] = film_metadata_subset_df['tmdb_id'].astype(str)

        # Proceed with merge
        merged_star_power_df = star_power_df.merge(
            film_metadata_subset_df,
            on='tmdb_id',
            how='left',
            suffixes=('', '_duplicate')
        )

        # Clean up fields.
        # 1. Convert release_date to datetime
        merged_star_power_df['release_date'] = pd.to_datetime(
            merged_star_power_df['release_date'], errors='coerce'
        )
        merged_star_power_df['release_year'] = merged_star_power_df['release_date'].dt.year.fillna(0).astype(int)
        merged_star_power_df['release_month'] = merged_star_power_df['release_date'].dt.month.fillna(0).astype(int)

        # 2. numeric conversion for these fields
        merged_star_power_df['budget'] = pd.to_numeric(merged_star_power_df['budget'], errors='coerce')
        merged_star_power_df['revenue'] = pd.to_numeric(merged_star_power_df['revenue'], errors='coerce')
        merged_star_power_df['popularity'] = pd.to_numeric(merged_star_power_df['popularity'], errors='coerce')
        merged_star_power_df['vote_average'] = (
            pd.to_numeric(merged_star_power_df['vote_average'], errors='coerce', downcast='float'))
        merged_star_power_df['vote_count'] = (
            pd.to_numeric(merged_star_power_df['vote_count'], errors='coerce', downcast='integer'))

        # sort by release date
        merged_star_power_df.dropna(subset=['release_date'], inplace=True)
        merged_star_power_df.sort_values(by='release_date', inplace=True)

        print(show_df_info(merged_star_power_df, "Sorted Film Contributions."))
        print(pretty_print_df(merged_star_power_df, rows=20))

        merged_star_power_df = process_genres(merged_star_power_df)

        # Add content advisory data.
        print(merged_star_power_df['imdb_id'].dtype)  # should be 'string' or 'object'
        print(imdb_movie_content_warning_df['IMDB ID'].dtype)  # should also be 'string'

        merged_star_power_df['imdb_id'] = merged_star_power_df['imdb_id'].astype(str).str.strip()
        imdb_movie_content_warning_df['IMDB ID'] = imdb_movie_content_warning_df['IMDB ID'].astype(str).str.strip()

        merged_ids = set(merged_star_power_df['imdb_id'].unique())
        warning_ids = set(imdb_movie_content_warning_df['IMDB ID'].unique())
        print("Matches:", len(merged_ids & warning_ids))
        print("In merged only:", len(merged_ids - warning_ids))
        print("In warning only:", len(warning_ids - merged_ids))

        merged_star_power_with_content_df = merge_content_warnings(merged_star_power_df, imdb_movie_content_warning_df)
        print(show_df_info(merged_star_power_with_content_df, "Sorted Film Contributions."))
        print(pretty_print_df(merged_star_power_with_content_df, rows=20))
        # test_value = merged_star_power_with_content_df.query("imdb_id == 'tt0120053'")[[
        #     'title', 'sex_factor', 'violence_factor', 'profanity_factor'
        # ]]
        #
        # print(test_value) Works!

        # Booleans for home page and collection.
        merged_star_power_with_content_df['has_collection'] = merged_star_power_with_content_df[
                                                                  'belongs_to_collection'].notna() & (
                                                                      merged_star_power_with_content_df[
                                                                          'belongs_to_collection'].str.strip() != '')
        merged_star_power_with_content_df['has_homepage'] = merged_star_power_with_content_df['homepage'].notna() & (
                merged_star_power_with_content_df['homepage'].str.strip() != '')

        # Shift columns to store previous performance.
        # Define the relevant columns for "sp" calculation
        columns_to_shift = [
            'weight',
            'vote_count',
            'vote_average',
            'budget_adj',
            'revenue_adj'
        ]

        # adjust budget and revenue for cpi. (creates _adj fields)
        merged_star_power_with_content_df = adjust_for_inflation(merged_star_power_with_content_df)
        merged_star_power_with_content_df.to_csv(MERGED_STAR_POWER_INTERMEDIATE_FILE, index=False)

        # Generate previous sp contributions for individuals (cast/crew)
        film_sp_df = shift_columns_by_person(merged_star_power_with_content_df, columns_to_shift, num_previous=3)

        # Step 2: Calculate prev sp based on shifted values
        film_sp_df = calculate_prev_sp(film_sp_df, num_previous=3)

        # Fill missing prev columns with weighted average (using both mean and global average)
        fill_cols = (['prev_1_sp', 'prev_2_sp', 'prev_3_sp'])
        film_sp_df = smart_fill(film_sp_df, fill_cols)

        # compute aggregates
        film_sp_df['mean_prev_budget'] = (
            film_sp_df[['prev_1_budget_adj', 'prev_2_budget_adj', 'prev_3_budget_adj']].mean(axis=1))
        film_sp_df['mean_prev_revenue'] = (
            film_sp_df[['prev_1_revenue_adj', 'prev_2_revenue_adj', 'prev_3_revenue_adj']].mean(axis=1))
        film_sp_df['sum_prev_revenue'] = (
            film_sp_df[['prev_1_revenue_adj', 'prev_2_revenue_adj', 'prev_3_revenue_adj']].sum(axis=1))

        # Compute current sp and prior sp sum
        film_sp_df['weight'] = pd.to_numeric(film_sp_df['weight'], errors='coerce', downcast='float')
        film_sp_df['sp_sum_previous'] = film_sp_df[['prev_1_sp', 'prev_2_sp', 'prev_3_sp']].sum(axis=1)

        # print(show_df_info(film_sp_df, "before dropping duplicates"))
        film_sp_df = (
            film_sp_df
            .sort_values(['vote_count', 'popularity'], ascending=False)
            .drop_duplicates(subset=['tmdb_id', 'person_id'], keep='first')
        )

        print(show_df_info(film_sp_df, "after dropping duplicates"))

        # Sometimes a role is missing so the weight may not add to 6.
        # There are also a few movies with weights above 6, which might be data entry issues.
        # Normalize the data.
        #
        # Compute normalization factor per film
        total_weights = film_sp_df.groupby('tmdb_id')['weight'].transform('sum')
        film_sp_df['weight'] *= (6.0 / total_weights.replace(0, 1e-6))  # prevent divide by zero

        # Now that weight is correct, calculate target film's sp.
        film_sp_df['sp'] = calculate_sp(film_sp_df)
        # Normalize column too for all contributors for film.
        film_sp_df['sp_sum_previous_mean'] = film_sp_df.groupby('tmdb_id')['sp_sum_previous'].transform('mean')
        # Normalize weight sum
        total_weights = film_sp_df.groupby('tmdb_id')['weight'].transform('sum')
        film_sp_df['total_weight'] = total_weights * (6.0 / total_weights.replace(0, 1e-6))  # prevent divide by zero

        # Use log of vote count to dampen effect of stuffing.
        film_sp_df['log_vote_count'] = np.log1p(film_sp_df['vote_count'])

        # Omit rows without all required fields.
        financial_film_sp_df = film_sp_df[
            (film_sp_df['budget_adj'] >= 5_000_000) &
            (film_sp_df['revenue_adj'] >= 5_000_000)
            ].copy()

        financial_film_sp_df.dropna(subset=['budget_adj', 'revenue_adj', 'vote_average', 'vote_count', 'weight'],
                                    inplace=True)

        financial_film_sp_df['mean_prev_budget'] = (
            financial_film_sp_df[['prev_1_budget_adj', 'prev_2_budget_adj', 'prev_3_budget_adj']].mean(axis=1))
        financial_film_sp_df['mean_prev_revenue'] = (
            financial_film_sp_df[['prev_1_revenue_adj', 'prev_2_revenue_adj', 'prev_3_revenue_adj']].mean(axis=1))
        financial_film_sp_df['sum_prev_revenue'] = (
            financial_film_sp_df[['prev_1_revenue_adj', 'prev_2_revenue_adj', 'prev_3_revenue_adj']].sum(axis=1))

        financial_film_sp_df['mean_prev_budget_mean'] = (
            financial_film_sp_df.groupby('tmdb_id')['mean_prev_budget'].transform('mean'))
        financial_film_sp_df['mean_prev_revenue_mean'] = (
            financial_film_sp_df.groupby('tmdb_id')['mean_prev_revenue'].transform('mean'))
        financial_film_sp_df['sum_prev_revenue_mean'] = (
            financial_film_sp_df.groupby('tmdb_id')['sum_prev_revenue'].transform('mean'))

        # Calculate ratios.
        financial_film_sp_df['rev_to_budget_ratio'] = (
                financial_film_sp_df['mean_prev_revenue_mean'] / (financial_film_sp_df['mean_prev_budget_mean'] + 1e-6))
        financial_film_sp_df['rev_per_prev_sp'] = (
                financial_film_sp_df['mean_prev_revenue_mean'] / (financial_film_sp_df['sp_sum_previous_mean'] + 1e-6))
        financial_film_sp_df['log_vote_count'] = np.log1p(financial_film_sp_df['vote_count'])

        # Save data before modeling. (so step can be jumped)
        film_sp_df.to_csv(os.path.join(DATA_DIRECTORY, "film_sp.csv"), index=False)
        print(show_df_info(film_sp_df, "All Film Contributor Data"))

        financial_film_sp_df.to_csv(os.path.join(DATA_DIRECTORY, "financial_film_sp.csv"), index=False)
        print(show_df_info(financial_film_sp_df, "Filtered for Financial Details - Film Contributor Data"))

        # Group by film
        film_grouped_df = group_by_film(film_sp_df)
        financial_film_grouped_df = group_by_film(financial_film_sp_df)
        print(show_df_info(financial_film_grouped_df, "Financial Film Grouped"))

        # add titles
        # Keep only the title and tmdb_id from metadata
        # Ensure 'tmdb_id' exists in both dataframes as string
        film_grouped_df['tmdb_id'] = film_grouped_df['tmdb_id'].astype(str)
        financial_film_grouped_df['tmdb_id'] = financial_film_grouped_df['tmdb_id'].astype(str)

        # Data to merge from tmdb film database file
        film_metadata_subset = film_sp_df[[
            'tmdb_id', 'imdb_id', 'title', 'release_date',
            'has_collection', 'has_homepage',
            'Sex - Report Count', 'Violence - Report Count', 'Profanity - Report Count',
            'Drugs - Report Count', 'Intense - Report Count',
            'Action', 'Adventure',
            'Animation', 'Comedy',
            'Crime', 'Documentary',
            'Drama', 'Family',
            'Fantasy', 'Foreign',
            'History', 'Horror',
            'Music', 'Mystery',
            'Romance', 'Science Fiction',
            'TV Movie', 'Thriller',
            'War', 'Western',
            'release_year', 'release_month',
            'budget_adj', 'revenue_adj',
            'vote_average', 'vote_count',
            'popularity', 'total_weight',
            'log_vote_count'
        ]]

        financial_metadata_subset = financial_film_sp_df[[
            'tmdb_id', 'imdb_id', 'title', 'release_date',
            'has_collection', 'has_homepage',
            'Sex - Report Count', 'Violence - Report Count', 'Profanity - Report Count',
            'Drugs - Report Count', 'Intense - Report Count',
            'Action', 'Adventure',
            'Animation', 'Comedy',
            'Crime', 'Documentary',
            'Drama', 'Family',
            'Fantasy', 'Foreign',
            'History', 'Horror',
            'Music', 'Mystery',
            'Romance', 'Science Fiction',
            'TV Movie', 'Thriller',
            'War', 'Western',
            'release_year', 'release_month',
            'budget_adj',
            'revenue_adj', 'vote_average', 'vote_count',
            'popularity', 'sp_sum_previous_mean',
            'rev_to_budget_ratio', 'rev_per_prev_sp',
            'sum_prev_revenue_mean', 'mean_prev_revenue_mean',
            'mean_prev_budget_mean', 'total_weight',
            'log_vote_count'
        ]]

        # Merge title info with grouped film data
        film_grouped_with_titles_df = film_grouped_df.merge(
            film_metadata_subset,
            on='tmdb_id',
            how='left',
            suffixes=('', '_duplicate')
        ).drop_duplicates(subset='tmdb_id', keep='first')

        film_grouped_with_titles_df['weight'] = (
            (film_grouped_with_titles_df['total_weight'] * 6.0 / film_grouped_with_titles_df['total_weight']))

        film_grouped_with_titles_df.to_csv(os.path.join(DATA_DIRECTORY, "film_grouped_with_titles.csv"), index=False)
        # Merge title info with grouped film data
        financial_grouped_with_titles_df = financial_film_grouped_df.merge(
            financial_metadata_subset,
            on='tmdb_id',
            how='left',
            suffixes=('', '_duplicate')
        ).drop_duplicates(subset='tmdb_id', keep='first')

        financial_grouped_with_titles_df['weight'] = \
            (financial_grouped_with_titles_df['total_weight'] * 6.0 / financial_grouped_with_titles_df['total_weight'])
        financial_grouped_with_titles_df.to_csv(os.path.join(DATA_DIRECTORY,
                                                             "financial_film_grouped_with_titles.csv"), index=False)
    else:
        film_sp_df = pd.read_csv(os.path.join(DATA_DIRECTORY, "film_sp.csv"))
        film_grouped_with_titles_df = pd.read_csv(os.path.join(DATA_DIRECTORY, "film_grouped_with_titles.csv"))
        financial_film_sp_df = pd.read_csv(os.path.join(DATA_DIRECTORY, "financial_film_sp.csv"))
        financial_grouped_with_titles_df = pd.read_csv(os.path.join(DATA_DIRECTORY,
                                                                    "financial_film_grouped_with_titles.csv"))
        print("Starting with temporary cached files.")

    print(show_df_info(financial_grouped_with_titles_df, "Subset of Films with Financial Data"))

    top_with_titles_df = film_grouped_with_titles_df.sort_values(by='sp', ascending=False)
    top_with_titles_df = top_with_titles_df.drop_duplicates(subset='tmdb_id')
    top_financial_with_titles_df = financial_grouped_with_titles_df.sort_values(by='sp', ascending=False)
    top_financial_with_titles_df = top_financial_with_titles_df.drop_duplicates(subset='tmdb_id')

    top_financial_with_titles_df['profit'] = (
            top_financial_with_titles_df['revenue_adj'] - top_financial_with_titles_df['budget_adj'])

    interesting_columns = \
        ['tmdb_id', 'title', 'release_date', 'budget_adj', 'revenue_adj', 'vote_count', 'vote_average',
         'weight', 'log_vote_count', 'sp']
    currency_columns = ['budget_adj', 'revenue_adj']
    rounded_columns = ['vote_average', 'sp']

    # preview data
    print(pretty_print_df(top_with_titles_df, rows=20, interesting_columns=interesting_columns,
                          currency_cols=currency_columns, rounded_cols=rounded_columns))

    # anything without a home page is removed.
    top_with_titles_df = top_with_titles_df[top_with_titles_df['has_homepage'] == True]

    # take out bad records (metropolis is in DM not dollars)
    top_financial_with_titles_df = top_financial_with_titles_df[top_financial_with_titles_df['budget_adj'] < 1000000000]

    top_with_titles_df['sp_sum_previous_squared'] = top_with_titles_df['sp_sum_previous'] ** 2
    top_financial_with_titles_df['sp_sum_previous_squared'] = top_financial_with_titles_df['sp_sum_previous'] ** 2
    top_with_titles_df['sp_squared'] = top_with_titles_df['sp'] ** 2
    top_financial_with_titles_df['sp_squared'] = top_financial_with_titles_df['sp'] ** 2

    top_with_titles_df['log_sp_sum_previous'] = np.log1p(top_with_titles_df['sp_sum_previous'])
    top_with_titles_df['log_sp'] = np.log1p(top_with_titles_df['sp'])
    top_with_titles_df['inv_sp_sum_previous'] = 1 / (top_with_titles_df['sp_sum_previous'] + 1)
    top_with_titles_df['sqrt_sp_sum_previous'] = np.sqrt(top_with_titles_df['sp_sum_previous'])
    top_with_titles_df['sp_sum_prev_bin'] = pd.cut(top_with_titles_df['sp_sum_previous'],
                                                   bins=[0, 100, 300, 600, 1000, np.inf],
                                                   labels=['Low', 'Med-Low', 'Med', 'High', 'Extreme'])
    top_financial_with_titles_df['log_sp_sum_previous'] = np.log1p(top_financial_with_titles_df['sp_sum_previous'])
    top_financial_with_titles_df['log_sp'] = np.log1p(top_financial_with_titles_df['sp'])
    top_financial_with_titles_df['inv_sp_sum_previous'] = 1 / (top_financial_with_titles_df['sp_sum_previous'] + 1)
    top_financial_with_titles_df['sqrt_sp_sum_previous'] = np.sqrt(top_financial_with_titles_df['sp_sum_previous'])

    # # Change target to log.
    # budget_adj	= size of the project
    # log_budget_adj  =	scaled version of budget
    # sp_sum_previous	= cast/crew star power
    # sum_prev_revenue	= total revenue history of cast/crew
    # mean_prev_revenue	 = avg past revenue of cast/crew
    # mean_prev_budget	= avg past budget of cast/crew
    # (maybe release year)	= seasonality effect — optional

    financial_grouped_with_titles_df['log_budget_adj'] = np.log1p(financial_grouped_with_titles_df['budget_adj'])
    financial_grouped_with_titles_df['log_revenue_adj'] = np.log1p(financial_grouped_with_titles_df['revenue_adj'])

    financial_grouped_with_titles_df['log_sum_prev_revenue_mean'] = np.log1p(
        financial_grouped_with_titles_df['sum_prev_revenue_mean'])
    financial_grouped_with_titles_df['log_mean_prev_revenue_mean'] = np.log1p(
        financial_grouped_with_titles_df['mean_prev_revenue_mean'])
    financial_grouped_with_titles_df['log_mean_prev_budget_mean'] = np.log1p(
        financial_grouped_with_titles_df['mean_prev_budget_mean'])

    financial_grouped_with_titles_df['profit'] = (
            financial_grouped_with_titles_df['revenue_adj'] - financial_grouped_with_titles_df['budget_adj'])

    financial_grouped_with_titles_df['is_profitable'] = \
        (financial_grouped_with_titles_df['revenue_adj'] > (2 * financial_grouped_with_titles_df['budget_adj']))

    financial_grouped_with_titles_df.dropna(subset=general_modeling_columns, inplace=True)
    financial_grouped_with_titles_df.to_csv(os.path.join(DATA_DIRECTORY, "data_to_model.csv"), index=False)

    return (film_sp_df, financial_film_sp_df, film_grouped_with_titles_df, financial_grouped_with_titles_df,
            top_with_titles_df, top_financial_with_titles_df)


def perform_revenue_regressions(df, add_collection = False):
    # do model regressions for these options.
    feature_importances_df, y_actual, y_pred = (
        model_regressions(df, general_modeling_columns, 'log_revenue_adj'))
    # show pictures.
    regression_visualisations(df, y_actual, y_pred)
    print(pretty_print_df(feature_importances_df))

    base_cols = [
        'log_budget_adj', 'sp_sum_previous_mean',
        'log_sum_prev_revenue_mean', 'log_mean_prev_revenue_mean',
        'log_mean_prev_budget_mean', 'rev_to_budget_ratio',
        'rev_per_prev_sp', 'release_year'
    ]
    genre_cols = [col for col in df.columns if col in found_genres]

    # adding has_collection is like a cheat code for the models (likely overfitting!)
    if add_collection:
        base_cols.append('has_collection')

    general_modeling_columns_with_content_and_genre = base_cols + content_modeling_cols + genre_cols
    extended_model_data_df = df.copy()

    extended_model_data_df.dropna(subset=general_modeling_columns_with_content_and_genre, inplace=True
                                  )
    # do model regressions for these options.
    extended_feature_importances_df, extended_y_actual, extended_y_pred = (
        model_regressions(extended_model_data_df, general_modeling_columns_with_content_and_genre, 'log_revenue_adj'))
    # show pictures.
    regression_visualisations(extended_model_data_df, extended_y_actual, extended_y_pred)
    print(pretty_print_df(extended_feature_importances_df))


def produce_failure_report(df):
    # determine film revenue = budget
    df['profit'] = df['revenue_adj'] - df['budget_adj']
    df = df.sort_values(['profit'], ascending=False)

    df['is_profitable'] = df['revenue_adj'] > (2 * df['budget_adj'])

    interesting_columns = \
        ['tmdb_id', 'title', 'release_date', 'budget_adj', 'revenue_adj', 'profit', 'sp']
    currency_columns = ['budget_adj', 'revenue_adj', 'profit']
    rounded_columns = ['sp']

    print("Most profitable films - adjusted for Release Year and CPI")
    print(pretty_print_df(df.head(10), interesting_columns=interesting_columns,
                          currency_cols=currency_columns, rounded_cols=rounded_columns))
    print("Least profitable films - adjusted for Release Year and CPI")
    print(pretty_print_df(df.tail(10), interesting_columns=interesting_columns,
                          currency_cols=currency_columns, rounded_cols=rounded_columns))


def force_starpower_rebuild():
    (film_sp_df, financial_film_sp_df, film_grouped_with_titles_df, financial_grouped_with_titles_df,
        top_with_titles_df, top_financial_with_titles_df) =  build_star_power(True, False)
    do_all_starpower_correlation_transformations(top_with_titles_df, top_financial_with_titles_df)
    perform_revenue_regressions(financial_grouped_with_titles_df)
    produce_failure_report(top_financial_with_titles_df)


def starpower_main():
    (film_sp_df, financial_film_sp_df, film_grouped_with_titles_df, financial_grouped_with_titles_df,
        top_with_titles_df, top_financial_with_titles_df) =  build_star_power(False, False)
    do_all_starpower_correlation_transformations(top_with_titles_df, top_financial_with_titles_df)
    perform_revenue_regressions(financial_grouped_with_titles_df)
    produce_failure_report(top_financial_with_titles_df)


if __name__ == '__main__':

    print("Current directory:", os.getcwd())
    force_starpower_rebuild()







