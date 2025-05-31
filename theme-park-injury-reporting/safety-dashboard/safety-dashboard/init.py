"""
Overview:
The `init.py` module is responsible for initializing and preparing data before the application starts.
It ensures that necessary data files are downloaded and loaded into Pandas DataFrames
for use in the application.

Functions:

1. init_data():
   - Downloads required data files and reads them into Pandas DataFrames.
   - Returns:
     - child_care_prices_df (DataFrame): DataFrame containing child care price data.
     - fips_df (DataFrame): DataFrame containing FIPS county and state mapping information.
   - Logic:
     - Calls `download_file()` to download CSV files from specified URLs.
     - Reads the downloaded files into DataFrames using `pd.read_csv()`.
     - Calls `show_df_info()` to print information about the DataFrames for verification.

Dependencies:
- `download_file()` and `download_binary_file()` from `download`: Handle file downloading.
- `show_df_info()` from `print_output`: Prints summary information about DataFrames.
- `paths`: Provides URL constants and file path variables.
- `warnings` and `pandas`: Used for data manipulation and handling potential warnings.

External Resources:
- The module downloads the following files:
  - `CHILD_CARE_PRICES_URL`: URL for child care prices data.
  - `FIPS_COUNTY_TABLE_URL`: URL for the FIPS county table.
  - `METADATA_CHILD_CARE_PRICES_URL`: URL for metadata related to child care prices.

File Paths and Constants:
- `CHILD_CARE_PRICES_FILE`: Local path for storing the child care prices data.
- `FIPS_COUNTY_FILE`: Local path for storing the FIPS county data.
- `METADATA_CHILD_CARE_PRICES_FILE`: Local path for storing the metadata file.

Usage:
- This module should be called to initialize data before starting the main application.
- The returned DataFrames (`child_care_prices_df` and `fips_df`) are essential
    for further application processing.

"""

from download import download_binary_file, download_file
from print_output import show_df_info
from paths import FIPS_COUNTY_TABLE_URL, CHILD_CARE_PRICES_URL, CHILD_CARE_PRICES_FILE, FIPS_COUNTY_FILE, \
    FINAL_DATA_DIRECTORY, METADATA_CHILD_CARE_PRICES_URL, METADATA_CHILD_CARE_PRICES_FILE
import warnings
import pandas as pd


# Download and read files into data frames.
def init_data():
    # This function runs before the app starts to ensure all necessary data is downloaded

    download_file(CHILD_CARE_PRICES_URL, CHILD_CARE_PRICES_FILE)
    download_file(FIPS_COUNTY_TABLE_URL, FIPS_COUNTY_FILE, True)
    download_file(METADATA_CHILD_CARE_PRICES_URL, METADATA_CHILD_CARE_PRICES_FILE)

    child_care_prices_df = pd.read_csv(CHILD_CARE_PRICES_FILE)
    fips_df = pd.read_csv(FIPS_COUNTY_FILE)

    show_df_info(child_care_prices_df, "Child Care Prices Data")
    show_df_info(fips_df, "FIPS county and state info")
    return child_care_prices_df, fips_df
