import pandas as pd
from flask import Flask, render_template, request, redirect, render_template_string
from datetime import datetime
from dotenv import load_dotenv
from access.Incident import SyntheticIncident, RealIncident
from access.db import IncidentBase, IncidentDatabase, ParkDatabase, ParkBase
from access.synthetic import load_distributions, set_fake_mode, is_fake_mode, \
    classify_ride_type, compute_fear_factor, generate_incidents
from access.parkInfo import load_coasters_from_db, load_parks_from_db, load_rides_from_db
from access.table_access import load_or_create_incident_log, load_incidents_from_db, ensure_synthetic_data
from sqlalchemy import inspect, text
from sklearn.ensemble import RandomForestClassifier

from config.filter_config import filter_fields
from generate_graphs import generate_graphs
from utils.enrichment import plot_cm
from utils.utilities import show_df_info, apply_filters
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix


def produce_models(use_fake, return_eval=False):
    model_class = SyntheticIncident if use_fake else RealIncident
    df = load_incidents_from_db(model_class)

    if df.empty:
        raise ValueError("No incident data available in the database.")

    df = df.dropna(subset=["age_group", "gender", "ride_number", "park_number", "severity", "injury_location", "incident_date"])
    if df.empty:
        raise ValueError("All rows dropped due to missing values in required columns.")

    df["month"] = pd.to_datetime(df["incident_date"], errors='coerce').dt.month
    df["ride_type"] = df["ride_name"].apply(lambda x: classify_ride_type(x, "", set(), None))

    def encode(col, mapping): return df[col].map(mapping)

    age_map = {"Under 12": 0, "18–40": 1, "41–60": 2, "60+": 3, "Minor": 0, "Teen": 1, "Adult": 2, "Senior": 3}
    gender_map = {"Female": 0, "Male": 1, "Nonbinary": 2, "Other": 3, "Unknown": 3}
    ride_type_map = {"coaster": 0, "water": 1, "other": 2}

    X = pd.DataFrame({
        "age": encode("age_group", age_map),
        "gender": encode("gender", gender_map),
        "month": df["month"],
        "ride_type": encode("ride_type", ride_type_map)
    }).dropna()

    if X.empty:
        raise ValueError("No data available after encoding and dropping NA values.")

    y_loc = df.loc[X.index, "injury_location"]
    y_sev = df.loc[X.index, "severity"]

    X_train, X_test, y_loc_train, y_loc_test = train_test_split(X, y_loc, test_size=0.2, random_state=42)
    _, _, y_sev_train, y_sev_test = train_test_split(X, y_sev, test_size=0.2, random_state=42)

    location_model = RandomForestClassifier(n_estimators=100, class_weight='balanced').fit(X_train, y_loc_train)
    severity_model = RandomForestClassifier(n_estimators=100, class_weight='balanced').fit(X_train, y_sev_train)

    if return_eval:
        y_loc_pred = location_model.predict(X_test)
        y_sev_pred = severity_model.predict(X_test)

        # Generate confusion matrices (already done)
        plot_cm(y_loc_test, y_loc_pred, "Injury Location Confusion Matrix")
        plot_cm(y_sev_test, y_sev_pred, "Severity Confusion Matrix")

        # Generate classification reports
        loc_report = classification_report(y_loc_test, y_loc_pred, zero_division=0)
        sev_report = classification_report(y_sev_test, y_sev_pred, zero_division=0)

        return location_model, severity_model, loc_report, sev_report

    return location_model, severity_model

def inspect_menu_data():
    # for debugging basically
    df_parks = load_parks_from_db()
    df_rides = load_rides_from_db()
    df_coasters = load_coasters_from_db()

    print("Unique Owner_Names:", df_parks["Owner_Name"].nunique())
    print(df_parks["Owner_Name"].dropna().unique()[:10])

    print("\nUnique Park_Names:", df_parks["Park_Name"].nunique())
    print(df_parks["Park_Name"].dropna().unique()[:10])

    print("\nUnique Ride_Names (Coasters):", df_coasters["Ride_Name"].nunique())
    print(df_coasters["Ride_Name"].dropna().unique()[:10])


