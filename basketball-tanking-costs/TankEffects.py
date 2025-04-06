"""
TankEffects.py

This module contains tools for analyzing the effects of tanking in the NBA,
with a focus on forecasting, trend analysis, and data transformation.

Functionality includes:
- Computing lagged performance metrics and win percentages
- Forecasting future team or player outcomes based on historical data
- Generating smoothed or normalized performance visualizations
- Supporting functions for attendance and revenue impact studies

Data Sources:
- Historical game logs, franchise mappings, and cleaned player records
- Revenue and attendance metrics from team financial data

Dependencies:
- pandas, numpy, matplotlib, seaborn, BeautifulSoup (for parsing if needed)
- statsmodels for regression modeling
- FreeAgent, General, Tables, TankLog (internal modules)

Typical Usage:
- Used in conjunction with regression pipelines or exploratory notebooks
- Supports graphics output and data formatting for downstream modeling
"""

import textwrap
import lxml
import datetime

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from bs4 import BeautifulSoup
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from FreeAgent import generate_efficiency_table
from General import (
    add_hint_to_filename,
    add_hint_to_title,
    determine_season,
    download,
    prepare_for_numeric_modeling,
    save_plot,
    show_df_info
)
from Paths import FILE_PATH_TO_COMPILED_DATA
from Tables import (
    load_extended_cleaned_player_records,
    load_extended_game_history,
    load_team_revenue
)
from TankLog import TankLog


