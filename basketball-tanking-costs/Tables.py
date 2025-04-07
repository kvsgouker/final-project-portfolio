import os
import sqlite3

from tabulate import tabulate

from General import show_df_info
# GAMES subfolder is not necessary for final version
# GAMES subfolder is important for preprocessing, so uncomment when regenning.
from Paths import FILE_PATH_TO_GAMES_DATA, FILE_PATH_TO_COMPILED_DATA
import pandas as pd


def add_lagged_features(df, group_col, time_col, columns_to_lag, lags):
    """
    Adds lagged versions of specified columns.

    Parameters:
        df (pd.DataFrame): Input dataframe.
        group_col (str): Column to group by (e.g., 'franchise_id').
        time_col (str): Column representing time (e.g., 'season_year').
        columns_to_lag (list of str): List of columns to lag.
        lags (list of int): List of lag periods (e.g., [1, 2, 4, 6]).

    Returns:
        pd.DataFrame: DataFrame with lagged columns added.
    """
    df = df.copy()
    df = df.sort_values(by=[group_col, time_col])

    for col in columns_to_lag:
        for lag in lags:
            lagged_col_name = f"{col}_lag{lag}"
            df[lagged_col_name] = df.groupby(group_col)[col].shift(lag)

    return df


def load_team_revenue():
    """
    This data is sourced from a published JP Morgan research document:
        https://assets.jpmprivatebank.com/content/dam/jpm-pb-aem/global/en/documents/eotm/a-piece-of-the-action.pdf

    Returns:
         dataframe: Dataframe with team-revenue data.
    """
    team_revenue_dtypes = dict(Team="string", season_year="Int64",
                               Team_Revenue="Float64", Ticket_Price="Float64", Operating_Income="Float64",
                               franchise_id="Int64"
                        )
    # Add Table for Game by Game info.
    team_revenue_path = os.path.join(FILE_PATH_TO_COMPILED_DATA, "TeamRevenueUpdated.csv")
    team_revenue_df = pd.read_csv(
        team_revenue_path,
        dtype=team_revenue_dtypes
    )
    return team_revenue_df


def load_team_mapping():
    """
    Loads the team mapping table, which links franchise identifiers to team names,
    abbreviations, cities, and active year ranges.

    Returns:
        pd.DataFrame: A DataFrame with correct data types for franchise lookup.
    """
    team_mapping_path = FILE_PATH_TO_COMPILED_DATA + 'team_mapping.csv'

    team_mapping_dtypes = dict(
        Team="string",                  # Full name like "Atlanta Hawks"
        City="string",                 # City like "Atlanta"
        **{
            "Beginning-Year": "Int64",  # Starting year of the franchise
            "Ending-Year": "Int64",     # Ending year (use FINAL_YEAR+1 for active teams)
            "Abbreviation": "string",   # Abbreviated form, e.g., ATL
            "franchise_id": "Int64",    # Internal franchise ID
            "teamId": "string",         # External team identifier (NBA's internal ID)
            "other_abbreviation": "string"  # Alternate abbreviations (e.g., from other sources)
        }
    )

    team_mapping_df = pd.read_csv(team_mapping_path, dtype=team_mapping_dtypes)
    return team_mapping_df


def load_player_salaries():
    """
    Loads player salary data.

    Returns:
        pd.DataFrame: DataFrame of player salaries.
    """
    player_salary_dtypes = dict(
        team_abbreviation = "string",
        season = "Int64",
        player_name = "string",
        player_link = "string",
        salary = "Float64",
        player_id = "string"
    )
    players_salaries_path = FILE_PATH_TO_COMPILED_DATA + 'player_salaries.csv'
    players_salaries_df = pd.read_csv(players_salaries_path, dtype=player_salary_dtypes)
    return players_salaries_df


def load_league_mapping():
    """
    Loads a league mapping table that indicates the beginning and option end year of a league.
    This is a "foreign" file that we support to get access to the games dataa.

    Returns:
        pd.DataFrame: DataFrame of league mapping.
    """
    league_mapping_dtypes = dict(
        League = "string",
        Beginning = "Int64",
        Ending = "Int64",
    )
    league_mapping_path = FILE_PATH_TO_COMPILED_DATA + 'league_mapping.csv'
    league_mapping_df = pd.read_csv(league_mapping_path)
    return league_mapping_df


