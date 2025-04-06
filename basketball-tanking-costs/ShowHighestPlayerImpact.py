"""
show_highest_player_impact.py

Generates and displays sorted tables of NBA player impact metrics.
Includes analysis for:
- All players
- Free agents not on rookie contracts
- Rookie players (not found in the free agent list)
"""
from FreeAgent import get_player_records, get_cleaned_player_records
from General import pretty_print_df
from Paths import FILE_PATH_TO_COMPILED_DATA
from Tables import load_extended_cleaned_player_records

# Default columns to display when viewing player impact
default_player_impact_columns = [
    'player_id', 'Player', 'Rank', 'Year Drafted', 'Age', 'Team',
    'MP RS', 'OWS RS', 'DWS RS', 'WS RS', 'WS/48 RS', 'season_year',
    'MP PO', 'OWS PO', 'DWS PO', 'WS PO', 'WS/48 PO', 'Impact',
    'Year Started', 'franchise_id', 'teams_played_for', 'salary',
    'allocated_salary', 'MP_Total', 'MP_RS_Cost', 'MP_TOT_Cost',
    'WS_RS_Cost', 'WS_TOT_Cost', 'Impact_Cost', 'Rookie Contract Year'
]


def show_highest_player_impact(columns_to_display=default_player_impact_columns):
    """
    Displays the top 20 NBA players ranked by 'Impact' from three datasets:
    1. Players not on rookie contracts (free agents)
    2. All cleaned players
    3. Rookies (players not in the free agent list)

    Args:
        columns_to_display (list): List of column names to include in the display table.
    """
    # first load the players and slice them up by contract type

    # Load free agent players not on rookie contracts
    player_records_df = get_player_records()
    player_records_df.rename(columns={'Year': 'season_year'}, inplace=True)

    # remove nans and drafted players (only first four seasons).
    all_players_df, free_agents_df = get_cleaned_player_records(player_records_df)

    top_impact_players_not_rookie_df = free_agents_df.sort_values(
        by='Impact', ascending=False
    )[columns_to_display].reset_index(drop=True)

    print(pretty_print_df(top_impact_players_not_rookie_df, rows=20, interesting_columns=columns_to_display))

    top_impact_players_df = all_players_df.sort_values(
        by='Impact', ascending=False
    )[columns_to_display].head(20).reset_index(drop=True)

    print(pretty_print_df(top_impact_players_df, rows=20, interesting_columns=columns_to_display))

    # Identify rookies by excluding any player-season found in the free agent dataset
    merge_keys = ['player_id', 'season_year']
    all_players_with_flag = all_players_df.merge(
        free_agents_df[merge_keys].assign(is_free_agent=True),
        on=merge_keys,
        how='left'
    )

    just_rookies_df = all_players_with_flag[
        all_players_with_flag['is_free_agent'].isna()
    ].drop(columns=['is_free_agent'])

    just_rookies_df = just_rookies_df.sort_values(
        by='Impact', ascending=False
    )[columns_to_display].head(20).reset_index(drop=True)

    print(pretty_print_df(just_rookies_df, rows=20, interesting_columns=columns_to_display))


if __name__ == '__main__':
    show_highest_player_impact()