def compute_fan_attendance_and_wins(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes per-season attendance and win statistics for each NBA franchise.

    This function:
    - Infers the season year from each game's date.
    - Computes win flags for both home and away teams.
    - Aggregates home and away statistics (wins, games, attendance).
    - Merges these into a unified team-season view.
    - Calculates total and average attendance and win percentage.

    Args:
        games_df (pd.DataFrame): A DataFrame containing game-level data with the following required columns:
            - 'gameId': Unique identifier for each game.
            - 'gameDate': A datetime object representing when the game occurred.
            - 'hometeamId', 'awayteamId': Team IDs for home and away teams.
            - 'home_team_franchise_id', 'away_team_franchise_id': Franchise mappings.
            - 'winner': The team ID of the game winner.
            - 'attendance': The reported attendance for the game.

    Returns:
        pd.DataFrame: A DataFrame grouped by franchise and season year, with these columns:
            - 'franchise_id'
            - 'season_year'
            - 'home_games', 'away_games', 'total_games'
            - 'home_wins', 'away_wins', 'total_wins'
            - 'home_attendance_total', 'away_attendance_total', 'attendance_total'
            - 'home_attendance_avg', 'away_attendance_avg', 'attendance_avg'
            - 'win_pct' (overall win percentage for the season)
    """
    df = games_df.copy()

    # Compute season year
    df["season_year"] = df["gameDate"].apply(
        lambda d: d.year + 1 if d.month >= 10 else d.year
    )

    # Initialize win/loss flags for both home and away teams
    df["home_win"] = (df["hometeamId"] == df["winner"]).astype(int)
    df["away_win"] = (df["awayteamId"] == df["winner"]).astype(int)

    # Create home game attendance and win summaries
    home_stats = df.groupby(["home_team_franchise_id", "season_year"]).agg(
        home_games=("gameId", "count"),
        home_wins=("home_win", "sum"),
        home_attendance_total=("attendance", "sum"),
        home_attendance_avg=("attendance", "mean")
    ).reset_index().rename(columns={"home_team_franchise_id": "franchise_id"})

    # Create away game attendance and win summaries
    away_stats = df.groupby(["away_team_franchise_id", "season_year"]).agg(
        away_games=("gameId", "count"),
        away_wins=("away_win", "sum"),
        away_attendance_total=("attendance", "sum"),
        away_attendance_avg=("attendance", "mean")
    ).reset_index().rename(columns={"away_team_franchise_id": "franchise_id"})

    # Merge home and away summaries
    fan_attendance_df = pd.merge(home_stats, away_stats, on=["franchise_id", "season_year"], how="outer").fillna(0)

    # Calculate overall stats
    fan_attendance_df["total_games"] = fan_attendance_df["home_games"] + fan_attendance_df["away_games"]
    fan_attendance_df["total_wins"] = fan_attendance_df["home_wins"] + fan_attendance_df["away_wins"]
    fan_attendance_df["win_pct"] = fan_attendance_df["total_wins"] / fan_attendance_df["total_games"]

    fan_attendance_df["attendance_total"] = fan_attendance_df["home_attendance_total"] + fan_attendance_df["away_attendance_total"]
    fan_attendance_df["attendance_avg"] = fan_attendance_df["attendance_total"] / fan_attendance_df["total_games"]

    return fan_attendance_df


def plot_impact_cost_highlighted(
    df,
    column='Lagging_Impact_AVG_COST_2Y',
    loser_threshold=0.4,
    winner_threshold=0.6,
    bins=30,
    hint=""
):
    """
    Plots a histogram of a given impact-related cost metric, highlighting values
    associated with players on low-performing (losing) teams.

    Args:
        df (pd.DataFrame): DataFrame containing at least the specified `column` and 'Pct' (win %) columns.
        column (str): Name of the cost or impact column to plot.
        win_threshold (float): Maximum win percentage to consider a team as "losing."
        bins (int): Number of histogram bins.
        hint (str): Optional string to include in plot title and filename suffix.

    Behavior:
        - If the specified column is missing, the function logs a warning and exits gracefully.
        - Produces a histogram comparing the distribution of the metric across:
            1. All players (in gray)
            2. Players on losing teams (in red)
        - Saves and displays the histogram with formatted axes and labels.

    Output:
        - Saves the plot to disk using `save_plot`.
        - Displays the plot using `plt.show()`.
    """
    df = df.copy().reset_index(drop=True)

    if column not in df.columns:
        TankLog.get_shared_logger().log(
            TankLog.WARNING_LOGGING,
            f"Warning: Column '{column}' does not exist in dataframe."
        )
        all_values = pd.Series(dtype='float64')
        losing_values = pd.Series(dtype='float64')
        winning_values = pd.Series(dtype='float64')
    else:
        all_values = df[column].dropna()
        losing_values = df[df['Pct'] < loser_threshold][column].dropna()
        winning_values = df[df['Pct'] > winner_threshold][column].dropna()

    plt.figure(figsize=(12, 6))

    # Full dataset histogram (background)
    plt.hist(
        all_values,
        bins=bins,
        color='lightgray',
        edgecolor='gray',
        label='All Players',
        alpha=0.7
    )

    # Overlay for losing teams
    plt.hist(
        losing_values,
        bins=bins,
        color='red',
        edgecolor='darkred',
        label=f'Teams with win% < {loser_threshold:.0%}',
        alpha=0.6
    )

    # Overlay for losing teams
    plt.hist(
        winning_values,
        bins=bins,
        color='green',
        edgecolor='darkgreen',
        label=f'Teams with win% > {winner_threshold:.0%}',
        alpha=0.6
    )

    plt.xlabel(f'{column.replace("_", " ")} ($)')
    plt.ylabel('Frequency')
    plt.title(f'{add_hint_to_title(column.replace("_", " "), hint)} with Highlight on Losing Teams')
    plt.legend()
    plt.grid(True)

    ax = plt.gca()
    ax.ticklabel_format(style='plain', axis='x')
    ax.xaxis.set_major_formatter(ScalarFormatter())

    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("UnproductiveLosingFreeAgents", hint))
    plt.show()


def filter_seasons(df, min_year=None, max_year=None, exclude_seasons=None):
    """
    Filters a dataframe by season_year.

    Parameters:
    - df (pd.DataFrame): The dataframe to filter (must have 'season_year' column).
    - min_year (int or None): Minimum season year to include.
    - max_year (int or None): Maximum season year to include.
    - exclude_seasons (list of int or None): Specific seasons to exclude.

    Returns:
    - Filtered dataframe.
    """
    df_filtered = df.copy()

    if min_year is not None:
        df_filtered = df_filtered[df_filtered['season_year'] >= min_year]

    if max_year is not None:
        df_filtered = df_filtered[df_filtered['season_year'] <= max_year]

    if exclude_seasons is not None:
        df_filtered = df_filtered[~df_filtered['season_year'].isin(exclude_seasons)]

    return df_filtered


def plotHomeAttendanceVsWinPercentage(fan_attendance_df, hint=""):
    # Plot: Total Attendance vs Win Percentage
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_df, x='Pct', y='avg_home_attendance', legend=False)
    sns.regplot(
        x=fan_attendance_df['Pct'].to_numpy(),
        y=fan_attendance_df['avg_home_attendance'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )

    plt.title(add_hint_to_title('Home Attendance vs Team Win Percentage', hint))
    plt.xlabel('Win Percentage')
    plt.ylabel('Home Attendance')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("HomeAttendanceVsWinPercentage", hint))
    plt.show()

def plotLAFRVsLAFA(fan_attendance_revenue_df, hint=""):
    # Plot: Team Revenue vs Average Home Attendance
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_revenue_df, x='LAFA', y='LAFR')
    sns.regplot(
        x=fan_attendance_revenue_df['LAFA'].to_numpy(),
        y=fan_attendance_revenue_df['LAFR'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )

    plt.title(add_hint_to_title('Relative Team Revenue vs Relative Home Attendance', hint))
    plt.xlabel('Average Home Attendance')
    plt.ylabel('Team Revenue (as pct of league)')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("TeamRevenueVsRelativeHomeAttendance", hint))
    plt.show()


def plotLAFAVsWinPercentage(fan_attendance_df, hint=""):
    # Plot: Total Attendance vs Win Percentage
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_df, x='Pct', y='LAFA', legend=False)
    sns.regplot(
        x=fan_attendance_df['Pct'].to_numpy(),
        y=fan_attendance_df['LAFA'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )

    plt.title(add_hint_to_title('Relative Home Attendance vs Team Win Percentage', hint))
    plt.xlabel('Win Percentage')
    plt.ylabel('Relative Home Attendance (as pct of league)')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("LAFAVsWinPercentage", hint))
    plt.show()


# Plot: Average Home Attendance vs Win Percentage
def plotAverageHomeAttendanceVsWinPercentage(fan_attendance_df, hint=""):
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_df, x='Pct', y='attendance_avg', legend=False)
    sns.regplot(
        x=fan_attendance_df['Pct'].to_numpy(),
        y=fan_attendance_df['attendance_avg'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )

    plt.title(add_hint_to_title('Average Home Attendance vs Team Win Percentage', hint))
    plt.xlabel('Win Percentage')
    plt.ylabel('Average Home Attendance')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("TotalAttendanceVsWinPercentage", hint))
    plt.show()


def plotAwayAttendanceVsWinPercentage(fan_attendance_df, hint=""):
    # Effects of bad teams on away audiences.
    # Plot: Average Away Attendance vs Win Percentage
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_df, x='Pct', y='avg_away_attendance', legend=False)
    sns.regplot(
        x=fan_attendance_df['Pct'].to_numpy(),
        y=fan_attendance_df['avg_away_attendance'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )
    plt.title(add_hint_to_title('Average Away Attendance vs Team Win Percentage', hint))
    plt.xlabel('Win Percentage')
    plt.ylabel('Average Away Attendance')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("AwayAttendanceVsWinPercentage", hint))
    plt.show()


def plotTeamRevenueVsTotalWins(fan_attendance_revenue_df, hint=""):
    # Plot: Team Revenue vs Total Wins
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_revenue_df, x='total_wins', y='Team_Revenue')
    sns.regplot(
        x=fan_attendance_revenue_df['total_wins'].to_numpy(),
        y=fan_attendance_revenue_df['Team_Revenue'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )
    plt.title(add_hint_to_title('Team Revenue vs Total Wins', hint))
    plt.xlabel('Total Wins')
    plt.ylabel('Team Revenue (in millions)')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("TeamRevenueVsTotalWins", hint))
    plt.show()


def plotOperatingIncomeVsTotalWins(fan_attendance_revenue_df, hint=""):
    # Plot: Operating Income vs Total Wins
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_revenue_df, x='total_wins', y='Operating_Income')
    sns.regplot(
        x=fan_attendance_revenue_df['total_wins'].to_numpy(),
        y=fan_attendance_revenue_df['Operating_Income'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )
    plt.title(add_hint_to_title('Operating Income vs Total Wins', hint))
    plt.xlabel('Total Wins')
    plt.ylabel('Operating Income (in millions)')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("OperatingIncomeVsTotalWins", hint))
    plt.show()


def plotTeamRevenueVsAverageHomeAttendance(fan_attendance_revenue_df, hint=""):
    # Plot: Team Revenue vs Average Home Attendance
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=fan_attendance_revenue_df, x='avg_home_attendance', y='Team_Revenue')
    sns.regplot(
        x=fan_attendance_revenue_df['avg_home_attendance'].to_numpy(),
        y=fan_attendance_revenue_df['Team_Revenue'].to_numpy(),
        scatter=False,
        color='red',
        label='Trend Line'
    )
    plt.title(add_hint_to_title('Team Revenue vs Average Home Attendance', hint))
    plt.xlabel('Average Home Attendance')
    plt.ylabel('Team Revenue (in millions)')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, add_hint_to_filename("TeamRevenueVsAverageHomeAttendance", hint))
    plt.show()


def show_championships_plot(df_champs):
    # Clean team names to remove footnote markers like [i], [ii], etc.
    df_champs['Team'] = df_champs['Team'].str.replace(r'\[.*?\]', '', regex=True).str.strip()

    # Ensure 'Win' is numeric
    df_champs['Win'] = pd.to_numeric(df_champs['Win'], errors='coerce').fillna(0).astype(int)
    df_champs = df_champs[df_champs['Win'] >= 1]

    # Group single-championship teams into "Others"
    single_champs = df_champs[df_champs['Win'] == 1]
    others_row = pd.DataFrame({
        'Team': ['Others'],
        'Win': [single_champs['Win'].sum()],
        'Year(s) won': [', '.join([f"{row['Team']} ({row['Year(s) won']})" for _, row in single_champs.iterrows()])]
    })

    # Combine back the dataframe
    df_grouped = pd.concat([df_champs[df_champs['Win'] > 1], others_row]).sort_values(by='Win', ascending=False)
    # Define team colors
    team_colors = {
        'Los Angeles Lakers': '#552583',
        'Boston Celtics': '#007A33',
        'Golden State Warriors': '#FFC72C',
        'Chicago Bulls': '#CE1141',
        'San Antonio Spurs': '#C4CED4',
        'Miami Heat': '#98002E',
        'Detroit Pistons': '#002D62',
        'Philadelphia 76ers': '#006BB6',
        'Milwaukee Bucks': '#00471B',
        'Dallas Mavericks': '#00538C',
        'Houston Rockets': '#CE1141',
        'New York Knicks': '#F58426',
        'Portland Trail Blazers': '#E03A3E',
        'Cleveland Cavaliers': '#6F263D',
        'Atlanta Hawks': '#E03A3E',
        'Washington Wizards': '#002B5C',
        'Oklahoma City Thunder': '#007AC1',
        'Toronto Raptors': '#CE1141',
        'Denver Nuggets': '#0E2240',
        'Sacramento Kings': '#5A2D81',
        'Others': '#A9A9A9'
    }

    # Plot Donut Chart
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        df_grouped['Win'],
        labels=df_grouped['Team'],
        autopct='%1.1f%%',
        startangle=90,
        colors=[team_colors.get(team, '#333333') for team in df_grouped['Team']],
        wedgeprops=dict(width=0.4, edgecolor='white')
    )

    # Wrap the annotation nicely
    wrapped_text = textwrap.fill(f"Others: {others_row['Year(s) won'].values[0]}", width=80)

    # Place annotation below the plot
    plt.annotate(
        wrapped_text,
        xy=(0, -1.4), xycoords='axes fraction',
        ha='center', fontsize=8, wrap=True
    )

    # Title
    ax.set_title("NBA Championships Distribution by Team (Grouped)", fontsize=14, y=1.05)

    plt.tight_layout()
    save_plot(plt, "NBA_Championship_Donut")
    plt.show()


def perform_tanking_effects_analysis():
    """
    Plot a number of graphs, including a championship plot, attendance effects, revenue effects, etc.

    """
    # show distribution of nba championships
    local_url = FILE_PATH_TO_COMPILED_DATA + "championships.html"
    download("https://en.wikipedia.org/wiki/List_of_NBA_champions", local_url)
    try:
        with open(local_url, 'r', encoding='utf-8') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table') #, {'class': 'wikitable sortable sticky-header jquery-tablesorter'})

        # Get the second table
        championship_table = tables[2]

        # Load into pandas dataframe
        championship_table_df = pd.read_html(str(championship_table))[0]
        championship_table_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "championships_table.csv", index=False)
        show_championships_plot(championship_table_df)

    except FileNotFoundError:
        print("Championship page failed to download.")

    # load game data with columns for franchise id for home and away! (already done!)
    # Thank you, Eoin A Moore! https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores
    games_df = load_extended_game_history()
    print(show_df_info(games_df, "Games with Franchise Ids for Home and Away"))
    # This data comes from a published JP Morgan research document: https://assets.jpmprivatebank.com/content/dam/jpm-pb-aem/global/en/documents/eotm/a-piece-of-the-action.pdf
    team_revenue_df = load_team_revenue()
    print(show_df_info(team_revenue_df, "Team Revenue"))

    # Add season column. NBA seasons span two years. The constraint I use is Oct 15, which is after the 2020 Bubble Finals.
    # 2023-2024, therefore, is season 2024.
    games_df["season_year"] = games_df["gameDate"].apply(determine_season)

    # Filter for regular season games only and drop games without attendance
    regular_games_df = games_df[games_df["gameType"] == "Regular Season"]
    regular_games_df['attendance'].fillna(0)

    # Build the fan attendance table from the games data.
    fan_attendance_df = compute_fan_attendance_and_wins(regular_games_df)
    fan_attendance_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "fan_attendance.csv", index=False)

    # Debug output.
    TankLog.get_shared_logger().log(TankLog.INFO_LOGGING,f"{fan_attendance_df.groupby(['franchise_id', 'season_year']).size().value_counts()}")

    # Rename columns to match intended use in plotting
    fan_attendance_df.rename(columns={
        "win_pct": "Pct",
        "attendance_total": "total_attendance",
        "home_attendance_avg": "avg_home_attendance",
        "away_attendance_avg": "avg_away_attendance"
    }, inplace=True)

    # save a copy.
    fan_attendance_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "fan_attendance.csv", index=False)

    show_df_info(fan_attendance_df, "Season by Season Franchise Attendance for Home and Away with Winning Pct")

    # Filter both dataframes to shared range (2011–2021)
    revenue_years = range(2011, 2022)

    filtered_attendance_df = fan_attendance_df[fan_attendance_df["season_year"].isin(revenue_years)].copy()
    filtered_revenue_df = team_revenue_df[team_revenue_df["season_year"].isin(revenue_years)].copy()

    # Merge revenue into the attendance data for overlapping seasons
    fan_attendance_revenue_df = pd.merge(
        filtered_attendance_df,
        filtered_revenue_df[["franchise_id", "season_year", "Team Revenue", "Ticket Price", "Operating Income"]],
        on=["franchise_id", "season_year"],
        how="left"
    )

    # Rename columns to match intended use in plotting
    fan_attendance_revenue_df.rename(columns={
        'Team Revenue':'Team_Revenue',
        'Ticket Price':'Ticket_Price',
        'Operating Income':'Operating_Income'
    }, inplace=True)

    # === Compute League-Adjusted Metrics ===
    fan_attendance_revenue_df['LAFR'] = fan_attendance_revenue_df.groupby('season_year')['Team_Revenue'].transform(
        lambda x: x / x.sum())
    fan_attendance_revenue_df['LAFA'] = fan_attendance_revenue_df.groupby('season_year')[
        'home_attendance_total'].transform(lambda x: x / x.sum())

    columns_to_fix = [
        'LAFA',
        'LAFR',
        'Pct',
        'attendance_avg',
        'avg_away_attendance',
        'total_wins',
        'Team_Revenue',
        'Operating_Income'
    ]

    for col in columns_to_fix:
        fan_attendance_revenue_df[col] = (
            pd.to_numeric(fan_attendance_revenue_df[col], errors='coerce')
            .astype(float)
        )

    # Save with the new columns
    fan_attendance_revenue_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "fan_attendance_revenue.csv", index=False)

    # Exclude COVID seasons (2020 and 2021).
    fan_attendance_revenue_filtered_for_covid_df = filter_seasons(fan_attendance_revenue_df, min_year=2011, max_year=2019)

    merged_df, merged_not_on_rookie_scale_df = generate_efficiency_table()

    # Drop 'Pct' from lagged df to avoid conflict
    efficiency_lagged_df = merged_df.drop(columns=["Pct"])
    efficiency_lagged_not_on_rookie_scale_df = merged_not_on_rookie_scale_df.drop(columns=["Pct"])

    # Merge lagged efficiency data into the main team_season_df
    plot_df = pd.merge(fan_attendance_revenue_df, efficiency_lagged_df, on=['franchise_id', 'season_year'], how='left')
    print(show_df_info(plot_df, "Team Season - Merged Revenue and Performance"))

    no_rookie_scale_plot_df = pd.merge(fan_attendance_revenue_df, efficiency_lagged_not_on_rookie_scale_df, on=['franchise_id', 'season_year'], how='left')
    print(show_df_info(no_rookie_scale_plot_df, "Team Season - Merged Revenue and Performance - No Rookie Scale"))

    # Merge lagged efficiency data into the main team_season_df
    no_covid_plot_df = pd.merge(fan_attendance_revenue_filtered_for_covid_df, efficiency_lagged_df, on=['franchise_id', 'season_year'], how='left')
    no_covid_no_rookie_scale_plot_df = pd.merge(fan_attendance_revenue_filtered_for_covid_df, efficiency_lagged_df, on=['franchise_id', 'season_year'], how='left')
    print(show_df_info(no_covid_plot_df, "Team Season - Revenue and Performance - No covid."))

    # pretty graphs
    # Set plot style
    sns.set(style="whitegrid")

    fan_attendance_revenue_df['Pct'] = pd.to_numeric(fan_attendance_revenue_df['Pct'], errors='coerce')
    fan_attendance_revenue_df['avg_home_attendance'] = \
        pd.to_numeric(fan_attendance_revenue_df['avg_home_attendance'], errors='coerce')
    fan_attendance_revenue_df = fan_attendance_revenue_df.dropna(subset=['Pct', 'avg_home_attendance'])
    # Needed to do this to force right type of number.
    fan_attendance_revenue_df['Pct'] = fan_attendance_revenue_df['Pct'].astype('float64')
    fan_attendance_revenue_df['avg_home_attendance'] = fan_attendance_revenue_df['avg_home_attendance'].astype('float64')

    # Show graphs.
    plotHomeAttendanceVsWinPercentage(fan_attendance_revenue_df)
    plotAwayAttendanceVsWinPercentage(fan_attendance_revenue_df)
    plotAverageHomeAttendanceVsWinPercentage(fan_attendance_revenue_df)
    plotTeamRevenueVsTotalWins(fan_attendance_revenue_df)
    plotOperatingIncomeVsTotalWins(fan_attendance_revenue_df)
    plotTeamRevenueVsAverageHomeAttendance(fan_attendance_revenue_df)

    plot_impact_cost_highlighted(plot_df)

    fan_attendance_revenue_filtered_for_covid_df['Pct'] = pd.to_numeric(fan_attendance_revenue_filtered_for_covid_df['Pct'], errors='coerce')
    fan_attendance_revenue_filtered_for_covid_df['avg_home_attendance'] = \
        pd.to_numeric(fan_attendance_revenue_filtered_for_covid_df['avg_home_attendance'], errors='coerce')
    fan_attendance_revenue_filtered_for_covid_df = fan_attendance_revenue_filtered_for_covid_df.dropna(subset=['Pct', 'avg_home_attendance'])
    # Needed to do this to force right type of number.
    fan_attendance_revenue_filtered_for_covid_df['Pct'] = fan_attendance_revenue_filtered_for_covid_df['Pct'].astype('float64')
    fan_attendance_revenue_filtered_for_covid_df['avg_home_attendance'] = fan_attendance_revenue_filtered_for_covid_df['avg_home_attendance'].astype('float64')

    plotHomeAttendanceVsWinPercentage(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")
    plotAwayAttendanceVsWinPercentage(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")
    plotAverageHomeAttendanceVsWinPercentage(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")
    plotTeamRevenueVsTotalWins(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")
    plotOperatingIncomeVsTotalWins(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")
    plotTeamRevenueVsAverageHomeAttendance(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")

    plot_impact_cost_highlighted(no_covid_plot_df, hint = "Without Pandemic")

    plotLAFAVsWinPercentage(fan_attendance_revenue_filtered_for_covid_df,"Without Pandemic")
    plotLAFRVsLAFA(fan_attendance_revenue_filtered_for_covid_df, "Without Pandemic")

    # These last are worth modeling
    model_df = prepare_for_numeric_modeling(fan_attendance_revenue_filtered_for_covid_df, ['LAFA', 'LAFR', 'Pct'])

    X = model_df[['LAFA']]  # Independent variable
    X = sm.add_constant(X)  # Adds the intercept term
    y = model_df['Pct']  # Dependent variable

    lafa_vs_pct_model = sm.OLS(y, X).fit(cov_type='HC1')  # Use robust standard errors!
    # LAFA vs Pct
    print(lafa_vs_pct_model.summary())

    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=model_df, x='LAFA', y='Pct')
    sns.regplot(
        x=model_df['LAFA'].to_numpy(),
        y=model_df['Pct'].to_numpy(),
        scatter=False,
        color='red',
        label='OLS Fit'
    )
    plt.xlabel('Relative Average Home Attendance (LAFA)')
    plt.ylabel('Team Winning Percentage (Pct)')
    plt.title('Relationship Between Relative Attendance and Winning Percentage')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, "LAFA_vs_Pct_Model")
    plt.show()

    X = model_df[['LAFR']]
    X = sm.add_constant(X)
    y = model_df['Pct']

    # LAFR vs Pct
    lafr_vs_pct_model = sm.OLS(y, X).fit(cov_type='HC1')  # Use robust standard errors!

    print(lafr_vs_pct_model.summary())

    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=model_df, x='LAFR', y='Pct')
    sns.regplot(
        x=model_df['LAFR'].to_numpy(),
        y=model_df['Pct'].to_numpy(),
        scatter=False,
        color='red',
        label='OLS Fit'
    )
    plt.xlabel('Relative Average Franchise Revenue (LAFR)')
    plt.ylabel('Team Winning Percentage (Pct)')
    plt.title('Relationship Between Relative Revenue and Winning Percentage')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, "LAFR_vs_Pct_Model")
    plt.show()

    model_df = prepare_for_numeric_modeling(fan_attendance_revenue_filtered_for_covid_df, ['LAFA', 'LAFR', 'Pct'])

    # Remove any residual NaNs
    model_df = model_df.dropna(subset=['LAFA', 'LAFR', 'Pct'])

    X = model_df[['LAFA']]  # Independent variable
    X = sm.add_constant(X)  # Adds the intercept term
    y = model_df['LAFR']  # Dependent variable

    lafr_vs_lafa_model = sm.OLS(y, X).fit(cov_type='HC1')  # Robust standard errors recommended

    print(lafr_vs_lafa_model.summary())

    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=model_df, x='LAFA', y='LAFR')
    sns.regplot(
        x=model_df['LAFA'].to_numpy(),
        y=model_df['LAFR'].to_numpy(),
        scatter=False,
        color='red',
        label='OLS Fit'
    )
    plt.xlabel('Relative Average Home Attendance (LAFA)')
    plt.ylabel('Relative Team Revenue (LAFR)')
    plt.title('Relationship Between Relative Attendance and Relative Revenue')
    plt.legend()
    plt.tight_layout()
    save_plot(plt, "LAFA_vs_LAFR_Model")
    plt.show()


if __name__ == "__main__":
    perform_tanking_effects_analysis()
