# Category	Incidents/Year/Park	Justification
#
# Disney/Universal	~14 (real)	underreported
# Regional thrill parks	20–30	fewer staff, higher risk
# Carnival/touring	30–50+	poor maintenance, no oversight
# Small family parks	5–15	less extreme rides

import random
from datetime import datetime, timedelta

import pandas as pd

from access.Incident import SyntheticIncident
import json
import os
import numpy as np
from collections import Counter


# Synthetic data support.
USE_SYNTHETIC_DATA = False

def is_fake_mode():
    global USE_SYNTHETIC_DATA
    return USE_SYNTHETIC_DATA

def set_fake_mode(mode: bool):
    global USE_SYNTHETIC_DATA
    USE_SYNTHETIC_DATA = mode

def sample_from_distribution(dist):
    if isinstance(dist, list):
        return random.choice(dist)
    elif isinstance(dist, dict):
        values = list(dist.keys())
        weights = list(dist.values())
        return random.choices(values, weights=weights, k=1)[0]
    else:
        raise ValueError("Distribution must be a list or dict.")


# Multipliers representing attendance level for each year
ATTENDANCE_WEIGHTS = {
    2020: 0.20,
    2021: 0.40,
    2022: 0.75,
    # Note: All others default to 1.0
}


def classify_ride_type(ride_name, theme_park_name, coaster_ids, ride_number):
    ride = str(ride_name).lower()
    park = str(theme_park_name).lower()

    water_keywords = ['splash', 'slide', 'wet', 'falls', 'water', 'beach', 'lagoon', 'river']

    if ride_number in coaster_ids:
        return 'coaster'
    elif any(word in ride or word in park for word in water_keywords):
        return 'water'
    else:
        return 'other'


def compute_fear_factor(df):
    df = df.copy()

    # Max values for scaling (avoid div by zero)
    max_vals = {
        "Speed": df["Speed"].max() or 1,
        "Height": df["Height"].max() or 1,
        "Drop": df["Drop"].max() or 1,
        "Inversions": df["Inversions"].max() or 1,
        "G-force": df["G-force"].max() or 1,
        "Max_Vertical_Angle": df["Max_Vertical_Angle"].max() or 1
    }

    # Weights and exponents for each feature
    base_weights = {
        "Speed": 0.22,
        "Height": 0.18,
        "Drop": 0.2,
        "Inversions": 0.15,
        "G-force": 0.15,
        "Max_Vertical_Angle": 0.1
    }

    exponents = {
        "Speed": 2.0,
        "Height": 1.8,
        "Drop": 2.0,
        "Inversions": 2.5,
        "G-force": 2.2,
        "Max_Vertical_Angle": 2.0
    }

    # Only use features that have data
    active_cols = [col for col in base_weights if col in df.columns and max_vals[col] > 0]
    weight_sum = sum(base_weights[col] for col in active_cols)

    # Compute nonlinear score
    fear = 0
    for col in active_cols:
        scaled = (df[col] / max_vals[col]).clip(0, 1).pow(exponents[col]).fillna(0)
        fear += scaled * (base_weights[col] / weight_sum)

    # Optional: ramp extreme scores using sigmoid-like curve
    def fear_ramp(x):
        # S-curve: sharp rise near high values, squashes low
        return (x**3) / ((x**3 + (1 - x)**3) + 1e-6)

    fear = fear_ramp(fear)

    # Binary feature multipliers (bonus fear for exotic design)
    extreme_flags = ["flying", "spinning", "dive", "motorbike"]
    boost_counts = df[extreme_flags].fillna(0).astype(bool).sum(axis=1)
    multiplier = 1.15 ** boost_counts

    # Final fear factor, clipped to [0, 1]
    fear_factor = (fear * multiplier).clip(0, 1)

    return fear_factor



def random_date(start_year, end_year):
    years = list(range(int(start_year), int(end_year) + 1))
    weights = [ATTENDANCE_WEIGHTS.get(year, 1.0) for year in years]
    normalized = [w / sum(weights) for w in weights]

    selected_year = np.random.choice(years, p=normalized)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe default to avoid invalid dates

    return f"{selected_year}-{month:02d}-{day:02d}"


