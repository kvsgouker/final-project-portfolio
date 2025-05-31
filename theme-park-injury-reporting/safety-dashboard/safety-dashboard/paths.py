"""
Overview:
The `paths.py` module defines and manages paths and URLs used for data storage and access
within the application. It ensures necessary directories are created and provides
constants for file paths and URLs related to data downloads and storage.

Key Variables and Constants:

1. DATA_DIRECTORY:
   - Path to the main data directory (`"data"`).
   - Checks if the directory exists and creates it if not, printing a confirmation message.

2. FINAL_DATA_DIRECTORY:
   - Path to the final data subdirectory (`"data/final"`).
   - Ensures the directory exists and creates it if needed, with a printed confirmation.

3. MAP_FILE:
   - Path to a shapefile for maps:
   (`"maps/ne_110m_admin_1_states_provinces/ne_110m_admin_1_states_provinces.shp"`).

4. CHILD_CARE_PRICES_FILE:
   - Local path for storing the child care prices summary CSV file.
   - `FINAL_DATA_DIRECTORY + "/summary_states_year.csv"`.

5. CHILD_CARE_PRICES_URL:
   - URL to download the child care prices data.
   - `"https://drive.google.com/uc?id=1Pp64-2KdL2Crp-Gn0uRzK5lKOCvMcgEY&export=download"`.

6. METADATA_CHILD_CARE_PRICES_FILE:
   - Local path for storing the metadata of the national child care prices database.
   - `FINAL_DATA_DIRECTORY + "metadata of national database of childcare prices.csv"`.

7. METADATA_CHILD_CARE_PRICES_URL:
   - URL to download the metadata file.
   - `"https://drive.google.com/uc?id=1QGX9ht3PMFzdFcxEtBuvMEjkQmKjkJgM&export=download"`.

8. INFLATION_TABLE_URL:
- URL for accessing the historical Consumer Price Index (CPI) table:
"https://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/"

9. FIPS_COUNTY_TABLE_URL:
   - URL to download FIPS county codes data.
   - `"https://github.com/kjhealy/fips-codes/blob/master/state_and_county_fips_master.csv"`.

10. FIPS_COUNTY_FILE:
    - Local path for storing the FIPS county codes CSV file.
    - `FINAL_DATA_DIRECTORY + "/fips_county_codes.csv"`.

File System Checks:
- The script checks if `DATA_DIRECTORY` and `FINAL_DATA_DIRECTORY` exist.
- Creates directories if they do not exist and prints a message confirming their creation.

Usage:
- This module should be imported to provide standardized paths and URLs for
data management and file downloads in other parts of the application.
- Ensures data organization by structuring downloaded and stored files under defined directories.

"""

# File system searches, etc.
import os

# Stores data in its own directory for organization purposes.
DATA_DIRECTORY = "data"

# Check if the directory exists
if not os.path.exists(DATA_DIRECTORY):
    # If it doesn't exist, make it
    os.makedirs(DATA_DIRECTORY)
    print(f"Directory '{DATA_DIRECTORY}' created.")

MAP_FILE = "maps/ne_110m_admin_1_states_provinces/ne_110m_admin_1_states_provinces.shp"

CHILD_CARE_PRICES_FILE = DATA_DIRECTORY + \
    "/summary_states_year.csv"
CHILD_CARE_PRICES_URL = \
    "https://drive.google.com/uc?id=1Pp64-2KdL2Crp-Gn0uRzK5lKOCvMcgEY&export=download"

METADATA_CHILD_CARE_PRICES_FILE = DATA_DIRECTORY + \
    "metadata of national database of childcare prices.csv"
METADATA_CHILD_CARE_PRICES_URL = \
    "https://drive.google.com/uc?id=1QGX9ht3PMFzdFcxEtBuvMEjkQmKjkJgM&export=download"

# For conversion to 2024 dollars.
INFLATION_TABLE_URL = \
"https://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/"


