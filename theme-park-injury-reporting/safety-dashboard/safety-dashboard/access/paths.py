"""
Project Name: Star Power
File: paths.py
Purpose: Defines directory paths, constants, and remote URLs used across the film and TV ratings analysis project.
Ensures proper directory structure and centralizes access to key data locations and Google Drive resources.

Author: Kyle Salgado-Gouker

"""

import os
from telnetlib import NOOPT


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
DOWNLOAD_DIRECTORY = os.path.join(DATA_DIRECTORY, "download")
LOG_DIRECTORY = os.path.join(DATA_DIRECTORY, "log")
NEISS_DIRECTORY = os.path.join(DATA_DIRECTORY, "neiss")

ALL_DIRECTORIES = [
    DATA_DIRECTORY,
    DOWNLOAD_DIRECTORY,
    LOG_DIRECTORY,
    NEISS_DIRECTORY
]

# --- Local Files ---

SUGGESTION_2_FILE = os.path.join(DOWNLOAD_DIRECTORY, "suggestion-2-fed res stl - theme park sales.csv")
SUGGESTION_4_FILE = os.path.join(DOWNLOAD_DIRECTORY, "suggestion-4-DisneylandReviews.csv")
SUGGESTION_5_FILE = os.path.join(DOWNLOAD_DIRECTORY, "suggestion-5-disney-universal-incident-data.csv")
SUGGESTION_6_FILE = os.path.join(DOWNLOAD_DIRECTORY, "retail_sales_dataset.csv")

# --- Downloadable Data URLs ---


# --- Modeling Dataset File Paths ---


# --- Intermediate Data Sources (Google Drive URLs) ---

# SERIES_RATINGS_JUMP_TABLE_URL = get_google_drive_download_link("https://drive.google.com/file/d/10DkAK9Opsz6HAtAjKSjukDXZHSLZeBzU/view?usp=drive_link")


if __name__ == '__main__':
    ensure_directories_exist(ALL_DIRECTORIES)
