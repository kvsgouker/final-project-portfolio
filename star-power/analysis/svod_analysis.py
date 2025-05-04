"""
Project Name: Star Power
File: svod_analysis.py

Processes and cleans SVOD streaming data.
Integrates TMDB API results and enriches SVOD entries with genre, language, and network info.


Author: Kyle Salgado-Gouker

"""

import pandas as pd

from access.paths import SVOD_MEASURE_FILE, DATA_DIRECTORY
from analysis.genres import tmdb_genre_encoding
from config.settings import SKIP_TO_MODELING, CREATE_MISSING_SERIES_DATAFRAME
from utils.utilities import show_df_info

from tmdbv3api import TMDb, Movie, TV, Search


def create_missing_series_dataframe(results_to_test):
    ids = []
    titles = []
    number_of_seasons_list = []
    number_of_episodes_list = []
    original_languages = []
    vote_counts = []
    vote_averages = []
    overviews = []
    adults = []
    backdrop_paths = []
    first_air_dates = []
    last_air_dates = []
    homepages = []
    in_productions = []
    original_names = []
    popularitys = []
    poster_paths = []
    types = []
    status_list = []
    taglines = []
    genres_list = []
    created_bys = []
    languages_list = []
    networks_list = []
    origin_countrys = []
    spoken_languages_list = []
    production_companies_list = []
    production_countries_list = []
    episode_run_times = []

    for tmdb_result in results_to_test:
        title, tmdb_id, detailed_info = tmdb_result

        ids.append(tmdb_id)
        titles.append(title)

        # Extract data from detailed_info, ensuring to handle missing data and data types appropriately
        number_of_seasons_list.append(detailed_info.get('number_of_seasons', None))
        number_of_episodes_list.append(detailed_info.get('number_of_episodes', None))
        original_languages.append(detailed_info.get('original_language', None))
        vote_counts.append(detailed_info.get('vote_count', None))
        vote_averages.append(detailed_info.get('vote_average', None))
        overviews.append(detailed_info.get('overview', None))
        adults.append(detailed_info.get('adult', None))
        backdrop_paths.append(detailed_info.get('backdrop_path', None))
        first_air_dates.append(detailed_info.get('first_air_date', None))
        last_air_dates.append(detailed_info.get('last_air_date', None))
        homepages.append(detailed_info.get('homepage', None))
        in_productions.append(detailed_info.get('in_production', None))
        original_names.append(detailed_info.get('original_name', None))
        popularitys.append(detailed_info.get('popularity', None))
        poster_paths.append(detailed_info.get('poster_path', None))
        types.append(detailed_info.get('type', None))  # May need correction based on actual JSON key
        status_list.append(detailed_info.get('status', None))
        taglines.append(detailed_info.get('tagline', None))

        # Join genres into a comma-separated string
        genres_list.append(", ".join([genre['name'] for genre in detailed_info.get('genres', [])]))

        # Join creators into a comma-separated string
        created_bys.append(", ".join([creator['name'] for creator in detailed_info.get('created_by', [])]))

        # Join languages into a comma-separated string
        languages_list.append(", ".join(detailed_info.get('languages', [])))

        # Join networks into a comma-separated string
        networks_list.append(", ".join([network['name'] for network in detailed_info.get('networks', [])]))

        # Join origin countries into a comma-separated string
        origin_countrys.append(", ".join(detailed_info.get('origin_country', [])))

        # Join spoken languages into a comma-separated string
        spoken_languages_list.append(
            ", ".join([lang['english_name'] for lang in detailed_info.get('spoken_languages', [])]))

        # Join production companies into a comma-separated string
        production_companies_list.append(
            ", ".join([company['name'] for company in detailed_info.get('production_companies', [])]))

        # Join production countries into a comma-separated string
        production_countries_list.append(
            ", ".join([country['name'] for country in detailed_info.get('production_countries', [])]))

        episode_run_times.append(detailed_info.get('episode_run_time', None))

    column_names = ["ids", "titles", "number_of_seasons_list", "number_of_episodes_list", "original_languages",
                    "vote_counts", "vote_averages", "overviews", "adults", "backdrop_paths", "first_air_dates",
                    "last_air_dates", "homepages", "in_productions", "original_names", "popularitys",
                    "poster_paths",
                    "types", "status_list", "taglines", "genres_list", "created_bys", "languages_list",
                    "networks_list",
                    "origin_countrys", "spoken_languages_list", "production_companies_list",
                    "production_countries_list",
                    "episode_run_times"]

    data_lists = [ids, titles, number_of_seasons_list, number_of_episodes_list, original_languages, vote_counts,
                  vote_averages, overviews, adults, backdrop_paths, first_air_dates, last_air_dates, homepages,
                  in_productions, original_names, popularitys, poster_paths, types, status_list, taglines,
                  genres_list, created_bys, languages_list, networks_list, origin_countrys, spoken_languages_list,
                  production_companies_list, production_countries_list, episode_run_times]

    # Print the length of each list to see if they all have the same number of elements
    for name, data_list in zip(column_names, data_lists):
        print(f"Length of {name}: {len(data_list)}")

    # Combine all the data into a DataFrame
    series_data = {
        "id": ids,
        "Title": titles,
        "number_of_seasons": number_of_seasons_list,
        "number_of_episodes": number_of_episodes_list,
        "original_language": original_languages,
        "vote_count": vote_counts,
        "vote_average": vote_averages,
        "overview": overviews,
        "adult": adults,
        "backdrop_path": backdrop_paths,
        "first_air_date": first_air_dates,
        "last_air_date": last_air_dates,
        "homepage": homepages,
        "in_production": in_productions,
        "original_name": original_names,
        "popularity": popularitys,
        "poster_path": poster_paths,
        "type": types,
        "status": status_list,
        "tagline": taglines,
        "genres": genres_list,
        "created_by": created_bys,
        "languages": languages_list,
        "networks": networks_list,
        "origin_country": origin_countrys,
        "spoken_languages": spoken_languages_list,
        "production_companies": production_companies_list,
        "production_countries": production_countries_list,
        "episode_run_time": episode_run_times
    }

    return pd.DataFrame(series_data)


