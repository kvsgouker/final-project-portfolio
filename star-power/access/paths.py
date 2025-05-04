"""
Project Name: Star Power
File: paths.py
Purpose: Defines directory paths, constants, and remote URLs used across the film and TV ratings analysis project.
Ensures proper directory structure and centralizes access to key data locations and Google Drive resources.

Author: Kyle Salgado-Gouker

"""

import os

# --- Utility Functions ---

def ensure_directories_exist(dirs):
    """
    Ensures that all specified directories exist. Creates any that are missing.

    Args:
        dirs (list of str): List of directory paths to verify/create.
    """
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Directory '{d}' created.")

def get_google_drive_download_link(share_link_url):
    """
    Converts a Google Drive share link into a direct download URL.

    Args:
        share_link_url (str): Google Drive share link.

    Returns:
        str: Direct download link for the file.
    """
    file_id = share_link_url.split("/d/")[1].split("/")[0]
    return f"https://drive.google.com/uc?id={file_id}&export=download"

# --- Base Directories ---

DATA_DIRECTORY = "data"
RATINGS_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "ratings")
RATING_SHEETS_DATA_DIRECTORY = os.path.join(RATINGS_DATA_DIRECTORY, "downloads")
SVOD_SHEETS_DATA_DIRECTORY = os.path.join(RATINGS_DATA_DIRECTORY, "svod")
SVOD_GOOGLEDOC_DATA_DIRECTORY = os.path.join(SVOD_SHEETS_DATA_DIRECTORY, "google")
SVOD_DAYS_DATA_DIRECTORY = os.path.join(SVOD_GOOGLEDOC_DATA_DIRECTORY, "days")
SVOD_PROGRAM_DATA_DIRECTORY = os.path.join(SVOD_GOOGLEDOC_DATA_DIRECTORY, "programs")
MOVIE_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "movies")
MOVIE_BRANDS_DATA_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "brands")
MOVIE_FRANCHISES_DATA_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "franchises")
MOVIE_HTML_SAMPLE_DATA_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "html_sample")
MOVIE_HTML_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "html")
MOVIE_CONTENT_HTML_DIRECTORY = os.path.join(MOVIE_HTML_DIRECTORY, "content")
MOVIE_YEARS_DATA_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "years")
MOVIE_AUDIENCE_DATA_DIRECTORY = os.path.join(MOVIE_DATA_DIRECTORY, "audience")
MOVIE_AUDIENCE_DAILY_DATA_DIRECTORY = os.path.join(MOVIE_AUDIENCE_DATA_DIRECTORY, "daily")
TRENDS_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "trends")
CONTENT_DATA_DIRECTORY = os.path.join(DATA_DIRECTORY, "content")
TV_SERIES_PAGE_DIRECTORY = os.path.join(RATINGS_DATA_DIRECTORY, "series")
FILM_INFORMATION_DIRECTORY = os.path.join(DATA_DIRECTORY, "film info")
LOG_DIRECTORY = os.path.join(DATA_DIRECTORY, "log/")

ALL_DIRECTORIES = [
    DATA_DIRECTORY,
    RATINGS_DATA_DIRECTORY,
    RATING_SHEETS_DATA_DIRECTORY,
    SVOD_SHEETS_DATA_DIRECTORY,
    SVOD_GOOGLEDOC_DATA_DIRECTORY,
    SVOD_DAYS_DATA_DIRECTORY,
    SVOD_PROGRAM_DATA_DIRECTORY,
    MOVIE_DATA_DIRECTORY,
    MOVIE_BRANDS_DATA_DIRECTORY,
    MOVIE_FRANCHISES_DATA_DIRECTORY,
    MOVIE_HTML_SAMPLE_DATA_DIRECTORY,
    MOVIE_YEARS_DATA_DIRECTORY,
    MOVIE_HTML_DIRECTORY,
    MOVIE_CONTENT_HTML_DIRECTORY,
    MOVIE_AUDIENCE_DATA_DIRECTORY,
    MOVIE_AUDIENCE_DAILY_DATA_DIRECTORY,
    TRENDS_DATA_DIRECTORY,
    CONTENT_DATA_DIRECTORY,
    TV_SERIES_PAGE_DIRECTORY,
    LOG_DIRECTORY
]

