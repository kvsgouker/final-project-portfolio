import os
import re
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

KEYWORDS = {
    "injury_type": {
        "Fall / Slipped": [r"\bfall(?:en)?\b", r"\bslip(?:ped)?\b", r"\btrip(?:ped)?\b"],
        "Collision": [r"\bcollided?\b", r"\bhit\b", r"\bcrash(?:ed)?\b"],
        "Dizziness / Fainting": [r"\bfaint(?:ed)?\b", r"\bdizz(?:y|iness)\b"],
        "Ride Malfunction": [r"\bstuck\b", r"\bmalfunction\b", r"\bmechanical\b"],
        "Thrown / Ejection": [r"\bthrown\b", r"\beject(?:ed)?\b"],
        "Seizure / Illness": [r"\bseizure\b", r"\bill\b", r"\bsick\b"],
        "Burn / Wound / Cut": [r"\bburn(?:ed)?\b", r"\bcut\b", r"\bwound(?:ed)?\b"],
        "Psychological / Panic": [r"\bpanic\b", r"\bscare\b", r"\banxiety\b"],
    },
    "injury_location": {
        "Head": [r"\bhead\b", r"\bface\b", r"\bforehead\b"],
        "Back": [r"\bback\b", r"\bspine\b", r"\bneck\b"],
        "Arm": [r"\barm\b", r"\bhand\b", r"\bwrist\b"],
        "Leg": [r"\bleg\b", r"\bknee\b", r"\bfoot\b", r"\btoe\b"],
        "Chest": [r"\bchest\b", r"\brib\b", r"\babdomen\b"],
        "Internal": [r"\bstomach\b", r"\binternal\b", r"\borgan\b"],
    },
    "severity": {
        "Serious": [r"\bcritical\b", r"\bserious\b", r"\bemergency\b"],
        "Moderate": [r"\bmoderate\b", r"\bhospital\b", r"\bambulance\b"],
        "Minor": [r"\bminor\b", r"\bscrape\b", r"\bbruise\b"],
    },
    "medical_attention": {
        "Yes": [r"\bhospital\b", r"\btreat(ed)?\b", r"\bmedical\b", r"\bambulance\b"],
        "No": [r"\bno medical\b", r"\bdeclined treatment\b"]
    },
    "ride_status": {
        "In motion": [r"\bduring\b", r"\bin motion\b", r"\brunning\b"],
        "Loading/Unloading": [r"\bloading\b", r"\bunloading\b", r"\bgetting on\b", r"\bdisembark\b"],
        "Emergency stop": [r"\bstopped suddenly\b", r"\bemergency stop\b"],
    },
    "contributing_factor": {
        "Guest behavior": [r"\brunning\b", r"\bhorseplay\b", r"\bignored instructions\b"],
        "Operator error": [r"\boperator\b", r"\bemployee mistake\b", r"\bmiscommunication\b"],
        "Ride malfunction": [r"\bstuck\b", r"\bbrake failure\b", r"\bmechanical\b"],
        "Weather": [r"\brain\b", r"\bslick\b", r"\bwet\b"],
    }
}

def infer_tags_from_description(description):
    result = {
        "injury_type": pd.NA,
        "injury_location": pd.NA,
        "severity": pd.NA,
        "medical_attention": pd.NA,
        "ride_status": pd.NA,
        "contributing_factor": pd.NA,
    }

    if pd.isna(description):
        return result

    text = description.lower()

    for field, categories in KEYWORDS.items():
        for label, patterns in categories.items():
            if any(re.search(pat, text) for pat in patterns):
                # Allow multi-values for location
                if field == "injury_location":
                    current = result.get(field)
                    if pd.isna(current):
                        result[field] = label
                    else:
                        result[field] += f"|{label}"
                else:
                    result[field] = label
                    break  # Stop after first match

    return result

def parse_age_gender(value):
    """
    Extracts age and gender from values like '59 yof' or '68 yom'.
    Returns a tuple: (age_group, gender)
    """
    if pd.isna(value):
        return pd.NA, pd.NA

    # Lowercase and strip for safety
    val = value.lower().strip()

    # Match patterns like '59 yof' or '70 yom'
    match = re.match(r"(\d{1,3})\s*yo[fm]", val)
    if match:
        age = int(match.group(1))

        # Assign to age group
        if age < 10:
            age_group = "<10"
        elif age < 18:
            age_group = "10–17"
        elif age <= 40:
            age_group = "18–40"
        elif age <= 60:
            age_group = "41–60"
        else:
            age_group = "60+"

        # Extract gender
        gender = "Female" if "yof" in val else "Male"
        return age_group, gender

    return pd.NA, pd.NA


def plot_cm(y_true, y_pred, title):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(y_true), yticklabels=np.unique(y_true))
    plt.title(title)
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(f"static/{title.lower().replace(' ', '_')}.png")
    plt.close()