def create_all_missing_series(tmdb_results, possible_results):
    if not SKIP_TO_MODELING:

        CREATE_MISSING_SERIES_DATAFRAME = False

        if CREATE_MISSING_SERIES_DATAFRAME:
            streaming_series_df = create_missing_series_dataframe(tmdb_results)
            possible_series_df = create_missing_series_dataframe(possible_results)

            streaming_series_df.to_csv(DATA_DIRECTORY + "/missing_series_complete.csv", index=False)
            possible_series_df.to_csv(DATA_DIRECTORY + "/possible_series_complete.csv", index=False)
        else:
            streaming_series_df = pd.read_csv(DATA_DIRECTORY + "/missing_series_complete.csv")
            possible_series_df = pd.read_csv(DATA_DIRECTORY + "/possible_series_complete.csv")
    else:
        streaming_series_df = pd.read_csv(DATA_DIRECTORY + "/missing_series_complete.csv")
        possible_series_df = pd.read_csv(DATA_DIRECTORY + "/possible_series_complete.csv")

    return streaming_series_df, possible_series_df


def add_network_info_to_svod_results():

    svod_series_df = pd.read_csv(SVOD_MEASURE_FILE)

    show_df_info(svod_series_df, "SVOD Data")

    svod_series_df = svod_series_df.rename(columns={'Show': 'Title'})

    platforms_list = ['DISNEY+', 'HULU/DISNEY+', 'NETFLIX', 'AMAZON', 'APPLE TV+', 'MAX/NET', 'MAX',
     'HULU/NET', 'HULU', 'PEACOCK', 'PARAMOUNT+', 'PARA/NET', 'HULU/AMA', 'PEA/NET',
     'HULU/PARA+', 'HBO MAX', 'AMAZON/HULU', 'PEA/HULU', 'HULU/MAX', 'AMA/NET',
     'PARA/AMA', 'MAX/DISNEY+', 'NET/PARA+']

    network_replacement_list = ['Disney+', 'Hulu, Disney+', 'Netflix', 'Prime Video', 'Apple TV+', 'HBO Max, Netflix', 'HBO Max',
     'Hulu, Netflix', 'Hulu', 'Peacock', 'Paramount+', 'Paramount+, Netflix', 'Hulu, Prime Video', 'Peacock, Netflix',
     'Hulu, Paramount+', 'HBO Max', 'Prime Video, Hulu', 'Peacock, Hulu', 'Hulu, HBO Max', 'Prime Video, Netflix',
     'Paramount+, Prime Video', 'HBO Max, Disney+', 'Netflix, Paramount+']

    # Create boolean columns for each network
    # They are not quite the same so make a new field "Networks"
    # Create a mapping from platforms_list to network_replacement_list using zip.
    platform_to_network = dict(zip(platforms_list, network_replacement_list))

    # Map the 'Platform' column to the 'networks' column using the mapping
    svod_series_df['networks'] = svod_series_df['Platform'].map(platform_to_network)

    show_df_info(svod_series_df, "SVOD Data")
    return svod_series_df


