import pandas as pd
import matplotlib.pyplot as plt

from General import save_plot, pretty_print_df, printFormattedTestStat
from Paths import FILE_PATH_TO_COMPILED_DATA
from Tables import load_fan_attendance_revenue, load_team_mapping
from TeamMapping import franchise_mapper


def plot_team_operating_income():
    """Plot operating income over time for the top 5 and bottom 5 NBA teams."""

    # Load team mapping for franchise name lookup
    team_mapping_df = load_team_mapping()

    # Load and prepare the data
    df = load_fan_attendance_revenue()
    df["season_year_str"] = df["season_year"].astype(str)
    df["Operating_Income"] = pd.to_numeric(df["Operating_Income"], errors="coerce")

    # Compute average income per franchise
    avg_income_by_team = df.groupby("franchise_id")["Operating_Income"].mean().sort_values()

    # Identify bottom 5 and top 5 franchises by average income
    bottom_5_teams = avg_income_by_team.head(5).index.tolist()
    top_5_teams = avg_income_by_team.tail(5).index.tolist()
    selected_franchises = bottom_5_teams + top_5_teams

    # Map franchise_id to team names
    franchise_names = {
        fid: team_mapping_df.loc[team_mapping_df["franchise_id"] == fid, "Team"].values[0]
        for fid in selected_franchises
    }

    # Filter data to selected franchises
    filtered_df = df[df["franchise_id"].isin(selected_franchises)]

    # Plot the results
    plt.figure(figsize=(14, 7))
    for team_id in selected_franchises:
        team_data = filtered_df[filtered_df["franchise_id"] == team_id]

        # Use a year in the dataset to get the correct historical team name
        # Favor last location of franchise.
        sample_year = team_data["season_year"].max() - 1
        team_id = int(team_id)  # just in case it's a string from CSV

        team_name = franchise_mapper.get_team_name(team_id, sample_year)

        plt.plot(team_data["season_year_str"], team_data["Operating_Income"], label=team_name)

    plt.title("Operating Income Over Time: Top 5 vs Bottom 5 NBA Teams (Excluding Totals)")
    plt.xlabel("Season")
    plt.ylabel("Operating Income (in millions USD)")
    plt.legend(title="Franchise")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    save_plot(plt, "Operating Income Over Time")
    plt.show()

    # Filter rows with negative operating income
    # Get team name to show legend.
    negative_income_df = df[df["Operating_Income"] < 0].copy()
    # Ensure correct dtypes
    negative_income_df["season_year"] = pd.to_numeric(negative_income_df["season_year"], errors="coerce")
    negative_income_df["season_year"] = int(negative_income_df["season_year"].min())
    negative_income_df["franchise_id"] = int(negative_income_df['franchise_id'])

    # Add team name using franchise_mapper
    negative_income_df["Team"] = negative_income_df.apply(
        lambda row: franchise_mapper.get_team_name(row["franchise_id"], row["season_year"]), axis=1
    )

    # Print the result
    negative_income_df['Pct'] = negative_income_df['Pct'].apply(printFormattedTestStat)
    negative_income_df['attendance_avg'] = negative_income_df['attendance_avg'].apply(printFormattedTestStat)



if __name__ == "__main__":
    plot_team_operating_income()