def generate_incident_for_ride(ride, park, distributions, coaster_ids, care_quotient = 0.03):
    # simulate care - safety and training.
    if random.random() < care_quotient:
        print("Incident prevented!")
        return None

    # print("attempting to create incident for ride: ", ride['Ride_Name'])
    ride_type = classify_ride_type(ride["Ride_Name"], park["Park_Name"], coaster_ids, ride["Ride_Number"])

    # Base sampling
    age_group = sample_from_distribution(distributions["age_group"])
    gender = sample_from_distribution(distributions["gender"])
    injury_location = sample_from_distribution(distributions["injury_location"])

    severity_weights = distributions.get("severity_by_age_group", {}).get(age_group)

    if severity_weights:
        severity = random.choices(
            population=list(severity_weights.keys()),
            weights=list(severity_weights.values())
        )[0]
    else:
        # fallback
        severity = sample_from_distribution(distributions["severity"])

    medical_attention = sample_from_distribution(distributions["medical_attention"])
    injury_type = sample_from_distribution(distributions["injury_type"])
    ride_status = sample_from_distribution(distributions["ride_status"])
    contributing_factor = sample_from_distribution(distributions["contributing_factor"])

    # Salted tweaks
    date = random_date("2014", "2023")
    month = int(date.split("-")[1])
    description = "Normal Incident."
    salt_applied = False

    # Salt 1: Heat-related summer trend
    if month in [6, 7, 8] and age_group in ['60+', 'Under 12']:
        if random.random() < 0.3:
            injury_type = 'Dizziness / Fainting'
            severity = 'Moderate'
            description = 'Guest reported dizziness due to heat.'
            salt_applied = True

    # Water rides → more in summer, more illness/slips
    if not salt_applied and ride_type == 'water' and month in [6, 7, 8]:
        injury_type = random.choices(
            ["Slip / Fall", "Seizure / Illness", injury_type], weights=[0.4, 0.4, 0.2]
        )[0]
        severity = random.choices(["Minor", "Moderate", severity], weights=[0.5, 0.3, 0.2])[0]
        description = "Water incident."
        salt_applied = True

    # Coasters → more high-impact, neck/back/head, higher severity
    if not salt_applied and ride_type == "coaster":
        # Influence injury location
        injury_location = random.choices(
            ["Head", "Neck", "Back", injury_location], weights=[0.3, 0.25, 0.25, 0.2]
        )[0]
        description = "Coaster incident."

    return SyntheticIncident(
        company=park.get("Owner_Name", "Unknown Co."),
        theme_park=park["Park_Name"],
        ride_name=ride["Ride_Name"],
        incident_date=date,
        age_group=age_group,
        gender=gender,
        injury_location=injury_location,
        severity=severity,
        medical_attention=medical_attention,
        injury_type=injury_type,
        ride_status=ride_status,
        contributing_factor=contributing_factor,
        description=description,
        submission_time=datetime.now().isoformat(),
        ride_number=int(ride["Ride_Number"]) if not pd.isna(ride["Ride_Number"]) else None,
        park_number=int(park["Park_Number"]) if not pd.isna(park["Park_Number"]) else None
    )



def generate_incidents(distributions, parks_df, rides_df, coasters_df, incident_count=1000):
    incidents = []

    coasters_df['fear_factor'] = compute_fear_factor(coasters_df)
    fear_lookup = coasters_df['fear_factor'].to_dict()

    # coasters_df.to_csv("scary_rides.csv", index=False)

    # coaster_names = []
    # for _ in range(1000):
    #     ride = coasters_df.sample(n=1, weights=coasters_df['fear_factor']).iloc[0]
    #     coaster_names.append(ride['Ride_Name'])
    #
    # counts = Counter(coaster_names)
    # for ride, count in counts.most_common(20):
    #     print(f"{ride}: {count}")

    # Debug counter
    coaster_names = []


    coaster_ids = set(coasters_df["Ride_Number"].dropna().unique())
    valid_park_numbers = set(rides_df["Park_Number"].dropna().unique())
    parks_df = parks_df[parks_df["Park_Number"].isin(valid_park_numbers)]

    # Split rides into coasters and others
    coaster_subset_df = coasters_df.copy()
    others_subset_df = rides_df[~rides_df["Ride_Number"].isin(coaster_ids)]

    while len(incidents) < incident_count:
        park = parks_df.sample(n=1).iloc[0]

        if random.random() < 0.45:
            # Sample from coasters with direct fear_factor weights
            ride = coaster_subset_df.sample(n=1, weights=coaster_subset_df['fear_factor']).iloc[0]
        else:
            # Sample from others with default fallback weights
            ride = others_subset_df.sample(n=1).iloc[0]

        if ride["Ride_Number"] in coaster_subset_df["Ride_Number"].values:
            coaster_names.append(ride["Ride_Name"])

        incident = generate_incident_for_ride(ride, park, distributions, coaster_ids)
        if incident:
            incidents.append(incident)


    # After generation is complete:
    print("Top 20 coasters drawn:")
    for name, count in Counter(coaster_names).most_common(20):
        print(f"{name}: {count}")

    return incidents


def load_distributions(path="data/distributions.json"):
    with open(path, "r") as f:
        return json.load(f)