def build_drilldown_data():
    df_parks = load_parks_from_db()
    df_rides = load_rides_from_db()

    # Strip and normalize
    df_parks["Park_Name"] = df_parks["Park_Name"].str.strip()
    df_parks["Owner_Name"] = df_parks["Owner_Name"].str.strip()
    df_rides["Ride_Name"] = df_rides["Ride_Name"].str.strip()

    # Merge rides with parks
    merged = df_rides.merge(
        df_parks[["Park_Number", "Park_Name", "Owner_Name"]],
        on="Park_Number",
        how="left"
    )

    # Fill missing data
    merged["Owner_Name"] = merged["Owner_Name"].fillna("Other")
    merged["Park_Name"] = merged["Park_Name"].fillna("Unknown Park")
    merged["Ride_Name"] = merged["Ride_Name"].fillna("Unknown Ride")

    # Build nested dict
    nested = {}
    for _, row in merged.iterrows():
        owner = row["Owner_Name"]
        park = row["Park_Name"]
        ride = row["Ride_Name"]

        nested.setdefault(owner, {}).setdefault(park, []).append(ride)

    # Alphabetize: move "Other" to the end
    owners = sorted([o for o in nested.keys() if o != "Other"])
    if "Other" in nested:
        owners.append("Other")

    sorted_nested = {}
    for owner in owners:
        sorted_nested[owner] = {}
        for park in sorted(nested[owner].keys()):
            sorted_nested[owner][park] = sorted(nested[owner][park])

    return sorted_nested



load_dotenv()


# load old csv file
incident_log_df = load_or_create_incident_log()
print(show_df_info(incident_log_df, "Incident Log"))

# Incident DB setup
db = IncidentDatabase.instance()
db.init()
incident_engine = db.get_engine()

try:
    IncidentBase.metadata.create_all(incident_engine)
except Exception as e:
    print(f"[WARNING] Table creation failed: {e}")

# Park DB setup
ParkDatabase.instance().init()
park_engine = ParkDatabase.instance().get_engine()

# Check if 'incidents' exists in the incident database
if not inspect(incident_engine).has_table("synthetic_incidents"):
    print("Table 'synthetic_incidents' does not exist in the incident database")

if not inspect(incident_engine).has_table("real_incidents"):
    print("Table 'real_incidents' does not exist in the incident database")

# Check if key tables exist in park_info.db
for table_name in [
    "coasters", "parks", "rides",
    "ride_history_by_year", "ride_history_by_month",
    "ride_history_by_day", "ride_history_by_hour"
]:
    if not inspect(park_engine).has_table(table_name):
        print(f"Table '{table_name}' does NOT exist in park_info.db")
    else:
        print(f"Table '{table_name}' is present in park_info.db")

ensure_synthetic_data()

trained_models = {
    "location": None,
    "severity": None
}

location_model, severity_model = produce_models(is_fake_mode())
trained_models["location"] = location_model
trained_models["severity"] = severity_model

# Encode input
age_map = {"Under 12": 0, "18–40": 1, "41–60": 2, "60+": 3}
gender_map = {"Female": 0, "Male": 1, "Nonbinary": 2, "Other": 3}
month_map = {month: i for i, month in enumerate([
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
], 1)}
ride_type_map = {"coaster": 0, "water": 1, "other": 2}


app = Flask(__name__)


# Homepage Route
@app.route('/')
def index():
    return render_template('index.html', is_fake_mode=is_fake_mode())

@app.route('/set_fake/<mode>')
def set_fake_data_mode(mode):
    set_fake_mode(mode.lower() == 'true')
    location_model, severity_model = produce_models(is_fake_mode())
    trained_models["location"] = location_model
    trained_models["severity"] = severity_model
    return redirect('/')


@app.route('/data')
def view_data():
    use_fake = is_fake_mode()
    model_class = SyntheticIncident if use_fake else RealIncident
    df = load_incidents_from_db(model_class)
    filtered_df = apply_filters(df, request.args)
    table_html = filtered_df.to_html(classes='table table-striped', index=False)

    return render_template("data.html", table_html=table_html, filter_fields=filter_fields)

