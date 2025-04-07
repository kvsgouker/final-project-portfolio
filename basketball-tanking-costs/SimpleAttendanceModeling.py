"""
Attendance Modeling and Visualization Module

This module performs exploratory visualization and modeling of NBA game attendance,
including plotting lagged attendance trends and fitting regression models to identify
relationships between game performance and fan turnout.

Functions:
    - plot_attendance_vs_lag: Visualizes attendance trends with a 10-day lag.
    - do_attendance_modeling: Main modeling entry point (defined elsewhere).
"""

# === Standard Library Imports ===
import csv

# === Third-Party Imports ===
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# === Local Application Imports ===
from TankEffects import filter_seasons
from General import show_df_info, save_plot
from Paths import FILE_PATH_TO_COMPILED_DATA
from Tables import load_fan_attendance_revenue
from TankLog import TankLog

log = TankLog.get_shared_logger()


def plot_attendance_vs_lag(attendance_df):
    """
    Plots NBA home game attendance and its 10-game lagged average on dual axes.

    Args:
        attendance_df (pd.DataFrame): DataFrame containing 'gameDate', 'attendance',
                                      and 'attendance_lag_10' columns.

    Side Effects:
        - Displays a dual-axis plot.
        - Saves the figure to disk using `save_plot()`.
    """
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Primary axis: Home Attendance
    ax1.plot(
        attendance_df['gameDate'],
        attendance_df['attendance'],
        marker='o',
        linestyle='-',
        label='Home Attendance',
        color='blue'
    )
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Home Attendance", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    # Secondary axis: Lagged Attendance
    ax2 = ax1.twinx()
    ax2.plot(
        attendance_df['gameDate'],
        attendance_df['attendance_lag_10'],
        marker='s',
        linestyle='-',
        label='10-Day Lagged Attendance',
        color='green'
    )
    ax2.set_ylabel("10-Day Lagging Attendance", color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    # Title and Legends
    plt.title("Attendance and its 10-Day Lagged Value Over Time")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()
    save_plot(plt, "attendance_vs_lag")
    plt.show(block=False)


def run_ols_and_plot_residuals(X, y, title, filename):
    """
    Fits an OLS regression with robust standard errors, prints the summary,
    plots residuals, and calculates VIF.

    Args:
        X (pd.DataFrame): Predictor variables.
        y (pd.Series): Target variable.
        title (str): Title for the residuals plot.
        filename (str): File name to save the plot.
    """
    model = sm.OLS(y, X).fit(cov_type="HC1")
    print(model.summary())

    vif_data = pd.DataFrame({
        "feature": X.columns,
        "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    })
    print("\nVariance Inflation Factors:")
    print(vif_data)

    # Plot residuals
    plt.figure(figsize=(8, 5))
    sns.histplot(model.resid, bins=50, kde=True)
    plt.title(title)
    plt.xlabel("Residuals")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    save_plot(plt, filename)
    plt.show()


def do_attendance_modeling():
    """
    Runs exploratory and statistical analysis on NBA game attendance data.

    This function:
    1. Validates and inspects a compiled game history CSV for structural issues.
    2. Creates a 10-game lagged attendance variable per team.
    3. Fits linear regression models predicting attendance based on lag and win percentage.
    4. Produces and saves residual plots and VIF statistics to detect multicollinearity.
    5. Repeats similar modeling using season-level revenue and attendance data.

    Outputs:
        - Model summaries printed to console
        - Residual plots saved to disk
        - DataFrame statistics printed via `show_df_info`
    """

    expected_columns = 33  # Update this if your real CSV has 33 columns

    bad_rows = []

    with open(FILE_PATH_TO_COMPILED_DATA + "extended_game_history.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            field_count = len(row)
            if i == 0:
                print(f"Header has {field_count} columns.")
                continue  # header
            if field_count != expected_columns:
                bad_rows.append((i, field_count, row))

    print(f"\nTotal bad rows found: {len(bad_rows)}\n")

    for i, (row_num, field_count, row) in enumerate(bad_rows[:20]):  # limit to first 20 bad rows
        print(f"Row {row_num}: has {field_count} fields")
        print(row)
        print("-" * 40)

    if len(bad_rows) > 20:
        print(f"... and {len(bad_rows) - 20} more bad rows.")

    games_df = pd.read_csv(FILE_PATH_TO_COMPILED_DATA + "extended_game_history.csv")
        # load_extended_game_history())
    log.log(TankLog.WARNING_LOGGING, show_df_info(games_df, "Games History"))

    games_df = games_df[((games_df['season_year'] > 2004) & (games_df['season_year'] < 2020)) | (games_df['season_year'] > 2021)]
    selected_games_df = games_df.copy()

    print(show_df_info(games_df, "Games History"))
    # Prepare data for modeling
    # Create lagged attendance (10-day lag within each franchise)
    games_df['attendance_lag_10'] = games_df.groupby('home_team_franchise_id')['attendance'].shift(10)

    # Drop rows with missing values in relevant columns
    model_df = games_df.dropna(subset=[
        'attendance',
        'attendance_lag_10',
        # 'home_team_last10_win_pct',
        # 'home_team_last20_win_pct',
        'home_team_last50_win_pct',
        'season_year'
    ]).copy()

    # Select variables for modeling
    X = model_df[[
        'attendance_lag_10',
        # 'home_team_last10_win_pct',
        # 'home_team_last20_win_pct',
        'home_team_last50_win_pct',
        'season_year'
    ]]

    # Add constant for intercept
    X = sm.add_constant(X)

    # Define target variable
    target = 'attendance'
    y = model_df[target]

    # Fit OLS model with robust std errors.
    model = sm.OLS(y, X).fit(cov_type="HC1")

    # Display model summary
    print(model.summary())

    games_df = selected_games_df.copy()

    # Filter for valid seasons
    games_subset_df = games_df[((games_df['season_year'] > 2004) & (games_df['season_year'] < 2020)) | (games_df['season_year'] > 2021)].copy()

    # Create lagged attendance (10-day lag within each franchise)
    games_subset_df['attendance_lag_10'] = games_subset_df.groupby('home_team_franchise_id')['attendance'].shift(10)

    # Drop rows with missing values in relevant columns
    model_df = games_subset_df.dropna(subset=[
        target,
        'attendance_lag_10',
        'home_team_last50_win_pct'
    ]).copy()

    # Prepare the model variables
    X = model_df[['attendance_lag_10', 'home_team_last50_win_pct', 'season_year']]
    X = sm.add_constant(X)
    y = model_df['attendance']

    # Residual plot
    # Needs optimized. Skips display.
    run_ols_and_plot_residuals(X, y, "Residuals Distribution", "attendance_model_residuals")

    print(show_df_info(games_subset_df, "Games History"))
    # very slow graph. remove for now.
    # plot_attendance_vs_lag(games_subset_df)

    df = load_fan_attendance_revenue()
    fan_attendance_revenue_filtered_for_covid_df = filter_seasons(df, min_year=2011,
                                                                  max_year=2019)
    print(show_df_info(fan_attendance_revenue_filtered_for_covid_df, "Fan Attendance and Revenue"))

    target = "attendance_avg"

    # Drop rows with missing values in relevant columns
    model_df = df.dropna(subset=[
        'season_year',
        'home_wins',
        'Ticket_Price',
        'attendance_avg'
    ]).copy()

    # Prepare the model variables
    y = model_df[target]
    X = model_df[['home_wins', 'Ticket_Price', 'season_year']].copy()
    X['log_home_wins'] = np.log1p(model_df['home_wins'])
    X = sm.add_constant(X[['log_home_wins', 'Ticket_Price', 'season_year']])
    run_ols_and_plot_residuals(X, y, "Financial Attendance Residuals", "financial_attendance_residuals")


if __name__ == "__main__":
    do_attendance_modeling()
