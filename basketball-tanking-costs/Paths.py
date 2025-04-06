"""
paths.py

Defines directory paths and constants used across the NBA analysis project.
Ensures proper directory structure and provides reference to key data locations and URLs.
"""

import os

# Get current working directory
current_directory = os.getcwd()

# Base data directory
FILE_PATH_TO_DATA = "nba-data/"

# Directory for compiled outputs (CSV files, SQL database, etc.)
FILE_PATH_TO_COMPILED_DATA = FILE_PATH_TO_DATA

# Subdirectories for different types of data
FILE_PATH_TO_DRAFTS = os.path.join(FILE_PATH_TO_DATA, "drafts/draft-")
FILE_PATH_TO_GAMES_DATA = os.path.join(FILE_PATH_TO_DATA, "games/")
FILE_PATH_TO_HISTORY = os.path.join(FILE_PATH_TO_DATA, "history/")
FILE_PATH_TO_LOG = os.path.join(FILE_PATH_TO_DATA, "log/")
FILE_PATH_TO_PLAYER_SALARIES_HISTORY = os.path.join(FILE_PATH_TO_DATA, "player_salaries/")
FILE_PATH_TO_PLAYERS = os.path.join(FILE_PATH_TO_DATA, "players/")
FILE_PATH_TO_PLAYOFFS = os.path.join(FILE_PATH_TO_DATA, "playoffs/playoffs-")
FILE_PATH_TO_PLAYOFF_STATS = os.path.join(FILE_PATH_TO_DATA, "playoff_statistics/")
FILE_PATH_TO_PLOTS = os.path.join(FILE_PATH_TO_DATA, "plots/")
FILE_PATH_TO_SALARIES = os.path.join(FILE_PATH_TO_DATA, "salaries/")
FILE_PATH_TO_SEASONS = os.path.join(FILE_PATH_TO_DATA, "seasons/season-")
FILE_PATH_TO_STATS = os.path.join(FILE_PATH_TO_DATA, "statistics/")

# Reference URL
bbref_url = "https://www.basketball-reference.com/"


def create_directory_structure():
    """
    Creates all necessary data subdirectories if they do not already exist.

    This function ensures that the expected folder structure exists for storing data files,
    such as draft data, player data, statistics, and logs.
    """
    directories = [
        FILE_PATH_TO_DATA,
        FILE_PATH_TO_DRAFTS,
        FILE_PATH_TO_PLAYERS,
        FILE_PATH_TO_SEASONS,
        FILE_PATH_TO_PLAYOFFS,
        FILE_PATH_TO_HISTORY,
        FILE_PATH_TO_STATS,
        FILE_PATH_TO_PLAYOFF_STATS,
        FILE_PATH_TO_SALARIES,
        FILE_PATH_TO_PLAYER_SALARIES_HISTORY,
        FILE_PATH_TO_GAMES_DATA,
        FILE_PATH_TO_LOG
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Directory '{directory}' created.")