@app.route('/fear')
def show_fear():
    use_fake = is_fake_mode()
    model_class = SyntheticIncident if use_fake else RealIncident

    # Load data
    df = load_incidents_from_db(model_class)
    rides_df = load_rides_from_db()
    parks_df = load_parks_from_db()


    # Step 1: Load the CSV (for patching)
    # coasters_df = pd.read_csv("coasters_clean.csv")
    # #
    # # # Step 3: Store the DataFrame as a table in SQL (overwrite if needed)
    # coasters_df.to_sql("coasters", con=park_engine, if_exists="replace", index=False)

    coasters_df = load_coasters_from_db()


    # Drop rows where Ride_Name or Park_Name is missing (invalid ride linkage)
    rides_df = rides_df.dropna(subset=["Ride_Number", "Park_Number"])
    parks_df = parks_df.dropna(subset=["Park_Number"])
    coasters_df = coasters_df.dropna(subset=["Ride_Number", "Park_Number", "Ride_Name", "Park_Name"])

    # Filter incident data
    filtered_df = apply_filters(df, request.args)

    incident_counts = (
        filtered_df.groupby("ride_number")
        .size()
        .reset_index(name="incident_count")
        .rename(columns={"ride_number": "Ride_Number", "incident_count": "Incident_Count"})
    )

    merged = (
        incident_counts
        .merge(rides_df, on="Ride_Number", how="left")  # Adds Ride_Name, Park_Number
        .merge(parks_df, on="Park_Number", how="left")  # Now this works!
    )

    # Keep only coasters whose Ride_Number appears in rides_df
    coasters_df = coasters_df[coasters_df["Ride_Number"].isin(rides_df["Ride_Number"])]

    # Add fear factor
    fear_df = compute_fear_factor(coasters_df).reset_index()
    fear_df.columns = ["Ride_Number", "Fear_Factor"]
    merged = merged.merge(fear_df, on="Ride_Number", how="left")
    merged.dropna(subset=["Fear_Factor"], inplace=True)

    # Sort and select fields
    merged = merged.sort_values(by=["Incident_Count", "Fear_Factor"], ascending=False)

    display_df = merged[[
        "Ride_Name", "Ride_Number", "Park_Name", "Park_Number", "Incident_Count", "Fear_Factor"
    ]]

    display_df.columns = [
        "Ride Name", "Ride Number", "Park Name", "Park Number", "Incident Count", "Fear Factor"
    ]

    table_html = display_df.to_html(classes='table table-striped', index=False)
    return render_template("data.html", table_html=table_html, filter_fields=filter_fields)


@app.route('/graphs')
def show_graphs():
    use_fake = is_fake_mode()
    model = SyntheticIncident if use_fake else RealIncident
    df = load_incidents_from_db(model)
    filtered_df = apply_filters(df, request.args)

    if filtered_df.empty:
        return "No data available to generate graphs."

    fig_data = generate_graphs(filtered_df)

    return render_template(
        "graphs.html",
        **fig_data,
        filter_fields=filter_fields,
        request=request  # ✅ required for sidebar_filters.html
    )

@app.route('/submit', methods=['POST'])
def handle_submission():
    form_data = {
        k: v.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').strip()
        for k, v in request.form.to_dict(flat=True).items()
    }
    form_data["submission_time"] = datetime.now().isoformat()

    use_fake = is_fake_mode()
    model = SyntheticIncident if use_fake else RealIncident

    # Load rides table and do ride lookup
    rides_df = load_rides_from_db()

    def normalize(s):
        return ''.join(str(s).lower().strip())

    # Normalize input
    theme_park = normalize(form_data.get("theme_park", ""))
    ride_name = normalize(form_data.get("ride_name", ""))

    # Normalize rides table for lookup
    rides_df["norm_ride_name"] = rides_df["Ride_Name"].astype(str).apply(normalize)

    match = rides_df[
        (rides_df["norm_ride_name"] == ride_name)
    ]

    if not match.empty:
        form_data["ride_number"] = match.iloc[0]["Ride_Number"].item()
        form_data["park_number"] = match.iloc[0]["Park_Number"].item()
    else:
        print(f"[WARN] Ride lookup failed: {form_data['theme_park']} / {form_data['ride_name']}")
        form_data["ride_number"] = None
        form_data["park_number"] = None

    # Write to DB
    db_session = IncidentDatabase.instance().get_session()
    try:
        incident = model(**form_data)
        db_session.add(incident)
        db_session.commit()
    finally:
        db_session.close()

    return redirect('/')


@app.route('/initdb')
def init_db_route():
    engine = IncidentDatabase.instance().get_engine()
    IncidentBase.metadata.create_all(bind=engine)
    return "Database initialized!"

