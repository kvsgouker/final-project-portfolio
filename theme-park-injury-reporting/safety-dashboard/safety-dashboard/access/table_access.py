# Company,Incident_date,Ride_name_dirty,Ride_name,Theme_Park,age_gender,description


import os
import pandas as pd

from access.Incident import SyntheticIncident
from access.db import IncidentDatabase, ParkDatabase, IncidentBase
from access.parkInfo import Coaster, Ride, load_parks_from_db, load_coasters_from_db, load_rides_from_db
from access.parkInfo import Park
from access.synthetic import load_distributions, generate_incidents
from utils.utilities import pretty_print_df, show_df_info
from access.db import ParkDatabase

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker


DATA_DIRECTORY = "data"
PROPOSED_INCIDENT_FILE = os.path.join(DATA_DIRECTORY, "incident_log.csv")
DISNEY_UNIVERSAL_INCIDENT_FILE = os.path.join(DATA_DIRECTORY, "suggestion-5-disney-universal-incident-data.csv")
DISNEY_UNIVERSAL_RIDE_LIST = os.path.join(DATA_DIRECTORY, "disney-universal-ride-list.csv")
DISNEY_UNIVERSAL_RIDE_UPDATED_LIST = os.path.join(DATA_DIRECTORY, "disney-universal-ride-list-updated.csv")

# Define column names and types
PROPOSED_INCIDENT_DTYPES = {
    "company": "string",
    "theme_park": "string",
    "ride_name": "string",
    "park_number": "Int64",
    "ride_number": "Int64",
    "incident_date": "string",
    "age_group": "string",
    "gender": "string",
    "injury_location": "string",
    "severity": "string",
    "medical_attention": "string",
    "injury_type": "string",
    "ride_status": "string",
    "contributing_factor": "string",
    "description": "string",
    "submission_time": "string",
    "source": "string"
}


def load_or_create_incident_log():
    """Reads the incident log from disk or creates an empty one with defined schema."""
    if not os.path.exists(PROPOSED_INCIDENT_FILE):
        print("Incident log file not found — creating new one.")

        # Create empty DataFrame with specified dtypes
        empty_df = pd.DataFrame({col: pd.Series(dtype=typ) for col, typ in PROPOSED_INCIDENT_DTYPES.items()})

        # Ensure the directory exists
        os.makedirs(DATA_DIRECTORY, exist_ok=True)

        # Save empty file to disk
        empty_df.to_csv(PROPOSED_INCIDENT_FILE, index=False)
        return empty_df

    try:
        df = pd.read_csv(PROPOSED_INCIDENT_FILE, dtype=PROPOSED_INCIDENT_DTYPES)
        return df
    except Exception as e:
        print(f"Error loading incident log: {e}")
        raise


# Your target column schema and dtypes
DISNEY_UNIVERSAL_INCIDENT_COLUMNS = {
    "Company": "string",
    "Incident_date": "string",
    "Ride_name_dirty": "string",
    "Ride_name": "string",
    "Theme_Park": "string",
    "age_gender": "string",
    "description": "string"
}

