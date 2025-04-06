import pandas as pd
from Constants import FIRST_YEAR, FINAL_YEAR
from dataclasses import dataclass
from Paths import FILE_PATH_TO_COMPILED_DATA

league_mapping = [
    ["NBA", 1950, FINAL_YEAR + 1],
    ["ABA", 1968, 1976],
    ["BAA", 1947, 1949]
]


# lookup function for abbreviation (passes bb reference team name, like "Miami Heat")
def get_team_abbreviation(teams):
    abbreviations = []
    for team in teams:
        team_record = team_mapping_df[team_mapping_df['Team'] == team]['Abbreviation']
        if not team_record.empty:
            abbreviations.append(team_record.values[0])  # Use .values[0] to retrieve the value without index
        else:
            abbreviations.append("")  # Add an empty string if no match is found
    return abbreviations


# lookup function for abbreviation (passes bb reference team name, like "Miami Heat")
def get_team_abbreviation_from_franchise_id(franchise_ids):
    abbreviations = []
    for franchise_id in franchise_ids:
        team_record = team_mapping_df[team_mapping_df['franchise_id'] == franchise_id]['Abbreviation']
        if not team_record.empty:
            abbreviations.append(team_record.values[0])  # Use .values[0] to retrieve the value without index
        else:
            abbreviations.append("")  # Add an empty string if no match is found
    return abbreviations


# lookup function for team name (like "Miami Heat") (passes bb reference abbreviation, like "MIA")
def get_long_name(abbreviation):
    long_names = []
    for abbrev in abbreviation:
        team_record = team_mapping_df[team_mapping_df['Abbreviation'] == abbrev]['Team']
        if not team_record.empty:
            long_names.append(team_record.values[0])  # Use .values[0] to retrieve the value without index
        else:
            long_names.append("")  # Add an empty string if no match is found
    return long_names


# used to find franchise id from us today hoopshype city ("Miami") and year.
def get_franchise_id(city, year):
    global team_mapping_df
    franchise_ids = []
    team_record = team_mapping_df[(team_mapping_df['City'] == city) & (year >= team_mapping_df['Beginning-Year']) & (
            year <= team_mapping_df['Ending-Year'])]['franchise_id']
    if not team_record.empty:
        franchise_ids.append(team_record.values[0])
    else:
        franchise_ids.append("")
    return franchise_ids[0]


# used to find franchise team name (like "Miami Heat") from us today hoopshype city ("Miami") and year.
def get_team_from_city_year(city, year):
    global team_mapping_df
    teams = []
    team_record = team_mapping_df[(team_mapping_df['City'] == city) & (year >= team_mapping_df['Beginning-Year']) & (
            year <= team_mapping_df['Ending-Year'])]['Team']
    if not team_record.empty:
        teams.append(team_record.values[0])
    else:
        teams.append("")
    return teams[0]


def add_franchise_id(df, team_column="team_abbreviation", verbose=True):
    """
    Adds a franchise_id column to a DataFrame using the provided team_mapping DataFrame.

    Parameters:
        df (pd.DataFrame): DataFrame with a team column to update (e.g., "Tm", "team_abbreviation")
        team_column (str): Name of the column in df to join on (default: "team_abbreviation")
        verbose (bool): Whether to print warnings about unmatched teams

    Returns:
        pd.DataFrame: A new DataFrame with 'franchise_id' added
    """
    # Standardize input column
    global team_mapping_df

    df = df.copy()
    df[team_column] = df[team_column].str.strip().str.upper()

    # Standardize mapping column
    team_mapping = team_mapping_df[["Abbreviation", "franchise_id"]].copy()
    team_mapping["Abbreviation"] = team_mapping["Abbreviation"].str.strip().str.upper()

    # Merge to add franchise_id
    merged = df.merge(team_mapping, left_on=team_column, right_on="Abbreviation", how="left")

    # Report unmatched teams
    if verbose:
        unmatched = merged[merged["franchise_id"].isna()][team_column].unique()
        if len(unmatched) > 0:
            print("⚠️ Warning: The following team abbreviations were not matched to a franchise_id:")
            print(sorted(unmatched))

    return merged.drop(columns=["Abbreviation"])


# Team is used for basketball-reference lookup
# City is used for us today lookup
# Abbreviation is used for bb ref - draft pick lookup
# Franchise Id is universal key for this system's database
# Beginning-Year/Ending-Year are the dates franchise was established (if after the FIRST_YEAR) and perhaps moved, renamed, etc.
# FINAL_YEAR + 1 as Ending-Year means franchise has not been changed since its inception.
team_mapping_df = pd.read_csv(FILE_PATH_TO_COMPILED_DATA + "team_mapping.csv")
league_mapping_df = pd.read_csv(FILE_PATH_TO_COMPILED_DATA + "league_mapping.csv")


@dataclass
class FranchiseMapper:
    team_mapping_df: pd.DataFrame

    def get_franchise_id(self, team_id: int, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['teamId'] == team_id) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['franchise_id'].values[0] if not rec.empty else None

    def get_franchise_from_abbrev(self, abbrev: str, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['Abbreviation'].str.upper() == abbrev.strip().upper()) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['franchise_id'].values[0] if not rec.empty else None

    def get_team_name(self, franchise_id: int, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['franchise_id'] == franchise_id) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['Team'].values[0] if not rec.empty else None

    def get_team_id(self, franchise_id: int, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['franchise_id'] == franchise_id) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['teamId'].values[0] if not rec.empty else None

    def get_abbrev(self, franchise_id: int, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['franchise_id'] == franchise_id) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['Abbreviation'].values[0] if not rec.empty else None

    def get_franchise_from_name(self, team_name: str, year: int):
        rec = self.team_mapping_df[
            (self.team_mapping_df['Team'] == team_name) &
            (self.team_mapping_df['Beginning-Year'] <= year) &
            (self.team_mapping_df['Ending-Year'] >= year)
        ]
        return rec['franchise_id'].values[0] if not rec.empty else None


franchise_mapper = FranchiseMapper(team_mapping_df)
