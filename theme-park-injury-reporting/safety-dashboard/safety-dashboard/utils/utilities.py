"""
Project Name: Star Power
File: utilities.py

Miscellaneous functions.
Author: Kyle Salgado-Gouker
"""

import json

import pandas as pd
from PIL import Image, ImageFont, ImageDraw
from tabulate import tabulate
import ast

from config.filter_config import filter_fields


def pretty_print_df_info_with_nans(df):
    """
    Pretty-print metadata of a dataframe with NaNs and unique values.

    Args:
        df (pd.DataFrame): The DataFrame to display.

    Returns:
        str: A formatted string representing the DataFrame's metadata.
    """
    # Show the column names, data types, count of NaN values, and unique values.
    nunique_safe = {}
    for col in df.columns:
        try:
            nunique_safe[col] = df[col].nunique()
        except TypeError:
            nunique_safe[col] = "unhashable"

    columns_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes,
        'NaN Count': df.isnull().sum(),
        'Unique Values': [nunique_safe[col] for col in df.columns]
    }).reset_index(drop=True)

    # Try casting NaN counts to int where possible
    columns_info['NaN Count'] = pd.to_numeric(columns_info['NaN Count'], errors='coerce').astype("Int64")

    table = tabulate(columns_info, headers='keys', tablefmt='pretty', showindex="always")
    return f"Dataframe Information:\n{table}"



def show_df_info(df, title):
    """
    Pretty-print metadata of a dataframe with NaNs and unique values and a title.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        title (str): The title of the dataframe.

    Returns:
        str: A formatted string representing the DataFrame's metadata.
    """
    return (f"\nDataframe information for {title}:\n" + pretty_print_df_info_with_nans(df) +"\n" +
           f"\nThere are {df.shape[0]} rows and {df.shape[1]} columns of information.\n")


def pretty_print_df_with_json(df, rows=None, interesting_columns=None, headers='keys', max_width=120):
    """
    Pretty-print a pandas DataFrame using the `tabulate` library, with special handling for JSON-like columns.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        rows (int, optional): The number of rows to display from the top. Defaults to None (shows all).
        interesting_columns (list, optional): A list of columns to include. If None, all columns are shown.
        headers (str): Header formatting for tabulate. Defaults to 'keys'.
        max_width (int): Max width for each cell's string output.

    Returns:
        str: A formatted string representing the DataFrame.
    """

    def try_pretty_json(val):
        if isinstance(val, str) and (val.startswith('[') or val.startswith('{')):
            try:
                parsed = ast.literal_eval(val)
                if isinstance(parsed, list):
                    return '[{} items] {}'.format(len(parsed), json.dumps(parsed[:2], indent=2))  # show first 2 items
                if isinstance(parsed, dict):
                    return json.dumps(parsed, indent=2)
            except:
                return str(val)[:max_width]
        return str(val)[:max_width]

    if rows is not None:
        df = df.head(rows)

    if interesting_columns:
        df = df[interesting_columns]

    # Apply formatting
    formatted_df = df.copy()
    for col in formatted_df.columns:
        formatted_df[col] = formatted_df[col].apply(try_pretty_json)

    return tabulate(formatted_df, headers=headers, tablefmt='pretty', showindex=False)


def pretty_print_df(
    df,
    rows=None,
    interesting_columns=None,
    headers='keys',
    currency_cols=None,
    rounded_cols=None,
    currency_dec=2,
    round_dec=2
):
    """
    Pretty-print a DataFrame using `tabulate`, with optional currency and rounded formatting.

    Args:
        df (pd.DataFrame): The DataFrame to print.
        rows (int): Limit number of rows to show.
        interesting_columns (list): Limit to these columns.
        headers (str): Header type for tabulate.
        currency_cols (list): List of columns to format as currency.
        rounded_cols (list): List of columns to round.
        currency_dec (int): Decimal places for currency.
        round_dec (int): Decimal places for normal floats.

    Returns:
        str: Formatted DataFrame string.
    """
    if rows is not None:
        df = df.head(rows)

    if interesting_columns:
        df = df[interesting_columns]

    # Define formatting
    def format_val(col, val):
        try:
            if pd.isnull(val):
                return ""
            if currency_cols and col in currency_cols:
                return f"${val:,.{currency_dec}f}"
            elif rounded_cols and col in rounded_cols:
                return f"{val:.{round_dec}f}"
            else:
                return val
        except Exception:
            return val

    # Format the values
    formatted_data = [
        [format_val(col, row[col]) for col in df.columns]
        for _, row in df.iterrows()
    ]

    return tabulate(formatted_data, headers=df.columns, tablefmt='pretty', showindex=False)


def prepare_for_numeric_modeling(df, cols):
    """
    Pretty-print metadata of a dataframe with NaNs and unique values and a title.

    Args:
        df (pd.DataFrame): The DataFrame to display.
        cols (list): A list of column names. These will be cast to numbers using panda.

    Returns:
        pd.DataFrame: A dataframe without NaNs with columns coerced to numeric values.
    """
    df = df.dropna(subset=cols).copy()
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna(subset=cols)