def convert_old_incident_file(old_path=DISNEY_UNIVERSAL_INCIDENT_FILE, new_path=PROPOSED_INCIDENT_FILE):
    from datetime import datetime
    import pandas as pd

    df_old = pd.read_csv(old_path)
    ride_key_df = load_ride_key_df()

    # Step 1: Parse Age/Gender
    df_old["age_group"], df_old["gender"] = zip(*df_old["age_gender"].map(parse_age_gender))

    # Step 2: Build base cleaned frame
    df_new = pd.DataFrame({
        "company": df_old["Company"],
        "theme_park": df_old["Theme_Park"],
        "ride_name": df_old["Ride_name"],
        "incident_date": df_old["Incident_date"],
        "age_group": df_old["age_group"],
        "gender": df_old["gender"],
        "injury_location": df_old.get("injury_location", pd.NA),
        "severity": df_old.get("severity", pd.NA),
        "medical_attention": df_old.get("medical_attention", pd.NA),
        "injury_type": df_old.get("injury_type", pd.NA),
        "ride_status": df_old.get("ride_status", pd.NA),
        "contributing_factor": df_old.get("contributing_factor", pd.NA),
        "description": df_old["description"],
        "submission_time": datetime.utcnow().isoformat(),
        "source": "disney_universal_historical"
    })

    # Step 3: Normalize for merge
    def normalize(s): return ''.join(str(s).strip().lower())
    df_new["match_key"] = df_new.apply(lambda r: (normalize(r["theme_park"]), normalize(r["ride_name"])), axis=1)
    ride_key_df["match_key"] = ride_key_df.apply(lambda r: (normalize(r["theme_park"]), normalize(r["ride_name"])), axis=1)

    # Step 4: Merge to get park_number and ride_number
    df_new = df_new.merge(
        ride_key_df[["match_key", "park_number", "ride_number"]],
        on="match_key", how="left"
    )

    # Step 5: Assign ride_key based on the actual values
    df_new["ride_key"] = df_new.apply(
        lambda r: f"/parks/{int(r.park_number)}/rides/{int(r.ride_number)}"
        if pd.notna(r.park_number) and pd.notna(r.ride_number) else pd.NA,
        axis=1
    )

    # Step 6: Check for unmatched rides
    unmatched = df_new[df_new["ride_number"].isna()]
    if not unmatched.empty:
        print(f"Warning: {len(unmatched)} rides could not be matched.")
        print(unmatched[["theme_park", "ride_name"]].drop_duplicates().head())

    # Step 7: Infer injury fields
    inferred = df_new["description"].apply(infer_tags_from_description).apply(pd.Series)
    for col in inferred.columns:
        df_new[col] = df_new[col].fillna(inferred[col])

    # Step 8: Enforce schema and save
    df_new = df_new[list(PROPOSED_INCIDENT_DTYPES.keys())]
    for col, typ in PROPOSED_INCIDENT_DTYPES.items():
        df_new[col] = df_new[col].astype(typ)

    df_new.to_csv(new_path, index=False)
    print(f"Enriched incident log written to: {new_path} with {len(df_new)} records.")
    return df_new




def load_ride_key_df():
    dtype_spec = {
        "company": "string",
        "theme_park": "string",
        "park_number": "Int64",       # Nullable integer
        "ride_name": "string",
        "ride_number": "Int64"        # Nullable integer
    }

    try:
        df = pd.read_csv(DISNEY_UNIVERSAL_RIDE_LIST, dtype=dtype_spec)
        return df
    except Exception as e:
        print(f"Failed to load ride key file: {e}")
        return pd.DataFrame(columns=dtype_spec.keys())


def load_incidents_from_db(model_class):
    session = IncidentDatabase.instance().get_session()
    try:
        results = session.query(model_class).all()

        records = [
            {column: getattr(obj, column) for column in vars(obj) if not column.startswith('_')}
            for obj in results
        ]

        return pd.DataFrame(records)
    finally:
        session.close()

def add_ids_to_incident_log(incident_df, parks_df, rides_df):
    def normalize_park_name(s):
        return ''.join(c.lower() for c in str(s) if c.isalnum())

    incident_df["clean_theme_park"] = incident_df["theme_park"].apply(normalize_park_name)
    incident_df["clean_ride_name"] = incident_df["ride_name"].apply(normalize_park_name)
    parks_df["clean_name"] = parks_df["Park_Name"].apply(normalize_park_name)
    rides_df["clean_ride"] = rides_df["Ride_Name"].apply(normalize_park_name)

    # Merge park info
    incident_df = incident_df.merge(
        parks_df[["Park_Number", "clean_name"]],
        left_on="clean_theme_park",
        right_on="clean_name",
        how="left"
    )

    # Merge ride info
    incident_df = incident_df.merge(
        rides_df[["Ride_Number", "clean_ride", "Park_Number"]],
        left_on=["clean_ride_name", "Park_Number"],
        right_on=["clean_ride", "Park_Number"],
        how="left",
        suffixes=("", "_ride")
    )

    # Rename for clarity
    incident_df = incident_df.rename(columns={"Ride_Number": "Resolved_Ride_Number"})

    # Drop helper columns
    return incident_df.drop(columns=["clean_theme_park", "clean_ride_name", "clean_name", "clean_ride"])