def load_extended_game_history():
    """
    Loads an extended game history table which includes lagging pct values.
    This data is for attendance modeling.

    Returns:
        pd.DataFrame: DataFrame of all nba games 40+ years.
    """
    extended_game_history_dtypes = dict(
        gameId="int64",
        gameDate="string",
        gameDuration="string",
        hometeamCity="string",
        hometeamName="string",
        hometeamId="Int64",
        awayteamCity="string",
        awayteamName="string",
        awayteamId="Int64",
        homeScore="Int64",
        awayScore="Int64",
        winner="Int64",
        gameType="string",
        attendance="Int64",
        arenaId="Int64",
        gameLabel="string",
        gameSubLabel="string",
        seriesGameNumber="Int64",
        season_year="Int64",
        home_team_franchise_id="Int64",
        away_team_franchise_id="Int64",
        home_win_flag="int8",
        away_win_flag="int8",
        home_team_last5_win_pct="float64",
        home_team_last10_win_pct="float64",
        home_team_last20_win_pct="float64",
        home_team_last30_win_pct="float64",
        home_team_last40_win_pct="float64",
        home_team_last50_win_pct="float64",
        home_team_last60_win_pct="float64",
        home_team_last70_win_pct="float64",
        home_team_last80_win_pct="float64",
        home_team_last90_win_pct="float64",
        home_team_last100_win_pct="float64"
    )

    # Add Table for Game by Game info.
    games_path = os.path.join(FILE_PATH_TO_COMPILED_DATA, "extended_game_history.csv")
    games_df = pd.read_csv(
        games_path,
        dtype=extended_game_history_dtypes,
        parse_dates=["gameDate"]
    )
    return games_df


