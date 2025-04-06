import time
import urllib
import os
import requests
import random
import pandas as pd
from tabulate import tabulate
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}

def download(url, destination):
    """
    Download a file from the specified URL and save it to a local destination.
    This function avoids aggressive scraping by:
    - Respecting HTTP 429 (Too Many Requests) responses and backing off.
    - Sleeping for a short random interval after successful downloads.
    - Skipping downloads if the destination file already exists.

    Args:
        url (str): The URL to download the file from.
        destination (str): The local path where the file should be saved.

    Returns:
        bool: True if the file was downloaded or already exists, False otherwise.
    """
    if not os.path.exists(destination):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                with open(destination, 'w') as f:
                    f.write(response.text)
                print(f"Downloaded {destination}")
                time.sleep(random.uniform(2, 6))
                return True

            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait = int(retry_after)
                    print(f"Rate limit exceeded. Waiting {wait} seconds.")
                    time.sleep(wait)
                else:
                    print("Rate limit exceeded. Retry-After header not found. Waiting 60 seconds.")
                    time.sleep(60)
                return download(url, destination)

            else:
                print(f"Website returned status code: {response.status_code}")

        except urllib.error.HTTPError:
            print(f"HTTP error while downloading {url}")
        except Exception as e:
            print(f"Error writing to {destination}: {e}")

        return False
    else:
        return True  # Already downloaded


def pretty_print_df(df, rows=None, interesting_columns=None, headers='keys'):
    """
    Pretty-print a pandas DataFrame using the `tabulate` library.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        rows (int, optional): The number of rows to display from the top. Defaults to None (shows all).
        interesting_columns (list, optional): A list of columns to include. If None, all columns are shown.
        headers (str): Header formatting for tabulate. Defaults to 'keys'.

    Returns:
        str: A formatted string representing the DataFrame.
    """
    if rows is not None:
        df = df.head(rows)

    if interesting_columns:
        df = df[interesting_columns]

    return tabulate(df, headers=headers, tablefmt='pretty', showindex=False)


def pretty_print_df_info_with_nans(df):
    """
    Pretty-print metadata of a dataframe with NaNs and unique values.

    Args:
        df (pd.DataFrame): The DataFrame to display.

    Returns:
        str: A formatted string representing the DataFrame's meta data.
    """
    # Show the column names, data types, count of NaN values, and unique values.
    columns_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes,
        'NaN Count': df.isnull().sum(),
        'Unique Values': df.nunique()
    }).reset_index(drop=True)

    # Convert to int where appropriate
    columns_info['NaN Count'] = columns_info['NaN Count'].astype(int)
    columns_info['Unique Values'] = columns_info['Unique Values'].astype(int)

    table = tabulate(columns_info, headers='keys', tablefmt='pretty', showindex="always")
    return f"Dataframe Information:\n{table}"


def show_df_info(df, title):
    """
    Pretty-print meta data of a dataframe with NaNs and unique values and a title.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        title (str): The title of the dataframe.

    Returns:
        str: A formatted string representing the DataFrame's meta data.
    """
    return (f"\nDataframe information for {title}:\n" + pretty_print_df_info_with_nans(df) +"\n" +
           f"\nThere are {df.shape[0]} rows and {df.shape[1]} columns of information.\n")


def prepare_for_numeric_modeling(df, cols):
    """
    Pretty-print meta data of a dataframe with NaNs and unique values and a title.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        cols (list): A list of column names. These will be cast to numbers using panda.

    Returns:
        pd.DataFrame: A dataframe without NaNs with columns coerced to numeric values.'
    """
    df = df.dropna(subset=cols).copy()
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna(subset=cols)


def determine_season(date):
    """
    Pretty-print meta data of a dataframe with NaNs and unique values and a title.

    Args:
        date (datetime.date): The date to determine the season. Oct 15 is cutoff day.

    Returns:
        int: season number (year when season ends)

    """
    date = pd.to_datetime(date)
    if date.month < 10 or (date.month == 10 and date.day < 15):
        return date.year
    return date.year + 1


def printFormattedTestStat(value, dec=2):
    """
    Formats a numeric value into a formatted string of val with dec decimal places.

    Args:
        value (str): value to format
        dec (int): number of decimal places to show

    Returns:
        str: A formatted string representing the test statistic.
    """
    format_string = "{:.{dec}f}"
    return format_string.format(value, dec=dec)


def printCurrencyFormattedTestStat(value, dec=2):
    """
    Formats a currency value into a formatted string of val with dec decimal places.

    Args:
        value (str): value to format
        dec (int): number of decimal places to show

    Returns:
        str: A formatted string representing the test statistic.
    """
    format_string = "{:,.{dec}f}"
    return format_string.format(value, dec=dec)


def add_hint_to_filename(root, hint):
    """
    Adds "hint" to help distinguish similar graph filenames.

    Args:
        root (str): base name of graph plot image filename
        hint (str): hint for filename to distinguish it

    Returns:
        str: file name with "hint" embedded
    """
    if hint is not None and len(hint) > 0:
        return f"{root}_{hint}"
    else:
        return root


def add_hint_to_title(root, hint):
    """
    Adds "hint" to help distinguish graphs by adding hint to title.

    Args:
        root (str): base name of graph plot.
        hint (str): hint to distinguish it.

    Returns:
        str: Title with "hint" embedded
    """
    if hint is not None and len(hint) > 0:
        return f"{root}: {hint}"
    else:
        return root


def save_plot(plt_obj, filename: str, folder: str = "plots", dpi=300):
    """
    Save a matplotlib plot to disk.

    Args:
        plt_obj (matplotlib.pyplot): The plt object to save.
        filename (str): Desired filename (without extension).
        folder (str): Folder to save the plot in (will be created if doesn't exist).
        dpi (int): Resolution.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(folder, f"{filename}_{timestamp}.png")

    plt_obj.savefig(full_path, dpi=dpi, bbox_inches='tight')
    print(f"Plot saved to {full_path}")
