import itertools

from plotly.express import line, pie, bar, histogram
import plotly.io as pio
import plotly.express as px

import pandas as pd
import plotly.express as px
import plotly.io as pio

from access.parkInfo import load_coasters_from_db
from access.synthetic import load_distributions


def generate_graphs(df):

    coasters_df = load_coasters_from_db()
    coaster_ids = set(coasters_df["Ride_Number"].dropna())

    def classify_ride_type(row):
        ride = str(row["ride_name"]).lower()
        park = str(row["theme_park"]).lower()
        ride_number = row.get("ride_number")

        if ride_number in coaster_ids:
            return 'coaster'
        if any(w in ride or w in park for w in
               ["splash", "slide", "falls", "wet", "water", "beach", "lagoon", "river"]):
            return 'water'
        return 'other'

    coasters_meta = load_coasters_from_db()[['Ride_Number', 'Opening_Year']]

    # Ensure correct type
    df['ride_number'] = pd.to_numeric(df['ride_number'], errors='coerce')
    coasters_meta['Ride_Number'] = pd.to_numeric(coasters_meta['Ride_Number'], errors='coerce')

    # Merge on Ride_Number only
    merged_coasters_df = df.merge(coasters_meta, how='left', left_on='ride_number', right_on='Ride_Number')

    merged_coasters_df['Opening_Year'] = pd.to_numeric(merged_coasters_df['Opening_Year'], errors='coerce')
    merged = merged_coasters_df.dropna(subset=['Opening_Year']).copy()

    def bin_era(year):
        if year < 2000:
            return "Before 2000"
        elif year < 2010:
            return "2000–2009"
        elif year < 2020:
            return "2010–2019"
        else:
            return "2020+"

    merged['Era'] = merged['Opening_Year'].apply(bin_era)

    fig_severity_by_coaster_era = px.histogram(
        merged,
        x='Era',
        color='severity',
        barmode='group',
        category_orders={"Era": ["Before 2000", "2000–2009", "2010–2019", "2020+"]},
        title="Incident Severity by Coaster Era"
    )

    df["ride_type"] = df.apply(classify_ride_type, axis=1)
    df['incident_date'] = pd.to_datetime(df['incident_date'], errors='coerce')

    # --- Company grouping ---
    known = ["Disney", "Universal", "Sea World", "Six Flags", "Cedar Point"]
    def company_group(name):
        for k in known:
            if k.lower() in str(name).lower():
                return k
        return "Other"
    df['CompanyGroup'] = df['company'].apply(company_group)

    # --- Line chart: Monthly incidents by company ---
    line_data = df.groupby([df['incident_date'].dt.to_period("M"), "CompanyGroup"]).size().reset_index(name="count")
    line_data['incident_date'] = line_data['incident_date'].dt.to_timestamp()
    fig_line = px.line(line_data, x='incident_date', y='count', color='CompanyGroup', title='Monthly Incidents by Company')

    # --- Pie chart: Total incidents by company ---
    pie_data = df['CompanyGroup'].value_counts().reset_index()
    pie_data.columns = ['CompanyGroup', 'count']
    fig_pie = px.pie(pie_data, names='CompanyGroup', values='count', title='Incident Share by Company')

    # --- Bar chart: Severity by Month ---
    df['Month'] = df['incident_date'].dt.month_name()
    df = df.dropna(subset=['Month'])
    fig_hist = px.histogram(
        df,
        x='Month',
        color='severity',
        barmode='group',
        category_orders={'Month': [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]},
        title='Incident Severity by Month',
        labels={'Month': 'Month of Incident', 'count': 'Incident Count'}
    )

    ride_type_counts = df["ride_type"].value_counts().reset_index()
    ride_type_counts.columns = ["ride_type", "count"]
    fig_ride_type = px.bar(
        ride_type_counts,
        x="ride_type",
        y="count",
        title="Incident Count by Ride Type",
        labels={"ride_type": "Ride Type", "count": "Number of Incidents"}
    )

    gender_counts = df["gender"].value_counts().reset_index()
    gender_counts.columns = ["gender", "count"]
    fig_gender = px.pie(
        gender_counts,
        names="gender",
        values="count",
        title="Incident Distribution by Gender"
    )

    # Define the desired age group order
    distributions = load_distributions()

    # Define desired order
    age_order = list(reversed(distributions['age_group']))

    # All expected combinations
    severity_order = ["Minor", "Moderate", "Severe", "Fatal"]
    expected = pd.DataFrame(itertools.product(age_order, severity_order), columns=["age_group", "severity"])

    # Group actual data
    grouped = df.groupby(["age_group", "severity"]).size().reset_index(name="count")

    # Merge with all expected combinations (fill missing with 0)
    grouped = expected.merge(grouped, on=["age_group", "severity"], how="left").fillna(0)

    # Normalize within each age group
    grouped["percentage"] = grouped.groupby("age_group")["count"].transform(
        lambda x: x / x.sum() if x.sum() > 0 else 0
    )

    # Now pivot is guaranteed to work
    grouped["age_group"] = pd.Categorical(grouped["age_group"], categories=reversed(age_order), ordered=True)
    grouped["severity"] = pd.Categorical(grouped["severity"], categories=severity_order, ordered=True)

    heatmap_df = grouped.pivot(index="age_group", columns="severity", values="percentage").fillna(0)

    # Plot
    fig_age_severity = px.imshow(
        heatmap_df,
        text_auto='.1%',
        color_continuous_scale='Blues',
        labels=dict(color="Proportion"),
        title="Severity Distribution by Age Group (Normalized)"
    )

    park_counts = df["theme_park"].value_counts().reset_index()
    park_counts.columns = ["theme_park", "count"]
    fig_by_park = px.bar(
        park_counts,
        x="theme_park",
        y="count",
        title="Incident Count by Theme Park",
        labels={"theme_park": "Theme Park", "count": "Number of Incidents"}
    )


    severity_levels = ["Minor", "Moderate", "Severe", "Critical"]
    severity_counts = df['severity'].value_counts().reindex(severity_levels, fill_value=0).reset_index()
    severity_counts.columns = ['severity_level', 'count']

    fig_bar_severity = bar(severity_counts,
                           x='severity_level', y='count',
                           labels={'severity_level': 'Severity', 'count': 'Count'},
                           title='Incidents by Severity')

    # --- New: Severity by Symptom Type (Stacked Bar) ---
    df_symptom_severity = df.dropna(subset=['injury_type', 'severity'])
    fig_severity_by_symptom = px.histogram(
        df_symptom_severity,
        x='injury_type',
        color='severity',
        barmode='stack',
        title='Incident Severity by Symptom Type',
        labels={'injury_type': 'Symptom Type', 'severity': 'Severity', 'count': 'Incident Count'}
    )

    # --- Severity Distribution (Pie Chart) ---
    severity_counts = df['severity'].dropna().value_counts().reset_index()
    severity_counts.columns = ['severity', 'count']
    fig_severity_pie = px.pie(
        severity_counts,
        names='severity',
        values='count',
        title='Overall Incident Severity Distribution'
    )

    # --- Most Incidents (Pie Chart) ---
    # Group by theme park and ride name, count incidents
    # Group by theme park and ride name, count incidents
    incident_counts = (
        df.groupby(["theme_park", "ride_name"])
        .size()
        .reset_index(name="incident_count")
        .sort_values(by="incident_count", ascending=False)
    )

    # Limit to top 10 rides for readability
    top_rides = incident_counts.head(10).copy()

    # Combine theme park and ride name for label clarity
    top_rides["label"] = top_rides["ride_name"] + " (" + top_rides["theme_park"] + ")"

    # Create Plotly pie chart
    fig_most_incidents = px.pie(
        top_rides,
        names="label",
        values="incident_count",
        title="Top 10 Rides by Incident Count"
    )

    return {
        'plot_line': pio.to_html(fig_line, full_html=False),
        'plot_pie': pio.to_html(fig_pie, full_html=False),
        'plot_bar': pio.to_html(fig_severity_by_coaster_era, full_html=False),
        'plot_hist': pio.to_html(fig_hist, full_html=False),
        'plot_ride_type': pio.to_html(fig_ride_type, full_html=False),
        'plot_gender': pio.to_html(fig_gender, full_html=False),
        'plot_age_severity': pio.to_html(fig_age_severity, full_html=False),
        'plot_by_park': pio.to_html(fig_by_park, full_html=False),
        'plot_severity_by_symptom': pio.to_html(fig_severity_by_symptom, full_html=False),
        'plot_severity_pie': pio.to_html(fig_severity_pie, full_html=False),
        'most_incidents_pie': pio.to_html(fig_most_incidents, full_html=False),
    }