# def load_game_with_franchise_id_history():
#     """
#     This is a temporary state of the games data.
#     Use load_extended_game_history() instead.
#
#     Returns:
#         pd.DataFrame: DataFrame of game history including franchise_ids (our keys).
#     """
#     games_with_franchise_id_dtypes = dict(gameId="int64", gameDate="string", gameDuration="string", hometeamId="Int64",
#                         awayteamId="Int64", homeScore="Int64", awayScore="Int64", winner="Int64", arenaId="Int64",
#                         attendance="Int64", gameType="string", gameLabel="string", seriesGameNumber="Int64",
#                         gameSubLabel="string", home_team_franchise_id = "Int64", away_team_franchise_id = "Int64"
#                         )
#
#     # Add Table for Game by Game info.
#     games_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "games_with_franchise_ids.csv")
#     games_df = pd.read_csv(
#         games_path,
#         dtype=games_with_franchise_id_dtypes,
#         parse_dates=["gameDate"]
#     )
#     return games_df
#
#
# def load_game_history():
#     """
#     This is original state of the games data.
#     It has been superseded.
#     Use load_extended_game_history() instead.
#
#     Returns:
#         pd.DataFrame: DataFrame of original game hstory.
#     """
#     games_dtypes = dict(gameId="int64", gameDate="string", gameDuration="string", hometeamId="Int64",
#                         awayteamId="Int64", homeScore="Int64", awayScore="Int64", winner="Int64", arenaId="Int64",
#                         attendance="Int64", gameType="string", gameLabel="string", seriesGameNumber="Int64",
#                         gameSubLabel="string"
#                         )
#     # Add Table for Game by Game info.
#     games_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "games.csv")
#     games_df = pd.read_csv(
#         games_path,
#         dtype=games_dtypes,
#         parse_dates=["gameDate"]
#     )
#     return games_df
#
#
# # This dataframe is for accessing the game history data and does not use our player-id!
# def load_alternative_players_data():
#     """
#     This is original state of the player info data of the games data.
#     The personId, firstName, and lastName are used to identify the players and relate them to our key.
#     You should only use this function if you are doing preprocessing.
#
#     Returns:
#         pd.DataFrame: DataFrame of player info (not stats).
#     """
#
#     alt_players_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "Players.csv")
#     players_dtypes = dict(personId="int64", firstName="string", lastName="string", birthdate="string",
#                           lastAttended="string", country="string", height="Int64", bodyWeight="Int64", guard="boolean",
#                           forward="boolean", center="boolean", draftYear="Int64", draftRound="Int64",
#                           draftNumber="Int64")
#
#     alt_players_df = pd.read_csv(
#         alt_players_path,
#         dtype=players_dtypes,
#         parse_dates=["birthdate"]
#     )
#     return alt_players_df
#
#
# def load_player_performance():
#     """
#     This is original state of the player info data of the games data.
#     I include it just to support the games data files.
#
#     Returns:
#         pd.DataFrame: DataFrame of player stats.
#     """
#
#     players_game_performance_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "PlayerStatistics.csv")
#     player_stats_dtypes = dict(id="int64", personId="int64", gameId="int64", teamId="int64", assists="Int64",
#                                blocks="Int64", fieldGoalsAttempted="Int64", fieldGoalsMade="Int64",
#                                fieldGoalsPercentage="float64", foulsPersonal="Int64", freeThrowsAttempted="string",
#                                freeThrowsMade="string", freeThrowsPercentage="float64", numMinutes="float64",
#                                plusMinusPoints="Int64", points="Int64", reboundsDefensive="Int64",
#                                reboundsOffensive="Int64", reboundsTotal="Int64", steals="Int64",
#                                threePointersAttempted="Int64", threePointersMade="Int64",
#                                threePointersPercentage="float64", turnovers="Int64")
#
#     players_game_performance_df = pd.read_csv(
#         players_game_performance_path,
#         dtype=player_stats_dtypes,
#         low_memory=False
#     )
#
#     # Convert to numeric, coercing bad entries to NaN
#     players_game_performance_df["freeThrowsAttempted"] = pd.to_numeric(players_game_performance_df["freeThrowsAttempted"], errors="coerce")
#     players_game_performance_df["freeThrowsMade"] = pd.to_numeric(players_game_performance_df["freeThrowsMade"], errors="coerce")
#     return players_game_performance_df
#
#
# def load_team_histories_obsolete():
#     """
#     This is team lookup table of the games data.
#     Use team_mapping instead. It has links for team and franchise lookups.
#     This one doesn't even have the franchise_id.
#     This is included for preprocessing, and you may need it to convert files.
#
#     Returns:
#         pd.DataFrame: DataFrame of team history.
#     """
#     team_histories_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "TeamHistories.csv")
#     team_histories_dtypes = dict(teamId="int64", teamCity="string", teamName="string", teamAbbrev = "string",
#                                  seasonFounded = "int64", seasonActiveTill = "int64",
#                                  league = "string")
#
#     team_histories_df = pd.read_csv(
#         team_histories_path,
#         dtype=team_histories_dtypes
#     )
#     return team_histories_df
#
#
# def load_team_performance():
#     """
#     This is team statistics table of the games data.
#
#     Returns:
#         pd.DataFrame: DataFrame of historical team performance stats.
#     """
#     teams_game_performance_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "TeamStatistics.csv")
#     team_stats_dtypes = dict(teamId="int64", gameId="int64", home="boolean", win="boolean", coachId="Int64",
#                              assists="Int64", blocks="Int64", fieldGoalsAttempted="Int64", fieldGoalsMade="Int64",
#                              fieldGoalsPercentage="float64", foulsPersonal="Int64", freeThrowsAttempted="Int64",
#                              freeThrowsMade="Int64", freeThrowsPercentage="float64", numMinutes="float64",
#                              plusMinusPoints="Int64", points="Int64", reboundsDefensive="Int64",
#                              reboundsOffensive="Int64", reboundsTotal="Int64", steals="Int64",
#                              threePointersAttempted="Int64", threePointersMade="Int64",
#                              threePointersPercentage="float64", turnovers="Int64", q1Points="Int64", q2Points="Int64",
#                              q3Points="Int64", q4Points="Int64", benchPoints="Int64", biggestLead="Int64",
#                              biggestScoringRun="Int64", leadChanges="Int64", pointsFastBreak="Int64",
#                              pointsFromTurnovers="Int64", pointsInThePaint="Int64", pointsSecondChance="Int64",
#                              timesTied="Int64", timeoutsRemaining="Int64", seasonWins="Int64", seasonLosses="Int64")
#
#     teams_game_performance_df = pd.read_csv(
#         teams_game_performance_path,
#         dtype=team_stats_dtypes
#     )
#     return teams_game_performance_df


