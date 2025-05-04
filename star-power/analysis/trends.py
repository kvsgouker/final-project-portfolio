"""
Project Name: Star Power
File: trends.py

Fetches and applies Google Trends data for episodes based on title and air date.
Uses pytrends to assess search interest before and after release.


Author: Kyle Salgado-Gouker

"""

from pytrends.request import TrendReq
from datetime import datetime, timedelta

from access.paths import DATA_DIRECTORY
from utils.date_utils import validate_date


# # Example usage
# fetch_trend_data("Game of Thrones", "Winter is Coming", "2011-04-17")

def fetch_trend_data(series_name, episode_name, air_date, retries=5):
    pytrend = TrendReq()
    kw_list = [f"{episode_name} {series_name}"]
    print("Getting Trend Data for ", kw_list)
    dt_format = '%Y-%m-%d'
    air_date_dt = datetime.strptime(air_date, dt_format)
    # 3 days before, 10 days after
    start_date = (air_date_dt - timedelta(days=3)).strftime(dt_format)
    end_date = (air_date_dt + timedelta(days=10)).strftime(dt_format)
    timeframe = f'{start_date} {end_date}'
    # category = 3  # Arts & Entertainment

    attempt = 0
    while attempt < retries:
        try:
            # pytrend.build_payload(kw_list, cat=category, timeframe=timeframe)
            pytrend.build_payload(kw_list, timeframe=timeframe)
            trends = pytrend.interest_over_time()
            if not trends.empty:
                return trends.mean().values[0]  # Average trend over the timeframe
            return 0  # If no trend data is found
        except Exception as e:
            print(f"Error fetching trends: {e}. Retrying in {2 ** attempt} seconds...")
            time.sleep(2 ** attempt)  # Exponential backoff
            attempt += 1

    print("Max retries exceeded.")
    return 0  # Return a default value after exceeding retries


def apply_trends(row):
    try:
        imdb_series_id = row['IMDb Series ID']
        main_row = tv_shows_main_df[tv_shows_main_df['IMDb Series ID'] == imdb_series_id]
        if not main_row.empty and 'Title' in main_row.columns:
            series_name = main_row['Title'].iloc[0]  # Extract series name as a string
            episode_name = row['title']

            # Validate release date before fetching trend data
            if validate_date(row['releaseDate']):
                return fetch_trend_data(series_name, episode_name, row['releaseDate'])
            else:
                print(f"Invalid release date for {row['title']}: {row['releaseDate']}")
                return 0
        else:
            print(f"No matching series found in main DataFrame for IMDb Series ID {imdb_series_id}")
            return 0
    except Exception as e:
        print(f"Error fetching trends for {row['Title']}: {e}")
        return 0


def apply_trends_to_dataframe(df):
    # Assuming episodes_df is your DataFrame
    df['Google Trends'] = df.copy().apply(apply_trends, axis=1)
    return df