# --- Local Files ---

CREDITS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "credits.csv")
KEYWORDS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "keywords.csv")
LINKS_SMALL_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "links_small.csv")
LINKS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "links.csv")
MOVIES_METADATA_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "movies_metadata.csv")
RATINGS_SMALL_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "ratings_small.csv")
RATINGS_FILE = os.path.join(FILM_INFORMATION_DIRECTORY, "ratings.csv")

RATINGS_LINK_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "sheet.html")
GOOGLEDOC_LINK_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "jump_table.html")

NIELSEN_RATINGS_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "tv_ratings2.csv")
SVOD_MEASURE_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "svod_ratings2.csv")
ARCHIVE_RATINGS_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "programs_ratings.csv")
TMDB_SERIES_MAIN_FILE_V3 = os.path.join(RATINGS_DATA_DIRECTORY, "TMDB_tv_dataset_v3.csv")
TMDB_FILMS_MAIN_FILE_V11 = os.path.join(MOVIE_DATA_DIRECTORY, "TMDB_movie_dataset_v11.csv")
VALID_ID_TMDB_SERIES_MAIN_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "TMDB_tv_valid_id_dataset.csv")
MERGED_EPISODE_DATA_FILE = os.path.join(DATA_DIRECTORY, "merged_episode_data.csv")
SERIES_RUNS_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "tv_series_runs.csv")
PRE_WEBSCRAPING_GOOGLE_DOCS_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "tv_shows2.csv")
POST_WEBSCRAPING_GOOGLE_DOCS_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "tv_shows3.csv")
COMPLETE_SERIES_LIST_FILE = os.path.join(DATA_DIRECTORY, "main_series_list.csv")
TV_SERIES_WITH_NETWORK_AND_GENRES_FILE = os.path.join(DATA_DIRECTORY, "tv_shows_main_with_network_and_genres.csv")

# --- Downloadable Data URLs ---

FILTERED_MAIN_SERIES_FOR_MODELING_URL = get_google_drive_download_link("https://drive.google.com/file/d/1v-OxsXmmt7CXOxOy6owP4ch8r3bo3PcL/view?usp=drive_link")
UNFILTERED_MAIN_SERIES_FOR_MODELING_URL = get_google_drive_download_link("https://drive.google.com/file/d/1i6jTpfRFk6mFVVCsyIINkOrDkVmZF5Fu/view?usp=drive_link")
SVOD_DATA_FOR_MODELING_URL = get_google_drive_download_link("https://drive.google.com/file/d/12A3OS5e8Lvi2m_LwsvC2ceJiZxdtpVl3/view?usp=drive_link")
EPISODE_NIELSEN_FOR_MODELING_URL = get_google_drive_download_link("https://drive.google.com/file/d/15b95elx37t8Toq0lGgme4z9ScyN9cIQ5/view?usp=drive_link")
EPISODES_FOR_MODELING_URL = get_google_drive_download_link("https://drive.google.com/file/d/14eGdTdg-1Mab7jeOKRDC5DF7khtctep-/view?usp=drive_link")

# --- Box Office Mojo Links ---

BOX_OFFICE_MOJO_YEAR_URL = "https://www.boxofficemojo.com/year/{year}/?grossesOption=calendarGrosses"
BOX_OFFICE_MOJO_PAGE = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_BASE_URL = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_RELEASE_PREFIX = "/release/"

# --- Modeling Dataset File Paths ---