def load_extended_cleaned_player_records(file_path):
    """
    Returns a table of extensive player performance data (per season, per team (franchise_id)).

    Returns:
        pd.DataFrame: DataFrame of historical player performance stats - season by season.
    """
    player_records_dtypes = dict(
        player_id="string",
        Player="string",
        Rank="float64",
        Year_Drafted="float64",
        Age="int64",
        Team="string",
        MP_RS="float64",
        OWS_RS="float64",
        DWS_RS="float64",
        WS_RS="float64",
        WS_48_RS="float64",
        season_year="int64",
        MP_PO="float64",
        OWS_PO="float64",
        DWS_PO="float64",
        WS_PO="float64",
        WS_48_PO="float64",
        Impact="float64",
        Year_Started="int64",
        franchise_id="int64",
        teams_played_for="int64",
        salary="float64",
        allocated_salary="float64",
        MP_Total="float64",
        MP_RS_Cost="float64",
        MP_TOT_Cost="float64",
        WS_RS_Cost="float64",
        WS_TOT_Cost="float64",
        Impact_Cost="float64",
        Rookie_Contract_Year="int64"
    )
    return pd.read_csv(file_path, dtype=player_records_dtypes)


# def load_team_histories():
#     """
#     This is team lookup table of the games data.
#     It has franchise_id too, so the teams can relate to the SQL data.
#
#     Returns:
#         pd.DataFrame: DataFrame of team history.
#     """
#     team_histories_path = os.path.join(FILE_PATH_TO_GAMES_DATA, "TeamHistories_Adjusted.csv")
#     team_histories_dtypes = dict(franchise_id="int64", teamId="int64", teamCity="string", teamName="string", teamAbbrev="string",
#                                  seasonFounded="int64", seasonActiveTill="int64",
#                                  league="string")
#
#     team_histories_df = pd.read_csv(team_histories_path,
#                                     dtype = team_histories_dtypes)
#     return team_histories_df


def load_fan_attendance_revenue():
    """
    This allows revenue, attendance, and operating income from from 2011-2021 to be used.
    It has franchise_id too, so the teams can relate to the SQL data.

    Returns:
        pd.DataFrame: DataFrame of franchise attendance and revenue..
    """
    attendance_revenue_dtypes = dict(
        franchise_id="Int64",
        season_year="int64",
        home_games="float64",
        home_wins="float64",
        home_attendance_total="Int64",
        avg_home_attendance="float64",
        away_games="float64",
        away_wins="float64",
        away_attendance_total="Int64",
        avg_away_attendance="float64",
        total_games="float64",
        total_wins="float64",
        Pct="float64",
        total_attendance="Int64",
        attendance_avg="float64",
        Team_Revenue="float64",
        Ticket_Price="float64",
        Operating_Income="float64"
    )

    file_path = os.path.join(FILE_PATH_TO_COMPILED_DATA, "fan_attendance_revenue.csv")

    fan_attendance_revenue_df = pd.read_csv(
        file_path,
        dtype=attendance_revenue_dtypes
    )

    return fan_attendance_revenue_df


def load_fan_attendance():
    """

    This is a dataframe containing all NBA attendance from games file.
    Note that unlike the revenue data this attendance data goes back almost 40 years.

    Returns:
        pd.DataFrame: DataFrame of franchise attendance and revenue..
    """
    attendance_dtypes = dict(
        franchise_id="Int64",
        season_year="int64",
        home_games="float64",
        home_wins="float64",
        home_attendance_total="Int64",
        avg_home_attendance="float64",
        away_games="float64",
        away_wins="float64",
        away_attendance_total="Int64",
        avg_away_attendance="float64",
        total_games="float64",
        total_wins="float64",
        Pct="float64",
        total_attendance="Int64",
        attendance_avg="float64"
    )

    file_path = os.path.join(FILE_PATH_TO_COMPILED_DATA, "fan_attendance.csv")

    fan_attendance_df = pd.read_csv(
        file_path,
        dtype=attendance_dtypes
    )

    return fan_attendance_df


