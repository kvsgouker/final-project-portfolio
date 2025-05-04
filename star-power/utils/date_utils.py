"""
Project Name: Star Power
File: data_utils.py
Author: Kyle Salgado-Gouker

Data validation function.

"""

from datetime import datetime


def validate_date(date_text, format='%Y-%m-%d'):
    try:
        # Assuming your date format is 'YYYY-MM-DD'
        datetime.strptime(date_text, format)
        return True
    except ValueError:
        return False