def insert_missing_rides(ride_list_df):
    db = ParkDatabase.instance()
    engine = db.get_engine()
    new_rides = []
    inserted_count = 0

    unmatched = ride_list_df[ride_list_df["ride_number"] == -1].copy()
    unmatched = unmatched.drop_duplicates(subset=["park_number", "ride_name"])

    with engine.begin() as conn:
        Session = sessionmaker(bind=conn)
        session = Session()

        try:
            for _, row in unmatched.iterrows():
                ride = Ride(
                    Ride_Number=None,
                    Park_Number=int(row["park_number"]),
                    Ride_Name=row["ride_name"],
                    Ride_Link=""
                )
                session.add(ride)
                session.flush()  # assigns Ride_Number (auto-increments!)
                # link key has a simple format.
                ride.Ride_Link = f"/parks/{ride.Park_Number}/rides/{ride.Ride_Number}"
                new_rides.append((ride.Ride_Name, ride.Ride_Number))
                inserted_count += 1

            session.commit()
            print(f"Inserted {inserted_count} new rides.")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Transaction failed: {e}")

        finally:
            session.close()

    return new_rides


def insert_additional_parks():
    new_parks = [
        {
            "Park_Name": "Blizzard Beach",
            "Owner_Name": "Walt Disney Attractions",
            "City": "Orlando",
            "State": "FL",
            "Country": "USA",
            "Continent": "North America",
            "Country_Code": "US",
            "Latitude": "28.3532",
            "Longitude": "-81.5661",
            "Time_Zone": "EST",
        },
        {
            "Park_Name": "Typhoon Lagoon",
            "Owner_Name": "Walt Disney Attractions",
            "City": "Orlando",
            "State": "FL",
            "Country": "USA",
            "Continent": "North America",
            "Country_Code": "US",
            "Latitude": "28.3638",
            "Longitude": "-81.5299",
            "Time_Zone": "EST",
        }
    ]

    # Park DB setup
    ParkDatabase.instance().init()

    db = ParkDatabase.instance()
    session = db.get_session()
    try:
        for park_data in new_parks:
            park = Park(**park_data)
            session.add(park)
        session.commit()
        print("New parks added with auto-incremented Park_Number.")
    except Exception as e:
        session.rollback()
        print(f"Error inserting parks: {e}")
    finally:
        session.close()

def ensure_synthetic_data(min_count=100):
    session = IncidentDatabase.instance().get_session()
    try:
        result = session.query(SyntheticIncident).count()
        if result >= min_count:
            return  # Already populated

        print(f"Auto-generating synthetic data...")

        distributions = load_distributions()
        coasters_df = load_coasters_from_db()
        parks_df = load_parks_from_db()
        rides_df = load_rides_from_db()

        fake_data = generate_incidents(distributions, parks_df, rides_df, coasters_df, incident_count=min_count)

        session.execute(text("DELETE FROM fake_incidents"))
        session.add_all([
            SyntheticIncident(**{k: v for k, v in vars(f).items() if not k.startswith('_')})
            for f in fake_data
        ])
        session.commit()

        print(f"{len(fake_data)} synthetic incidents saved.")
    finally:
        session.close()


if __name__ == "__main__":
    incident_df = pd.read_csv(DISNEY_UNIVERSAL_INCIDENT_FILE)

    # Drop rows with missing ride names
    filtered_df = incident_df.dropna(subset=["Ride_name", "Theme_Park", "Company"])

    unique_rides_df = load_ride_key_df()

    print(show_df_info(unique_rides_df, "Rides"))
    print(pretty_print_df(unique_rides_df))

    ParkDatabase.instance().init()
    engine = ParkDatabase.instance().get_engine()

    # insert_additional_parks()
    # insert_missing_rides(unique_rides_df)
    # show rides after conversion
    parks_df = load_parks_from_db()
    rides_df = load_rides_from_db()
    target_parks = [8, 338, 5, 6, 7, 339, 64, 65, 67]
    rides_subset_df = rides_df[rides_df["Park_Number"].isin(target_parks)]
    print(pretty_print_df(rides_subset_df))
    convert_old_incident_file()