def load_all_auxiliary_tables():
    """
    Load dataframes from the games database and financial info from morgan stanley and run repeat.

    Returns:
        pd.DataFrame: DataFrame of franchise attendance and revenue..
    """
    team_revenue = load_team_revenue()
    team_mapping = load_team_mapping()
    player_salaries = load_player_salaries()
    league_mapping = load_league_mapping()
    game_history = load_extended_game_history()
    # alternative_players = load_alternative_players_data()
    # player_performance = load_player_performance()
    # team_performance = load_team_performance()
    # team_histories = load_team_histories()
    fan_attendance_revenue = load_fan_attendance_revenue()
    fan_attendance = load_fan_attendance()
    return (team_revenue, team_mapping, player_salaries, league_mapping,
            game_history,
            # alternative_players, player_performance, team_performance,
            # team_histories,
            fan_attendance_revenue, fan_attendance)


def load_auxiliary_tables():
    (team_revenue_df, team_mapping_df, player_salaries_df, league_mapping_df,
     game_history_df,
     # alternative_players_df, player_performance_df, team_performance_df,
     # team_histories_df,
     fan_attendance_revenue_df, fan_attendance_df) = load_all_auxiliary_tables()
    return (team_revenue_df, team_mapping_df, player_salaries_df, league_mapping_df,
            game_history_df,
            # alternative_players_df, player_performance_df,
            # team_performance_df,
            # team_histories_df,
            fan_attendance_revenue_df, fan_attendance_df)


def build_sql_schemas_for_tables(db_path):
    """

    Generate an sql schema for tables in the database.

    Returns:
        pd.DataFrame: DataFrame of the fields of all tables.
    """

    conn = sqlite3.connect(db_path)

    # Get a list of all tables in the database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Format table names
    table_names = [table[0] for table in tables]

    print(table_names)

    # Get schema for each table
    table_schemas = {}

    for table in table_names:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        table_schemas[table] = columns

    # Format the schema info
    schema_report = {}
    for table, columns in table_schemas.items():
        schema_report[table] = [
            {
                "column_id": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "default_value": col[4],
                "is_primary_key": col[5]
            }
            for col in columns
        ]

    # Convert schema report to a DataFrame for display
    schema_rows = []
    for table, cols in schema_report.items():
        for col in cols:
            schema_rows.append({
                "Table": table,
                "Column ID": col["column_id"],
                "Column Name": col["name"],
                "Data Type": col["type"],
                "Not Null": bool(col["notnull"]),
                "Default Value": col["default_value"],
                "Primary Key": bool(col["is_primary_key"])
            })

    schema_df = pd.DataFrame(schema_rows)
    schema_df.to_csv(FILE_PATH_TO_COMPILED_DATA + "schema.csv", index=False)

    print(tabulate(schema_df, tablefmt="plain"))
    cursor.close()
    conn.close()
    return schema_df


def show_tables():
    """

    Menu option to display auxiliary the tables in the database.

    Returns:
        pd.DataFrame: DataFrame of franchise attendance and revenue..
    """
    (team_revenue_df, team_mapping_df, player_salaries_df, league_mapping_df,
     game_history_df, alternative_players_df, player_performance_df,
     team_performance_df, team_histories_df, fan_attendance_revenue_df,
     fan_attendance_df) = load_auxiliary_tables()
    dfs_to_show = [team_revenue_df, team_mapping_df, player_salaries_df, league_mapping_df,
     game_history_df, alternative_players_df, player_performance_df,
                   team_performance_df, team_histories_df, fan_attendance_revenue_df, fan_attendance_df]
    titles_to_show = ["Team Revenue History", "Franchise Location and Interval",
                      "Player Salary History", "League Duration Interval",
                      "Game History", "Alternative Players",
                      "Player Performance", "Team Performance",
                      "Franchise Histories", "Fan Attendance Revenue", "Fan Attendance History"]
    for df, title in zip(dfs_to_show, titles_to_show):
        show_df_info(df, title)


if __name__ == "__main__":
    show_tables()

