# filter_config.py
# field types: checkbox, select, text, or date

filter_fields = [
    {
        "name": "age_group",
        "label": "Age Group",
        "type": "checkbox",
        "options": ["Minor", "Teen", "Adult", "Senior"]
    },
    {
        "name": "gender",
        "label": "Gender",
        "type": "checkbox",
        "options": ["Male", "Female", "Nonbinary", "Unknown"]
    },
    {
        "name": "injury_location",
        "label": "Injury Location",
        "type": "checkbox",
        "options": ["Head", "Arm", "Leg", "Torso", "Neck"]
    },
    {
        "name": "severity",
        "label": "Severity",
        "type": "checkbox",
        "options": ["Minor", "Moderate", "Severe", "Fatal"]
    },
    {
        "name": "medical_attention",
        "label": "Medical Attention",
        "type": "checkbox",
        "options": ["No", "First Aid", "Hospital", "Emergency"]
    },
    {
        "name": "injury_type",
        "label": "Injury Type",
        "type": "checkbox",
        "options": ["Laceration", "Fracture", "Burn", "Whiplash", "Bruise"]
    },
    {
        "name": "ride_status",
        "label": "Ride Status",
        "type": "checkbox",
        "options": ["Operating", "Shut down", "Under repair"]
    },
    {
        "name": "contributing_factor",
        "label": "Contributing Factor",
        "type": "checkbox",
        "options": ["Guest behavior", "Mechanical failure", "Weather", "Staff error"]
    },
    {
        "name": "start_date",
        "label": "Start Date",
        "type": "date"
    },
    {
        "name": "end_date",
        "label": "End Date",
        "type": "date"
    }
]