@app.route('/resetdb')
def reset_db():
    engine = IncidentDatabase.instance().get_engine()
    IncidentBase.metadata.drop_all(bind=engine)
    IncidentBase.metadata.create_all(bind=engine)
    return "Database reset!"

@app.route("/model")
def model_page():
    use_fake = is_fake_mode()
    location_model, severity_model = produce_models(use_fake)
    trained_models["location"] = location_model
    trained_models["severity"] = severity_model
    return render_template("modeling_tools.html")

@app.route("/model/predict", methods=["POST"])
def predict_model():
    if not trained_models["location"] or not trained_models["severity"]:
        return "Model not trained. Please go to the modeling page first."


    # Get form input
    age = age_map.get(request.form.get("age_group"), -1)
    gender = gender_map.get(request.form.get("gender"), -1)
    month = month_map.get(request.form.get("month"), -1)
    ride_type = ride_type_map.get(request.form.get("ride_type"), -1)

    X_input = pd.DataFrame([{
        "age": age,
        "gender": gender,
        "month": month,
        "ride_type": ride_type
    }])

    location_pred = trained_models["location"].predict(X_input)[0]
    severity_pred = trained_models["severity"].predict(X_input)[0]

    return render_template("model_result.html",
                           age_group=request.form.get("age_group"),
                           gender=request.form.get("gender"),
                           month=request.form.get("month"),
                           ride_type=request.form.get("ride_type"),
                           location=location_pred,
                           severity=severity_pred)


@app.route("/model/evaluate")
def evaluate_model():
    use_fake = is_fake_mode()
    location_model, severity_model, loc_report, sev_report = produce_models(use_fake, return_eval=True)

    trained_models["location"] = location_model
    trained_models["severity"] = severity_model

    return render_template("model_eval.html",
                           location_img="/static/injury_location_confusion_matrix.png",
                           severity_img="/static/severity_confusion_matrix.png",
                           loc_report=loc_report,
                           sev_report=sev_report)

@app.route('/importcsv')
def import_csv_to_db():
    engine = IncidentDatabase.instance().get_engine()
    try:
        # Load enriched incident log (already contains ride_number and park_number)
        incident_log_df = load_or_create_incident_log()

        # Optional: Validate required fields exist
        required_columns = {'ride_number', 'park_number'}
        if not required_columns.issubset(set(incident_log_df.columns)):
            return "Error: Missing required ride_number or park_number columns."

        if 'source' in incident_log_df.columns:
            incident_log_df = incident_log_df.drop(columns=['source'])

        # Insert directly into incidents table
        incident_log_df.to_sql("real_incidents", engine, if_exists="append", index=False)

        return render_template_string("""
            <div class="container mt-5">
                <h3>CSV data imported. {{ count }} records processed.</h3>
                <div class="mt-4">
                    <a href="/" class="btn btn-outline-secondary">← Back to Home</a>
                </div>
            </div>
        """, count=len(incident_log_df))

    except Exception as e:
        return f"Error: {e}"


@app.route('/fakedata')
def fake_data():
    count_str = request.args.get("count", "1000")
    try:
        count = int(count_str)
    except ValueError:
        count = 1000

    distributions = load_distributions()
    coasters_df = load_coasters_from_db()
    parks_df = load_parks_from_db()
    rides_df = load_rides_from_db()

    fake_data = generate_incidents(distributions, parks_df, rides_df, coasters_df, count=count)

    session = IncidentDatabase.instance().get_session()

    try:
        # Clear old fake data
        session.execute(text("DELETE FROM fake_incidents"))
        session.add_all([
            SyntheticIncident(**{k: v for k, v in vars(f).items() if not k.startswith('_')})
            for f in fake_data
        ])
        session.commit()
        print(f"{len(fake_data)} fake incidents saved to fake_incidents table.")
    finally:
        session.close()

    return render_template_string("""
        <div class="container mt-5">
            <h3>{{ count }} fake incidents generated and stored.</h3>
            <div class="mt-4">
                <a href="/" class="btn btn-outline-secondary">← Back to Home</a>
            </div>
        </div>
    """, count=len(fake_data))

@app.route("/entry")
def input_form():
    drilldown_data = build_drilldown_data()
    return render_template("entry_form.html", drilldown_json=drilldown_data)



if __name__ == '__main__':
    app.run(debug=True)

