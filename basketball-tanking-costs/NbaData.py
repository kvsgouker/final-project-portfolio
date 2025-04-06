"""
NBA SQL Table Inspection and Sample Query Viewer

This module provides utilities to access, inspect, and test various tables
in the NBA SQLite database. It includes:

- SQL query wrappers for fetching and formatting data from SQLite.
- Functions for generating lagging (rolling average) values over time.
- A comprehensive test suite that queries and prints schemas and rows
  from key tables including drafts, player stats, playoff performance,
  and combined team seasons.
- Tools to clean SQL tables (e.g., drop columns).

Intended use:
- Debugging, verifying SQL content and structure.
- Performing exploratory data analysis from the database.
- Assisting developers in maintaining schema consistency.
"""
import sqlite3
import pandas as pd
from tabulate import tabulate
from General import printFormattedTestStat, printCurrencyFormattedTestStat
from Paths import FILE_PATH_TO_COMPILED_DATA


calculated_columns = ['WS_PER_48', 'Playoff_WS_PER_48', 'WS_Total', 'MP_Total', 'WS_Playoff_Total', 'MP_Playoff_Total', 'estimated_season_performance']
currency_columns = ['Payroll', 'Total Expenses', 'win_cost', 'performance_cost']


def getCustomSqlTable(cursor, request, column_names=None):
    """
    Executes a SQL query and returns a formatted DataFrame with selected columns.

    Args:
        cursor (sqlite3.Cursor): Database cursor used to execute the query.
        request (str): SQL query string.
        column_names (list[str], optional): List of columns to include in the resulting DataFrame.
            If None, all columns from the query are included.

    Returns:
        pd.DataFrame: A DataFrame containing the selected query results.
    """
    cursor.execute(request)
    test_data = cursor.fetchall()
    if column_names is None:
        column_names = [description[0] for description in cursor.description]
    test_df = pd.DataFrame(test_data, columns=[description[0] for description in cursor.description])
    selected_columns = [col for col in column_names if col in test_df.columns]
    formatted_df = test_df[selected_columns].copy()
    return formatted_df


def testSqlAccess(cursor, request, title, column_names=None, hdr=None):
    """
    Executes a SQL query, formats selected columns, and prints results in a readable table.

    Args:
        cursor (sqlite3.Cursor): Database cursor used to execute the query.
        request (str): SQL query string.
        title (str): Title to display before the printed table.
        column_names (list[str], optional): Columns to include from the result set.
        hdr (list[str], optional): Custom headers to use in the printed table. If None, uses column_names.

    Returns:
        pd.DataFrame: A formatted DataFrame of the query results with specified formatting.
    """
    cursor.execute(request)
    test_data = cursor.fetchall()
    if column_names is None:
        column_names = [description[0] for description in cursor.description]
    test_df = pd.DataFrame(test_data, columns=[description[0] for description in cursor.description])
    selected_columns = [col for col in column_names if col in test_df.columns]
    if hdr != None:
        headers = hdr
    else:
        headers = selected_columns
    formatted_df = test_df[selected_columns].copy()
    for col in selected_columns:
        if col in calculated_columns:
            formatted_df[col] = formatted_df[col].map(lambda x: printFormattedTestStat(x))
        if col in currency_columns:
            formatted_df[col] = formatted_df[col].map(lambda x: printCurrencyFormattedTestStat(x))

    print("\n" + title + "\n")
    print(tabulate(formatted_df, headers=headers, tablefmt='psql', showindex=False))
    return formatted_df


def drop_column_from_table(cursor, table_name, column_to_remove):
    """
    Removes a column from an existing SQLite table by rebuilding the table without it.

    Args:
        cursor (sqlite3.Cursor): Database cursor to perform table modification.
        table_name (str): Name of the table to modify.
        column_to_remove (str): Name of the column to drop.

    Raises:
        ValueError: If the specified column does not exist in the table.

    Side Effects:
        - Replaces the original table with a new one lacking the specified column.
        - Prints status messages about the operation.
    """
    # Step 1: Get current columns
    cursor.execute(f"PRAGMA table_info({table_name});")
    all_columns_info = cursor.fetchall()
    all_columns = [col[1] for col in all_columns_info]

    if column_to_remove not in all_columns:
        raise ValueError(f"Column '{column_to_remove}' not found in table '{table_name}'.")

    # Step 2: Build list of remaining columns
    remaining_columns = [col for col in all_columns if col != column_to_remove]
    select_columns_sql = ", ".join([f'"{col}"' for col in remaining_columns])

    # Step 3: Build SQL statements
    temp_table = f"{table_name}_new"

    create_sql = f"""
    CREATE TABLE {temp_table} AS
    SELECT {select_columns_sql}
    FROM {table_name};
    """

    drop_sql = f"DROP TABLE {table_name};"
    rename_sql = f"ALTER TABLE {temp_table} RENAME TO {table_name};"

    # Step 4: Execute SQL
    print("[INFO] Dropping column:", column_to_remove)
    cursor.executescript(create_sql + drop_sql + rename_sql)
    print(f"[SUCCESS] Column '{column_to_remove}' dropped from '{table_name}'.")


