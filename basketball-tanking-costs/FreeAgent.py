import sqlite3
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import ScalarFormatter
from General import pretty_print_df, save_plot
from NbaData import getCustomSqlTable
from Paths import FILE_PATH_TO_COMPILED_DATA
import pandas as pd
from TankLog import TankLog


def compute_team_lagging_averages(df, cols, windows=None):
    """
    Compute rolling lagging averages for specified columns grouped by franchise and year.

    Args:
        df (pd.DataFrame): The input DataFrame containing team season records.
        cols (list of str): The column names to compute lagged averages for.
        windows (list of int, optional): The window sizes for rolling means. Defaults to None and becomes [1, 2, 4, 6].

    Returns:
        pd.DataFrame: The DataFrame with new lagging average columns added.
    """
    if windows is None:
        windows = [1, 2, 4, 6]
    df = df.sort_values(['franchise_id', 'season_year'])
    for col in cols:
        for w in windows:
            col_name = f'Lagging_{col}_{w}Y'
            df[col_name] = (
                df
                .groupby('franchise_id')[col]
                .shift(1)
                .rolling(window=w, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
    return df


def get_player_records():
    """
    Retrieve the full player record table from the SQL database.

    Returns:
        pd.DataFrame: A DataFrame containing all player records with salary and performance data.
    """
    conn = sqlite3.connect(FILE_PATH_TO_COMPILED_DATA + 'nba_data.db')
    cursor = conn.cursor()
    player_records_df_columns = [
        "player_id", "Player", "Rank", "Year Drafted", "Age", "Team",
        "MP RS", "OWS RS", "DWS RS", "WS RS", "WS/48 RS", "Year",
        "MP PO", "OWS PO", "DWS PO", "WS PO", "WS/48 PO", "Impact",
        "Year Started", 'franchise_id', 'teams_played_for',
        'salary','allocated_salary',
        'MP_Total','MP_RS_Cost','MP_TOT_Cost','WS_RS_Cost','WS_TOT_Cost','Impact_Cost'
    ]
    player_records_df = getCustomSqlTable(cursor, 'SELECT * FROM player_records',
                                          column_names=player_records_df_columns)
    conn.close()
    return player_records_df


def get_team_season_records(write_file=True):
    """
    Retrieve team season-level data and optionally save to disk.

    Args:
        write_file (bool): If True, saves the result as CSV. Defaults to True.

    Returns:
        pd.DataFrame: A DataFrame containing team season performance metrics.
    """
    conn = sqlite3.connect(FILE_PATH_TO_COMPILED_DATA + 'nba_data.db')
    cursor = conn.cursor()
    team_season_records_df_columns = [
        "franchise_id", "Tm", "Team", "Year", "Wins", "Losses", "Pct",
        "Wins Finals", "Losses Finals", "Wins Conference Finals", "Losses Conference Finals",
        "Wins Semifinals", "Losses Semifinals", "Wins First Round", "Losses First Round",
        "season_performance", "draft_power", "adjusted_year", "adjusted_year2", "adjusted_year3",
        "adjusted_log_year", "Payroll", "Total Expenses", "win_cost", "performance_cost",
        "draft_rankings_info", "WS_Total", "MP_Total", "WS_Playoff_Total", "MP_Playoff_Total",
        "WS_PER_48", "Playoff_WS_PER_48", "estimated_season_performance"
    ]
    team_season_records_df = getCustomSqlTable(cursor, 'SELECT * FROM combined_season',
                                          column_names=team_season_records_df_columns)
    conn.close()
    if write_file:
        team_season_records_df.to_csv(FILE_PATH_TO_COMPILED_DATA + 'nba_player_team_season_records.csv', index=False)
    return team_season_records_df


def get_cleaned_player_records(player_records_df):
    """
    Clean player records by removing NaNs and filtering out rookie-scale contracts.

    Args:
        player_records_df (pd.DataFrame): The raw player data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Two DataFrames:
            - All cleaned players
            - Only those not on rookie-scale deals
    """
    # Drop rows with NaNs in critical fields
    cleaned_df = player_records_df.dropna(subset=[
        'salary', 'allocated_salary', 'MP_Total', 'MP_RS_Cost', 'MP_TOT_Cost',
        'WS_RS_Cost', 'WS_TOT_Cost', 'Impact_Cost'
    ]).copy()

    # Convert 'Rank' and 'Year Drafted' to integers
    cleaned_df['Rank'] = cleaned_df['Rank'].astype(int)
    cleaned_df['Year Drafted'] = cleaned_df['Year Drafted'].astype(int)
    cleaned_df['season_year'] = cleaned_df['season_year'].astype(int)

    # Add 'Rookie Contract Year' = Year - Year Drafted + 1
    cleaned_df['Rookie Contract Year'] = cleaned_df['season_year'] - cleaned_df['Year Drafted'] + 1

    # Identify players who were first-round picks in 1996 or later
    is_first_round = (cleaned_df['Rank'] >= 1) & (cleaned_df['Rank'] <= 30)
    is_after_rookie_scale = cleaned_df['Year Drafted'] >= 1996
    is_rookie_contract = (cleaned_df['Rookie Contract Year'] >= 1) & (cleaned_df['Rookie Contract Year'] <= 4)

    # Remove drafted? If on rookie scale deal give option to remove (default)
    # Keep rows that are:
    # - NOT first-round post-1995
    # - OR outside first 4 years of rookie scale

    not_on_rookie_scale_deal_df = cleaned_df[~(is_first_round & is_after_rookie_scale & is_rookie_contract)].copy()

    # Optional: export the result
    cleaned_df.to_csv(FILE_PATH_TO_COMPILED_DATA + 'nba_player_cleaned.csv', index=False)
    not_on_rookie_scale_deal_df.to_csv(FILE_PATH_TO_COMPILED_DATA + 'nba_player_cleaned_not_on_rookie.csv', index=False)

    return cleaned_df, not_on_rookie_scale_deal_df


def generate_team_lagging_data(team_season_records_df, write_file=True):
    """
    Generate lagging metrics for team performance and optionally export the result.

    Args:
        team_season_records_df (pd.DataFrame): Raw team season data.
        write_file (bool): Whether to write the output to disk. Defaults to True.

    Returns:
        pd.DataFrame: Lagging-enhanced version of team season data.
    """
    # Columns we want to compute lagging averages for
    lag_columns = ['Pct', 'draft_power', 'estimated_season_performance']

    # Rolling windows
    rolling_windows = [1, 2, 4, 6]

    # Add the new columns to team_season_records_df
    team_season_records_df = add_lagging_averages(
        df=team_season_records_df,
        group_col='franchise_id',
        year_col='season_year',
        target_cols=lag_columns,
        windows=rolling_windows
    )

    if write_file:
        team_season_records_df.to_csv(FILE_PATH_TO_COMPILED_DATA + 'nba_player_team_season_records_with_lagging.csv',
                                      index=False)
    # print some records to log (turn on INFO_LOGGING <- default is off)
    TankLog.get_shared_logger().log(TankLog.INFO_LOGGING,
                                    pretty_print_df(team_season_records_df, rows=20))
    return team_season_records_df


def generate_player_lagging_data(player_records_df):
    """
    Add lagging efficiency cost metrics to player records.

    Args:
        player_records_df (pd.DataFrame): Cleaned player records.

    Returns:
        pd.DataFrame: Player data with new lagging efficiency columns.
    """
    player_value_cols = ["WS_RS_Cost", "Impact_Cost"]
    player_records_with_lags_df = add_lagging_player_averages(player_records_df, player_value_cols)
    # print some records to log (turn on INFO_LOGGING <- default is off)
    TankLog.get_shared_logger().log(TankLog.INFO_LOGGING,
                                    pretty_print_df(player_records_with_lags_df, rows=20))
    return player_records_with_lags_df


def add_lagging_averages(df, group_col, year_col, target_cols, windows, suffix_prefix="Lagging"):
    def add_lagging_averages(df, group_col, year_col, target_cols, windows, suffix_prefix="Lagging"):
        """
        Adds rolling average (lagging) columns for specified metrics across time windows.

        For each target column and rolling window, a new column is added to the DataFrame
        representing the average value over the past `window` seasons, excluding the current one.
        If fewer than `window` prior values exist, padding is applied using the overall median.

        Args:
            df (pd.DataFrame): Input DataFrame containing historical records.
            group_col (str): Column name to group by (e.g., 'franchise_id').
            year_col (str): Column name indicating temporal order (e.g., 'season_year').
            target_cols (list[str]): List of column names to compute lagged averages for.
            windows (list[int]): List of window sizes (in years) to apply.
            suffix_prefix (str): Prefix for generated lagging column names.

        Returns:
            pd.DataFrame: A new DataFrame including lagging columns for each target variable.

        Example:
            Lagging_pct_2Y = average of prior 2 seasons' win percentages.
        """
    df_sorted = df.sort_values(by=[group_col, year_col]).copy()

    for col in target_cols:
        median_val = df_sorted[col].median()

        for window in windows:
            new_col = f"{suffix_prefix}_{col}_{window}Y"

            # Function applied per group
            def padded_rolling(group):
                # compute rolling mean with min_periods=1 to avoid NaN
                rolling = group[col].shift(1).rolling(window=window, min_periods=1).mean()

                # Fill where there are not enough previous years
                count_prior_years = group[col].expanding().count().shift(1)
                rolling[count_prior_years < window] = (
                    (rolling * count_prior_years + (window - count_prior_years) * median_val) / window
                )

                return rolling

            df_sorted[new_col] = (
                df_sorted[[year_col, col]]  # exclude group_col here
                .groupby(df_sorted[group_col], group_keys=False)
                .apply(padded_rolling)
                .reset_index(drop=True)
            )

    return df_sorted


def add_lagging_player_averages(df: pd.DataFrame, value_columns: list, years=[1, 2, 3]):
    """
    Computes rolling (lagging) averages of player statistics across seasons.

    For each player and value column, calculates the rolling mean across the past `k` seasons,
    excluding the current season. If a player has fewer than `k` prior seasons, the result is
    padded with their personal median for that stat to avoid NaNs.

    Args:
        df (pd.DataFrame): Input DataFrame containing player-season-level data.
        value_columns (list[str]): Columns to compute lagged averages for (e.g., ['WS_RS_Cost']).
        years (list[int]): List of lagging windows to apply (e.g., [1, 2, 3]).

    Returns:
        pd.DataFrame: The original DataFrame with additional lag columns added.

    Notes:
        - Columns are named using the format: Lag_<column_name>_<window>Y
        - Player-specific medians are used to fill early seasons lacking sufficient history.
    """
    df = df.sort_values(by=['player_id', 'season_year']).copy()

    # Calculate medians for padding
    player_medians = df.groupby('player_id')[value_columns].median().reset_index()
    player_medians.columns = ['player_id'] + [f"median_{col}" for col in value_columns]
    df = df.merge(player_medians, on='player_id', how='left')

    result_df = df.copy()

    for window in years:
        for col in value_columns:
            lag_col_name = f"Lag_{col}_{window}Y"

            def compute_lag(group):
                group = group.sort_values('season_year').copy()
                values = group[col].shift(1)  # exclude current year
                rolling = values.rolling(window=window, min_periods=1).mean()

                median_value = group[f"median_{col}"].iloc[0]
                group[lag_col_name] = rolling.fillna(median_value)
                return group[[lag_col_name]]

            lagged = df.groupby('player_id', group_keys=False)[['season_year', col, f"median_{col}"]].apply(
                compute_lag).reset_index(drop=True)
            result_df[lag_col_name] = lagged[lag_col_name].values

    # Clean up
    median_cols = [f"median_{col}" for col in value_columns]
    result_df = result_df.drop(columns=median_cols)

    return result_df


def generate_team_efficiency_records(cleaned_player_df_with_lags):
    """
    Aggregate player cost-efficiency data at the team-season level.

    Add efficiency data.

    1. Average MP_RS_COST, MP_TOT_COST, WS_RS_COST, WS_TOT_Cost, Impact_Cost
    2. Grouping the player_records using franchise_id, Year <- Year in this case is the Season-Year. (2023-2024 = 2024)
    3. Write these mean() columns: MP_RS_AVG_COST, MP_TOT_AVG_COST, WS_RS_AVG_COST, WS_TOT_AVG_Cost, Impact_Avg_Cost

    Args:
        cleaned_player_df_with_lags (pd.DataFrame): Lagged player metrics per season.

    Returns:
        pd.DataFrame: Team-level efficiency metrics with lagging values.
    """

    # Define efficiency columns to aggregate and roll
    efficiency_cols = [
        'MP_RS_Cost', 'MP_TOT_Cost', 'WS_RS_Cost', 'WS_TOT_Cost', 'Impact_Cost'
    ]

    # Group and aggregate mean efficiency values by franchise and year
    team_efficiency_df = (
        cleaned_player_df_with_lags.groupby(['franchise_id', 'season_year'])[efficiency_cols].mean().reset_index())

    # Rename to standard column names
    rename_dict = {
        'MP_RS_Cost': 'MP_RS_AVG_COST',
        'MP_TOT_Cost': 'MP_TOT_AVG_COST',
        'WS_RS_Cost': 'WS_RS_AVG_COST',
        'WS_TOT_Cost': 'WS_TOT_AVG_COST',
        'Impact_Cost': 'Impact_AVG_COST'
    }
    team_efficiency_df.rename(columns=rename_dict, inplace=True)

    # Compute rolling averages for 1Y, 2Y, 4Y, and 6Y
    windows = [1, 2, 4, 6]
    for col in rename_dict.values():
        for window in windows:
            lag_col = f"Lagging_{col}_{window}Y"
            rolling_df = (
                team_efficiency_df
                .sort_values(['franchise_id', 'season_year'])
                .groupby('franchise_id')[col]
                .shift(1)  # Exclude current year
                .groupby(team_efficiency_df['franchise_id'])
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
            team_efficiency_df[lag_col] = rolling_df

    # These values rank player performance versus their cost.
    efficiency_metrics = [
        'MP_RS_Cost', 'MP_TOT_Cost', 'WS_RS_Cost', 'WS_TOT_Cost', 'Impact_Cost'
    ]
    efficiency_grouped = (
        cleaned_player_df_with_lags.groupby(['franchise_id', 'season_year'])[efficiency_metrics].mean().reset_index())
    efficiency_grouped.rename(columns={
        'MP_RS_Cost': 'MP_RS_AVG_COST',
        'MP_TOT_Cost': 'MP_TOT_AVG_COST',
        'WS_RS_Cost': 'WS_RS_AVG_COST',
        'WS_TOT_Cost': 'WS_TOT_AVG_COST',
        'Impact_Cost': 'Impact_AVG_COST'
    }, inplace=True)
    # calculate lagging values for team efficiency values
    efficiency_lagged_df = compute_team_lagging_averages(efficiency_grouped, [
        'MP_RS_AVG_COST', 'MP_TOT_AVG_COST',
        'WS_RS_AVG_COST', 'WS_TOT_AVG_COST',
        'Impact_AVG_COST'
    ])
    return efficiency_lagged_df


def generate_efficiency_table():
    """
    End-to-end pipeline to generate full team and player efficiency tables,
    including rookie vs non-rookie filtered views.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Full and non-rookie team efficiency tables.
    """
    # query sql table.
    player_records_df = get_player_records()
    team_season_records_df = get_team_season_records()

    player_records_df.rename(columns={'Year': 'season_year'}, inplace=True)
    team_season_records_df.rename(columns={'Year': 'season_year'}, inplace=True)

    # remove nans and drafted players (only first four seasons).
    clean_player_records_df, not_on_rookie_scale_df = get_cleaned_player_records(player_records_df)

    # calculate lagging values.
    lagging_player_records_not_on_rookie_scale_df = generate_player_lagging_data(not_on_rookie_scale_df)
    lagging_player_records_df = generate_player_lagging_data(clean_player_records_df)
    lagging_team_season_records_df = generate_team_lagging_data(team_season_records_df)

    # calculate the team summaries of player efficiencies.
    team_efficiency_records_df = generate_team_efficiency_records(lagging_player_records_df)
    team_efficiency_records_not_on_rookie_scale_df = (
        generate_team_efficiency_records(lagging_player_records_not_on_rookie_scale_df))

    # Merge lagged efficiency data into the main team_season_df
    merged_df = pd.merge(lagging_team_season_records_df, team_efficiency_records_df,
                         on=['franchise_id', 'season_year'], how='left')
    merged_not_on_rookie_scale_df = pd.merge(lagging_team_season_records_df,
                                             team_efficiency_records_not_on_rookie_scale_df,
                                             on=['franchise_id', 'season_year'], how='left')
    return merged_df, merged_not_on_rookie_scale_df


def plot_free_agency_efficiency(free_agency_performance_df, player_column_name='', team_column_name='', hint=''):
    """
    Plot scatter + trend line and histogram of efficiency vs performance.

    Args:
        free_agency_performance_df (pd.DataFrame): Data to plot.
        player_column_name (str): Column name for X-axis.
        team_column_name (str): Column name for Y-axis.
        hint (str): Optional label for context in plot title.
    """
    # Scatter plot
    x = free_agency_performance_df[player_column_name]
    y = free_agency_performance_df[team_column_name]

    # Fit linear regression to observe convergence or divergence
    model = LinearRegression()
    x_reshape = x.values.reshape(-1, 1)
    model.fit(x_reshape, y)
    line = model.predict(x_reshape)

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.5, label='Teams')
    plt.plot(x, line, color='red', label='Trend Line')
    title = f'{player_column_name} vs {team_column_name} - {hint}'
    plt.title(title)
    plt.xlabel(player_column_name)
    plt.ylabel(team_column_name)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    save_plot(plt, title + ".csv")
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.hist(free_agency_performance_df[player_column_name].dropna(), bins=30, color='blue', alpha=0.7)
    plt.xlabel(f'{player_column_name}')
    plt.ylabel('Frequency')
    title = f'Histogram of {player_column_name} - {hint}'
    plt.title(title)
    plt.grid(True)

    # Apply plain number formatting on x-axis
    ax = plt.gca()
    ax.xaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style='plain', axis='x')  # Disables scientific notation

    plt.tight_layout()
    save_plot(plt, title + ".csv")
    plt.show()


def show_most_effective_players(players_df):
    """
    Return the top 20 most effective players based on 'Impact'.

    Args:
        players_df (pd.DataFrame): DataFrame containing cleaned player performance data.

    Returns:
        pd.DataFrame: Sorted top 20 players by total impact.
    """
    # Corrected column list based on actual column names (these change later)
    columns_to_display = [
        'player_id', 'Player', 'Rank', 'Year Drafted', 'Age', 'Team', 'MP RS', 'OWS RS', 'DWS RS',
        'WS RS', 'WS/48 RS', 'season_year', 'MP PO', 'OWS PO', 'DWS PO', 'WS PO', 'WS/48 PO', 'Impact',
        'Year Started', 'franchise_id', 'teams_played_for', 'salary', 'allocated_salary', 'MP_Total',
        'MP_RS_Cost', 'MP_TOT_Cost', 'WS_RS_Cost', 'WS_TOT_Cost', 'Impact_Cost', 'Rookie Contract Year'
    ]
    # Sort and display top 20 by Impact
    top_impact_players_df = players_df.sort_values(by='Impact', ascending=False)[columns_to_display].head(20)
    return top_impact_players_df


def do_free_agent_calculations():
    """
    Run the entire free agency analysis pipeline, including visualizations.
    """
    efficiency_table_df, not_on_rookie_scale_efficiency_table_df = generate_efficiency_table()
    # Drop rows with missing values for plotting
    plot_df = efficiency_table_df.dropna(subset=[
        'Lagging_Impact_AVG_COST_2Y',
        'Lagging_estimated_season_performance_2Y',
        'Lagging_Impact_AVG_COST_6Y',
        'Lagging_estimated_season_performance_6Y'
    ])
    plot_not_on_rookie_scale_df = not_on_rookie_scale_efficiency_table_df.dropna(subset=[
        'Lagging_Impact_AVG_COST_2Y',
        'Lagging_estimated_season_performance_2Y',
        'Lagging_Impact_AVG_COST_6Y',
        'Lagging_estimated_season_performance_6Y'
    ])
    plot_column_name_pairs = [
        ['Lagging_Impact_AVG_COST_2Y', 'Lagging_estimated_season_performance_2Y'],
        ['Lagging_Impact_AVG_COST_6Y', 'Lagging_estimated_season_performance_6Y']
    ]

    for plot_player_column_name, plot_team_column_name in plot_column_name_pairs:
        plot_free_agency_efficiency(plot_df, player_column_name=plot_player_column_name,
                                    team_column_name=plot_team_column_name, hint="All Players")
        plot_free_agency_efficiency(plot_not_on_rookie_scale_df, player_column_name=plot_player_column_name,
                                    team_column_name=plot_team_column_name, hint="All Players Not On Rookie Scale")


if __name__ == '__main__':
    do_free_agent_calculations()


