"""
Overview:
The `print_output.py` module provides functions to display and summarize Pandas DataFrames
in a user-friendly format. It utilizes the `tabulate` library for pretty-printing and
includes methods for displaying DataFrame information, including NaN counts and data types.

Functions:

1. pretty_print_df():
   - Prints a DataFrame in a tabular format with optional row limits and column selection.
   - Parameters:
     - df (DataFrame): The DataFrame to be printed.
     - rows (int, optional): The number of rows to display. Defaults to None (displays all rows).
     - interesting_columns (list, optional): Specific columns to display.
        Defaults to None (displays all columns).
     - headers (str or list, optional): Header format for tabulate. Defaults to 'keys'.
   - Prints the DataFrame using `tabulate` for improved readability.

2. pretty_print_df_info_with_nans():
   - Displays detailed column information, including data types and NaN counts, for a DataFrame.
   - Parameters:
     - df (DataFrame): The DataFrame for which column information is displayed.
   - Returns:
     - columns_info (DataFrame): A DataFrame containing column names, data types, and NaN counts.
   - Prints the information in a tabular format using `tabulate`.

3. show_df_info():
   - Prints a summary of a DataFrame, including column information and overall shape.
   - Parameters:
     - df (DataFrame): The DataFrame to be summarized.
     - title (str): A title for the printed output.
   - Calls `pretty_print_df_info_with_nans()` and prints the number of rows and columns in the DataFrame.

4. write_df_metadata_to_df():
   - Creates a DataFrame containing metadata about columns, including data types and NaN counts.
   - Parameters:
     - df (DataFrame): The DataFrame from which metadata is extracted.
   - Returns:
     - columns_info (DataFrame): A DataFrame containing metadata (column names, data types, & NaN counts).

Dependencies:
- `tabulate`: Used for pretty-printing DataFrame outputs in a tabular format.
- `pandas`: Used for DataFrame manipulation and metadata extraction.

Usage:
- Use `pretty_print_df()` for printing DataFrames with customized views
        (selected columns and limited rows).
- Use `pretty_print_df_info_with_nans()` or `show_df_info()` for detailed DataFrame summaries,
        including NaN counts.
- Use `write_df_metadata_to_df()` when you need to extract and return
        DataFrame metadata for further processing.

"""

from tabulate import tabulate
import pandas as pd


def pretty_print_df(df, rows=None, interesting_columns=None, headers='keys'):
    if rows is not None:
        df = df.head(rows)  # rows parameter limits the DataFrame to the specified number of rows
    if interesting_columns:
        # Filter DataFrame to include only specified columns
        df = df[interesting_columns]
        # Use Tabulate pretty printing.
    print(tabulate(df, headers=headers, tablefmt='pretty', showindex=False))


def pretty_print_df_info_with_nans(df):
    # Show the column names, data types, & count of NaN values.
    columns_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes,
        'NaN Count': df.isnull().sum()
    }).reset_index(drop=True)

    # Convert 'NaN Count' column to int for better display
    columns_info['NaN Count'] = columns_info['NaN Count'].astype(int)

    table = tabulate(columns_info, headers='keys', tablefmt='pretty', showindex="always")
    print(f"Dataframe Information:\n{table}")
    return columns_info


def show_df_info(df, title):
    print(f"\nDataframe information for {title}:\n")
    pretty_print_df_info_with_nans(df)
    print(f"\nThere are {df.shape[0]} rows and {df.shape[1]} columns of information.\n")


def write_df_metadata_to_df(df):
    columns_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes,
        'NaN Count': df.isnull().sum()
    }).reset_index(drop=True)

    # Convert 'NaN Count' column to int for better display
    columns_info['NaN Count'] = columns_info['NaN Count'].astype(int)
    return columns_info