FILTERED_MAIN_SERIES_FOR_MODELING_DATA_FILE = os.path.join(DATA_DIRECTORY, "tv_shows_main_with_networks_and_genres.csv")
UNFILTERED_MAIN_SERIES_FOR_MODELING_DATA_FILE = os.path.join(DATA_DIRECTORY, "tv_shows_main.csv")
SVOD_DATA_FOR_MODELING_DATA_FILE = os.path.join(DATA_DIRECTORY, "svod_merged_data.csv")
EPISODE_NIELSEN_FOR_MODELING_DATA_FILE = os.path.join(DATA_DIRECTORY, "episode_nielsen_data.csv")
EPISODES_FOR_MODELING_DATA_FILE = os.path.join(DATA_DIRECTORY, "episode_data_with_imdb_ratings_too.csv")

# --- Intermediate Data Sources (Google Drive URLs) ---

SERIES_RATINGS_JUMP_TABLE_URL = get_google_drive_download_link("https://drive.google.com/file/d/10DkAK9Opsz6HAtAjKSjukDXZHSLZeBzU/view?usp=drive_link")
NIELSEN_RATINGS_URL = get_google_drive_download_link("https://drive.google.com/file/d/1-I9L16_g4E4PCQb8CkKjRRVj5DiL_dU-/view?usp=drive_link")
SVOD_MEASURE_URL = get_google_drive_download_link("https://drive.google.com/file/d/1f065k2utd192T3GlNDRVj_3UZWCpF_DQ/view?usp=drive_link")
ARCHIVE_RATINGS_URL = get_google_drive_download_link("https://drive.google.com/file/d/1zOkFGeqnhgTiAmmHHTB6JmXkwCrzi34w/view?usp=drive_link")
ORIGINAL_TMDB_DATASET_URL = get_google_drive_download_link("https://drive.google.com/file/d/1huMGSMBefrcBOyG5jS1NWdjRTaI5eKYX/view?usp=drive_link")
VALID_ID_TMDB_SERIES_MAIN_URL = get_google_drive_download_link("https://drive.google.com/file/d/1R9MgE3cE7_9Oh45rWuL98TUoFn6UmAi5/view?usp=drive_link")
MERGED_EPISODE_DATA_URL = get_google_drive_download_link("https://drive.google.com/file/d/1Vx-FC_YQEHfokFB6eJ9-dOaYNdHSS8DK/view?usp=drive_link")
SERIES_RUNS_URL = get_google_drive_download_link("https://drive.google.com/file/d/1QkINkVV03m5xBVeNeLguad-YpT-XSBaA/view?usp=drive_link")
PRE_WEBSCRAPING_GOOGLE_DOCS_URL = get_google_drive_download_link("https://drive.google.com/file/d/1Z2HZ6Le-mKzv-awK9a-ro694reXCwO-r/view?usp=drive_link")
POST_WEBSCRAPING_GOOGLE_DOCS_URL = get_google_drive_download_link("https://drive.google.com/file/d/1SG3hHfcKGx_NUN1_3y24iWnUpbkGoieY/view?usp=drive_link")
COMPLETE_SERIES_LIST_URL = get_google_drive_download_link("https://drive.google.com/file/d/1g-U4f0U3R2GjVToUJy3ZT6jKC_tHBZ-o/view?usp=drive_link")
TV_SERIES_WITH_NETWORK_AND_GENRES_URL = get_google_drive_download_link("https://drive.google.com/file/d/1Hv2b6obxPLtch9fbBdTrVmADxVnO3T82/view?usp=drive_link")

# --- Star Power Alt

TMDB_MOVIES_METADATA_FILE = os.path.join(DATA_DIRECTORY, "TMDB_movie_dataset_v11.csv")

# --- Star Power

IMDB_MOVIE_METADATA_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_metadata.csv")
IMDB_MOVIE_CONTENT_WARNING_FILE = os.path.join(DATA_DIRECTORY, "all_imdb_movie_content_warnings.csv")
STAR_POWER_DATA_FILE = os.path.join(DATA_DIRECTORY, "star_power.csv")
MERGED_STAR_POWER_INTERMEDIATE_FILE = os.path.join(DATA_DIRECTORY, "merged_star_power.csv")


if __name__ == '__main__':
    ensure_directories_exist(ALL_DIRECTORIES)