def get_titles_to_check(svod_series_df):
    titles_to_check = svod_series_df['Title'].unique()
    return titles_to_check


def check_titles(titles_to_check):
    tmdb = TMDb()
    # need new api key and access token.
    tmdb.api_key = "de237f1a1a9211ebbbee2e4213faa265"
    tmdb_read_access_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJkZTIzN2YxYTFhOTIxMWViYmJlZTJlNDIxM2ZhYTI2NSIsInN1YiI6IjY2MWYzYzYwNmEzMDBiMDE3ZTMzMGJkNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.NcNdEoY5xb2PiF06DaelBjEblmOy-NTf7sPKz7BT6lU"

    search = Search()
    tv_details_fetcher = TV()
    movie_details_fetcher = Movie()

    # Initialize an empty list to store API results
    tmdb_results = []
    possible_results = []
    best_movie_results = []

    # Loop through each title
    for title in titles_to_check:

        print(f"Accessing TMDB records for {title}")
        # Use the TMDb API to search for the TV show by title
        matches_dict = search.tv_shows(title)

        # Extract the results list from the dictionary
        matches = matches_dict.get('results', [])

        if matches:
            save_page = None
            page_to_use = None
            series_vote_count = 0
            for page in matches:
                if 'vote_count' in page and isinstance(page['vote_count'], int):
                    test_vote_count = page['vote_count']
                    if page_to_use is None or test_vote_count > series_vote_count:
                        page_to_use = page
                        series_vote_count = test_vote_count

            # make sure it's not a film in disguise
            movie_matches = search.movies(title)
            movie_vote_count = 0
            movie_result_to_use = None
            for movie_match in movie_matches:
                if 'vote_count' in movie_match and isinstance(movie_match['vote_count'], int):
                    test_vote_count = movie_match['vote_count']
                    if test_vote_count > movie_vote_count:
                        movie_vote_count = test_vote_count
                        movie_result_to_use = movie_match

            # put in two lists (likely and improbable, which has frequent movie mismatches)
            if page_to_use and series_vote_count > movie_vote_count:
                print(f"processing tmdb page for {title}")
                detailed_info = tv_details_fetcher.details(page_to_use['id'])  # Fetch the detailed info using the ID
                # build a list of SVOD shows (includes movies and series)
                tmdb_results.append([title, page_to_use['id'], detailed_info])
            elif page_to_use:
                print(f"higher voted film for {title}")
                detailed_info = tv_details_fetcher.details(page_to_use['id'])  # Fetch the detailed info using the ID
                # build a list of SVOD shows (includes movies and series)
                possible_results.append([title, page_to_use['id'], detailed_info])
                # also build a list of films for later comparison.
                if movie_result_to_use:
                    detailed_info = movie_details_fetcher.details(movie_result_to_use['id'])
                    best_movie_results.append([title, movie_result_to_use['id'], detailed_info])

        else:
            # Log an error or handle the case where no matches are found
            print(f"No matches found for {title}")

    return tmdb_results, possible_results, best_movie_results