def test_nba_sql_tables_access():
    """
    Connects to the NBA SQLite database and performs a comprehensive schema
    and content inspection across key tables.

    Operations:
        - Connects to the `nba_data.db` SQLite database.
        - Lists all table names and prints their schema using `PRAGMA table_info`.
        - Performs test queries (via `testSqlAccess`) on multiple tables, including:
            - `player_info`, `all_drafts`, `regular_seasons`, `all_playoff`
            - `per_game_stats`, `total_stats`, `advanced_stats`
            - `playoff_per_game_stats`, `playoff_total_stats`, `playoff_advanced_stats`
            - `combined_season`, `team_salaries`, `player_records`
        - Selects subsets of player and team metrics with formatting applied.
        - Outputs tables as tabulated previews for quick inspection.
        - Saves no data but prints helpful summaries and formatted rows.

    Returns:
        None. The function logs and prints output to console.

    Example Usage:
        Run this module directly to inspect database content:
            `python Tables.py`
    """
    # Connect to the database
    conn = sqlite3.connect(FILE_PATH_TO_COMPILED_DATA+'nba_data.db')

    # Query the tables
    cursor = conn.cursor()

    # Get the list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]

    # Extract schema for each table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        schema_info = cursor.fetchall()
        schema_df = pd.DataFrame(schema_info, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])

        print(f"\nSchema for table: {table}")
        print(tabulate(schema_df, headers='keys', tablefmt='psql', showindex=False))

    # Query each table. Show the first records of each query in a table.
    player_info_columns_pg1 = ["Player", "player_id", "Birthdate", "Height", "Weight", "Position", "Shoots"]
    player_info_columns_pg2 = ["Player", "College", "Yrs", "Team", "Rank", "Year"]
    testSqlAccess(cursor, "SELECT * FROM player_info LIMIT 5", "Player Info #1", column_names = player_info_columns_pg1)
    testSqlAccess(cursor, "SELECT * FROM player_info LIMIT 5", "Player Info #2", column_names = player_info_columns_pg2)

    all_draft_columns = ['Player', 'Year', 'Rank', 'Tm', 'Team', 'Yrs', 'G', 'MP', 'WS', 'WS/48']
    testSqlAccess(cursor, "SELECT * FROM all_drafts LIMIT 5", "All Drafts", column_names = all_draft_columns)

    testSqlAccess(cursor, "SELECT * FROM draft_summary LIMIT 5", "Draft Summary")
    testSqlAccess(cursor, "SELECT * FROM regular_seasons LIMIT 5", "All Regular Seasons")
    testSqlAccess(cursor, "SELECT * FROM all_playoff LIMIT 5", "All Playoffs")

    player_stats_col_pg1 = ['player_id', 'Age', 'Season', 'Year', 'Tm', 'Team', 'Lg', 'Pos', 'G', 'GS']
    player_stats_col_pg2 = ['player_id', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%']
    player_stats_col_pg3 = ['player_id', 'eFG%', 'FT', 'FTA', 'FT%', 'PTS', 'Trp-Dbl']
    player_stats_col_pg4 = ['player_id', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK,' 'TOV', 'PF']

    testSqlAccess(cursor, "SELECT * FROM per_game_stats LIMIT 5", "Per Game #1", column_names = player_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM per_game_stats LIMIT 5", "Per Game #2", column_names = player_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM per_game_stats LIMIT 5", "Per Game #3", column_names = player_stats_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM per_game_stats LIMIT 5", "Per Game #4", column_names = player_stats_col_pg4)

    testSqlAccess(cursor, "SELECT * FROM total_stats LIMIT 5", "Totals #1", column_names = player_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM total_stats LIMIT 5", "Totals #2", column_names = player_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM total_stats LIMIT 5", "Totals #3", column_names = player_stats_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM total_stats LIMIT 5", "Totals #4", column_names = player_stats_col_pg4)

    adv_stats_col_pg1 = ['player_id', 'Age', 'Season', 'Year', 'Tm', 'Team', 'Lg', 'Pos', 'G', 'MP']
    adv_stats_col_pg2 = ['player_id', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%']
    adv_stats_col_pg3 = ['player_id', 'USG%', 'OWS', 'DWS', 'WS', 'WS/48', 'OBPM', 'DBPM', 'BPM', 'VORB', 'PER']

    testSqlAccess(cursor, "SELECT * FROM advanced_stats LIMIT 5", "Advanced #1", column_names = adv_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM advanced_stats LIMIT 5", "Advanced #2", column_names = adv_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM advanced_stats LIMIT 5", "Advanced #3", column_names = adv_stats_col_pg3)

    testSqlAccess(cursor, "SELECT * FROM playoff_per_game_stats LIMIT 5", "Playoffs Per Game #1", column_names = player_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM playoff_per_game_stats LIMIT 5", "Playoffs Per Game #2", column_names = player_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM playoff_per_game_stats LIMIT 5", "Playoffs Per Game #3", column_names = player_stats_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM playoff_per_game_stats LIMIT 5", "Playoffs Per Game #4", column_names = player_stats_col_pg4)

    testSqlAccess(cursor, "SELECT * FROM playoff_total_stats LIMIT 5", "Playoffs Totals #1", column_names = player_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM playoff_total_stats LIMIT 5", "Playoffs Totals #2", column_names = player_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM playoff_total_stats LIMIT 5", "Playoffs Totals #3", column_names = player_stats_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM playoff_total_stats LIMIT 5", "Playoffs Totals #4", column_names = player_stats_col_pg4)

    testSqlAccess(cursor, "SELECT * FROM playoff_advanced_stats LIMIT 5", "Playoffs Advanced #1", column_names = adv_stats_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM playoff_advanced_stats LIMIT 5", "Playoffs Advanced #2", column_names = adv_stats_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM playoff_advanced_stats LIMIT 5", "Playoffs Advanced #3", column_names = adv_stats_col_pg3)

    combined_col_pg1 = ['Team', 'Tm', 'franchise_id', 'Year', 'season_performance', 'Wins', 'Losses', 'Pct']
    combined_col_pg2 = ['Team', 'Year', 'Wins Finals', 'Losses Finals', 'Wins Conference Finals', 'Losses Conference Finals']
    combined_col_pg3 = ['Team', 'Year', 'Wins Semifinals', 'Losses Semifinals', 'Wins First Round', 'Losses First Round', ]
    combined_col_pg4 = ['Team', 'Year', 'draft_power', 'draft_rankings_info', 'WS_PER_48', 'Playoff_WS_PER_48']
    combined_col_pg5 = ['Team', 'Year', 'WS_Total', 'MP_Total', 'WS_Playoff_Total', 'MP_Playoff_Total']
    combined_col_pg6 = ['Team', 'Year', 'Payroll', 'Total Expenses', 'win_cost', 'estimated_season_performance', 'performance_cost']
    combined_col_pg7 = ['Team', 'Year', 'season_performance', 'WS_Total', 'WS_Playoff_Total', 'estimated_season_performance']
    combined_col_pg8 = ['Team', 'Year', 'draft_power', 'draft_rankings_info']

    hdr_pg6 = ['Team', 'Year', 'Payroll', 'Expenses', 'win_cost', 'Season Perf (est)', 'performance_cost']
    hdr_pg7 = ['Team', 'Year', 'Season Performance (real)', 'WS Total', 'WS Playoff Total', 'Season Performance (est)']

    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #1", column_names = combined_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #2", column_names = combined_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #3", column_names = combined_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #4", column_names = combined_col_pg4)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #5", column_names = combined_col_pg5)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #6", column_names = combined_col_pg6, hdr = hdr_pg6)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Tm = 'MIA'", "Combined Season #7", column_names = combined_col_pg7, hdr = hdr_pg7)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year>=2017 ORDER BY draft_power DESC", "Draft Power by Season 2017-2023", column_names = combined_col_pg8)

    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #1", column_names = combined_col_pg1)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #2", column_names = combined_col_pg2)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #3", column_names = combined_col_pg3)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #4", column_names = combined_col_pg4)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #5", column_names = combined_col_pg5)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #6", column_names = combined_col_pg6, hdr = hdr_pg6)
    testSqlAccess(cursor, "SELECT * FROM combined_season WHERE Year = '2022'", "Combined Season #7", column_names = combined_col_pg7, hdr = hdr_pg7)


    testSqlAccess(cursor, "SELECT * FROM team_salaries LIMIT 5", "Team Salaries")
    testSqlAccess(cursor, "SELECT * FROM all_drafts WHERE Year=2013", "Year 2013 from All Drafts", column_names = all_draft_columns)
    sample_df = testSqlAccess(cursor, "SELECT * FROM all_drafts WHERE Rank=6 or Player='Tyler Herro' ORDER BY WS/48", "Pick 6 from last 43 Drafts", column_names = all_draft_columns)

    sample_df = sample_df.sort_values(by=['WS/48'])
    print("\n" + "Pick 6 from last 43 Drafts" + "\n")
    print(tabulate(sample_df, headers=all_draft_columns, tablefmt='psql', showindex=False))

    sample_df = testSqlAccess(cursor, "SELECT * FROM player_records")

    # Close the cursor and connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_nba_sql_tables_access()