def print_formatted_test_stat(value, dec=2):
    """
    Formats a numeric value into a formatted string of val with dec decimal places.

    Args:
        value (str): value to format
        dec (int): number of decimal places to show

    Returns:
        str: A formatted string representing the test statistic.
    """
    format_string = "{:.{dec}f}"
    return format_string.format(value, dec=dec)


def print_currency_test_stat(value, dec=2):
    """
    Formats a currency value into a formatted string of val with dec decimal places.

    Args:
        value (str): value to format
        dec (int): number of decimal places to show

    Returns:
        str: A formatted string representing the test statistic.
    """
    format_string = "{:,.{dec}f}"
    return format_string.format(value, dec=dec)


def add_hint_to_filename(root, hint):
    """
    Adds "hint" to help distinguish similar graph filenames.

    Args:
        root (str): base name of graph plot image filename
        hint (str): hint for filename to distinguish it

    Returns:
        str: file name with "hint" embedded
    """
    if hint is not None and len(hint) > 0:
        return f"{root}_{hint}"
    else:
        return root


def add_hint_to_title(root, hint):
    """
    Adds "hint" to help distinguish graphs by adding hint to title.

    Args:
        root (str): base name of graph plot.
        hint (str): hint to distinguish it.

    Returns:
        str: Title with "hint" embedded
    """
    if hint is not None and len(hint) > 0:
        return f"{root}: {hint}"
    else:
        return root


# white
TABLE_BACKGROUND_COLOR = (255, 255, 255)
# black
TABLE_FONT_COLOR = (0, 0, 0)
TABLE_FONT_SIZE = 12
TABLE_WIDTH = 600
TABLE_HEIGHT = 800
TYPEFACE_FILE = "/Library/Fonts/Menlo.ttc"


# Prints a title decorated by stars.
def format_fancy_title(title):
    # Calculate the length of the title
    title_length = len(title)
    # format title with decoration
    title = "*" * (title_length + 4) + "\n" + f"* {title} *" + "\n" + "*" * (title_length + 4) + "\n"
    return title


def draw_text(image_filename, text, title="", width=TABLE_WIDTH, height=TABLE_HEIGHT,
             background_color=TABLE_BACKGROUND_COLOR, font_name=TYPEFACE_FILE, font_color=TABLE_FONT_COLOR,
             font_size=TABLE_FONT_SIZE):
    # Create an image with white background
    image = Image.new('RGB', (width, height), background_color)
    # Set the font style and size
    font = ImageFont.truetype(font_name, font_size)
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    # Calculate the position to start drawing the table
    x, y = 10, 10
    # Add an optional title.
    if len(title) > 0:
        text = format_fancy_title(title) + "\n" + text
    # Draw the table onto the image
    draw.text((x, y), text, font=font, fill=font_color)
    # Save the image
    image.save(image_filename)
    return text


def draw_table(image_filename, table, title="", width=TABLE_WIDTH, height=TABLE_HEIGHT,
              background_color=TABLE_BACKGROUND_COLOR, font_name=TYPEFACE_FILE, font_color=TABLE_FONT_COLOR,
              font_size=TABLE_FONT_SIZE):
    text = draw_text(image_filename, table, title, width, height, background_color, font_name, font_color, font_size)
    print(text)
    return text


def draw_report(image_filename, text, title="", width=TABLE_WIDTH, height=TABLE_HEIGHT,
               background_color=TABLE_BACKGROUND_COLOR, font_name=TYPEFACE_FILE, font_color=TABLE_FONT_COLOR,
               font_size=TABLE_FONT_SIZE):
    if len(title) > 0:
        draw_text(image_filename, text, title, width, height, background_color, font_name, font_color, font_size)
        print(format_fancy_title(title))
    else:
        draw_text(image_filename, text)
    print(text)
    return text


# formats long tables side by side.
def combine_tables(table1, table2, table3):
    # Split the input strings into rows
    table1_rows = table1.strip().split("\n")
    table2_rows = table2.strip().split("\n")
    table3_rows = table3.strip().split("\n")

    max_row_count = max(len(table1_rows), len(table2_rows), len(table3_rows))
    combined_table = ""

    for row_idx in range(max_row_count):
        # Get the corresponding rows from each table
        table1_row = table1_rows[row_idx] if row_idx < len(table1_rows) else ""
        table2_row = table2_rows[row_idx] if row_idx < len(table2_rows) else ""
        table3_row = table3_rows[row_idx] if row_idx < len(table3_rows) else ""

        # Combine the rows into a single row
        combined_row = f"{table1_row} {table2_row} {table3_row}".strip()

        # Add the combined row to the overall table
        combined_table += combined_row + "\n"

    return combined_table


# Mapping dictionary for word representation of numbers to integers
word_to_number = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def apply_filters(df, args):
    for field in filter_fields:
        name = field["name"]
        if field["type"] == "checkbox" and args.getlist(name):
            df = df[df[name].isin(args.getlist(name))]
        elif field["type"] == "select" and args.get(name):
            df = df[df[name] == args.get(name)]
        elif field["type"] == "date" and name in ["start_date", "end_date"]:
            if args.get("start_date") and args.get("end_date"):
                df = df[
                    (df["incident_date"] >= args.get("start_date")) &
                    (df["incident_date"] <= args.get("end_date"))
                ]
    return df

