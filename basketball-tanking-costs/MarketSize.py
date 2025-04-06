"""
MarketSize.py

This module provides tools to analyze NBA team market size based on metro population
and media market ranking. It generates a data table and a bar chart for visual insights.

Data Sources:
- U.S. Census Bureau (2025). Metropolitan and Micropolitan Statistical Areas Population Totals.
- Nielsen Company (2024). 2023 Market Ranks.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from General import pretty_print_df, save_plot
from Paths import FILE_PATH_TO_COMPILED_DATA


def create_market_share_table():
    """
    Creates a DataFrame with NBA teams and their corresponding metro area population,
    media market rank, and market size category. Also exports the table to CSV.

    Returns:
        pd.DataFrame: The full NBA market data.
    """
    nba_market_full = {
        "Team": [
            "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls",
            "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors",
            "Houston Rockets", "Indiana Pacers", "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies",
            "Miami Heat", "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
            "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
            "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards"
        ],
        "Metro Area": [
            "Atlanta, GA", "Boston, MA", "New York, NY", "Charlotte, NC", "Chicago, IL",
            "Cleveland, OH", "Dallas-Fort Worth, TX", "Denver, CO", "Detroit, MI", "San Francisco Bay Area, CA",
            "Houston, TX", "Indianapolis, IN", "Los Angeles, CA", "Los Angeles, CA", "Memphis, TN",
            "Miami, FL", "Milwaukee, WI", "Minneapolis-St. Paul, MN", "New Orleans, LA", "New York, NY",
            "Oklahoma City, OK", "Orlando, FL", "Philadelphia, PA", "Phoenix, AZ", "Portland, OR",
            "Sacramento, CA", "San Antonio, TX", "Toronto, ON", "Salt Lake City, UT", "Washington, DC"
        ],
        "Est. Metro Population (millions)": [
            6.0, 4.9, 19.6, 2.8, 9.5,
            2.0, 7.6, 3.0, 4.4, 7.8,
            7.1, 2.1, 13.2, 13.2, 1.3,
            6.1, 1.6, 3.7, 1.3, 19.6,
            1.4, 2.7, 6.2, 5.1, 2.5,
            2.4, 2.6, 6.7, 1.2, 6.3
        ],
        "Media Market Rank (Nielsen)": [
            7, 10, 1, 22, 3,
            19, 5, 17, 14, 6,
            8, 25, 2, 2, 51,
            18, 37, 15, 50, 1,
            45, 20, 4, 11, 21,
            20, 31, "-", 27, 9
        ],
        "Market Size Category": [
            "Mid", "Large", "Large", "Mid", "Large",
            "Small", "Large", "Mid", "Mid", "Large",
            "Large", "Small", "Large", "Large", "Small",
            "Mid", "Small", "Mid", "Small", "Large",
            "Small", "Mid", "Large", "Mid", "Mid",
            "Mid", "Small", "Large", "Small", "Large"
        ]
    }

    nba_market_full_df = pd.DataFrame(nba_market_full)
    nba_market_full_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "market_size.csv", index=False)
    print(pretty_print_df(nba_market_full_df, 30))
    return nba_market_full_df


def plot_metropolitan_area(sorted_df):
    """
    Plots a bar chart of NBA teams by estimated metro population and market size category.

    Args:
        sorted_df (pd.DataFrame): DataFrame sorted by metro population.
    """
    plt.figure(figsize=(12, 10))
    sns.barplot(
        data=sorted_df,
        x='Est. Metro Population (millions)',
        y='Team',
        hue='Market Size Category',
        dodge=False,
        palette='viridis'
    )

    plt.title('NBA Teams by Metro Population and Market Size Category')
    plt.xlabel('Estimated Metro Population (millions)')
    plt.ylabel('NBA Team')
    plt.legend(title='Market Size')
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    save_plot(plt, "plot_metropolitan_area")
    plt.show()


def do_market_size_option():
    """
    Main function to generate the market size table and plot.

    Calls:
        - create_market_share_table()
        - plot_metropolitan_area() with sorted DataFrame
    """
    nba_market_full_df = create_market_share_table()
    market_size_df_sorted = nba_market_full_df.sort_values(by='Est. Metro Population (millions)', ascending=True)
    plot_metropolitan_area(market_size_df_sorted)


if __name__ == "__main__":
    do_market_size_option()
