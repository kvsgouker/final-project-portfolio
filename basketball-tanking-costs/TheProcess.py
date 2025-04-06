# Re-import libraries and re-run the plotting code after environment reset

import matplotlib.pyplot as plt
import pandas as pd

from General import save_plot
from Tables import load_extended_game_history

def plot_tanking_team_examples():
    """
    This shows how a number of teams who have long histories of losing seasons.
    Tracks attendance together wth team wins and losses.
    """
    games_df = load_extended_game_history()

    # Teams and their annotations
    teams = {
        26: {  # Kings
            'name': 'Sacramento Kings',
            'annotations': {
                2006: "Eliminated by Spurs\nEnd of playoff streak",
                2010: "Draft DeMarcus Cousins",
                2017: "Trade Cousins to Pelicans",
                2020: "COVID begins",
                2023: "Return to Playoffs"
            }
        },
        3: {  # Hornets/Bobcats
            'name': 'Charlotte',
            'annotations': {
                2012: "Worst season in history\n(7-59 lockout year)",
                2014: "Rebrand to Hornets",
                2020: "LaMelo Ball drafted"
            }
        },
        22: {  # Magic
            'name': 'Orlando Magic',
            'annotations': {
                2012: "Dwight Howard traded",
                2014: "Draft Aaron Gordon",
                2020: "COVID begins",
                2022: "Draft Paolo Banchero"
            }
        },
        23: { # Sixers
            'name': 'Philadelphia 76ers',
            'annotations': {
                2013: "Jrue Holiday traded",
                2014: "The Process begins\nEmbiid drafted",
                2016: "Embiid debuts next season",
                2018: "76ers start winning\n(50+ wins)",
                2020: "COVID begins",
                2022: "Post-COVID recovery"
            }
        },
        18: {  # Timberwolves
            'name': 'Minnesota Timberwolves',
            'annotations': {
                2014: "Trade Kevin Love for Wiggins",
                2015: "Draft Karl-Anthony Towns",
                2020: "Draft Anthony Edwards"
            }
        },
        30: {  # Wizards
            'name': 'Washington Wizards',
            'annotations': {
                2013: "John Wall major injury",
                2019: "Trade Otto Porter",
                2020: "COVID begins",
                2023: "Trade Bradley Beal"
            }
        }
    }

    # Plotting for each team
    for team_id, info in teams.items():
        home_df = games_df[(games_df['home_team_franchise_id'] == team_id) &
                           (games_df['season_year'] >= 2005) &
                           (games_df['season_year'] <= 2024)].copy()
        away_df = games_df[(games_df['away_team_franchise_id'] == team_id) &
                           (games_df['season_year'] >= 2005) &
                           (games_df['season_year'] <= 2024)].copy()

        home_summary = home_df.groupby('season_year').agg(
            Games=('gameId', 'count'),
            HomeWins=('home_win_flag', 'sum'),
            Attendance=('attendance', 'sum')
        ).reset_index().sort_values('season_year')

        away_summary = away_df.groupby('season_year').agg(
            Games=('gameId', 'count'),
            AwayWins=('away_win_flag', 'sum')
        ).reset_index().sort_values('season_year')

        home_summary['AwayWins'] = away_summary['AwayWins'].values
        home_summary['TotalWins'] = home_summary['HomeWins'] + home_summary['AwayWins']

        fig, ax1 = plt.subplots(figsize=(12, 7))

        ax1.plot(home_summary['season_year'], home_summary['Attendance'], marker='o', linestyle='-', label='Home Attendance', color='blue')
        ax1.set_xlabel("Season")
        ax1.set_ylabel("Total Home Attendance", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.set_xticks(range(home_summary['season_year'].min(), home_summary['season_year'].max() + 1, 2))
        ax1.set_xticklabels([f"{year}-{str(year+1)[-2:]}" for year in ax1.get_xticks()])
        ax1.grid(True)

        for year, text in info['annotations'].items():
            if year in home_summary['season_year'].values:
                y = home_summary.loc[home_summary['season_year'] == year, 'Attendance'].values[0]
                ax1.annotate(text, (year, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, arrowprops=dict(arrowstyle="->"))

        ax2 = ax1.twinx()
        ax2.plot(home_summary['season_year'], home_summary['TotalWins'], marker='s', linestyle='-', color='red', label='Total Wins')
        ax2.set_ylabel("Total Wins (Home + Away)", color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        plt.title(f"{info['name']}: Attendance and Wins (2005-2024)")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.tight_layout()
        save_plot(plt, f"{info['name']}_tank")
        plt.show()

if __name__ == '__main__':
    plot_tanking_team_examples()
