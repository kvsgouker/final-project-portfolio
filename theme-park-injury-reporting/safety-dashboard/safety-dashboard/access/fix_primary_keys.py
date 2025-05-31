import os
from sqlalchemy import create_engine, MetaData, Table, Column, text
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError

from access.db import ParkDatabase

# You define the correct PKs here:
PRIMARY_KEYS = {
    "coasters": ["Ride_Number"],
    "rides": ["Ride_Number"],
    "parks": ["Park_Number"],
    "ride_history_by_year": ["Ride_Number", "Park_Number", "Year"],
    "ride_history_by_month": ["Ride_Number", "Park_Number", "Year", "Month"],
    "ride_history_by_day": ["Ride_Number", "Park_Number", "Day_of_Week", "Year"],
    "ride_history_by_hour": ["Ride_Number", "Park_Number", "Year", "Hour"],
}

def has_primary_key(engine, table_name):
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[-1] > 0 for row in result)

def fix_primary_key(engine, table_name, pk_columns):
    print(f"Checking table: {table_name}")
    if has_primary_key(engine, table_name):
        print(f"{table_name} already has a primary key. Skipping.\n")
        return

    metadata = MetaData()
    metadata.reflect(bind=engine)
    old_table = Table(table_name, metadata, autoload_with=engine)

    temp_table_name = f"{table_name}_fixed"
    print(f"{table_name} is missing a primary key — creating temporary table: {temp_table_name}")

    # Define columns for the new table, marking primary key fields
    new_columns = []
    for col in old_table.columns:
        kwargs = dict(col.info)
        if col.name in pk_columns:
            kwargs["primary_key"] = True
        new_columns.append(Column(col.name, col.type, **kwargs))

    new_table = Table(temp_table_name, MetaData(), *new_columns)

    with engine.connect() as conn:
        print(f"Dropping existing {temp_table_name} if it exists...")
        conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))

    print(f"Creating new table: {temp_table_name}")
    new_table.create(bind=engine)

    with engine.begin() as conn:  # ensures commit
        print(f"Reading rows from {table_name}...")
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = [dict(row) for row in result.mappings()]

        total_rows = len(rows)

        valid_rows = [row for row in rows if all(row.get(pk) is not None for pk in pk_columns)]
        skipped_rows = total_rows - len(valid_rows)

        print(f"Total rows read: {total_rows}")
        print(f"Rows with all PKs: {len(valid_rows)}")
        print(f"Rows skipped (missing PKs): {skipped_rows}")

        if valid_rows:
            print(f"Inserting valid rows into {temp_table_name}...")
            conn.execute(new_table.insert(), valid_rows)
        else:
            print(f"No valid rows to insert into {temp_table_name}. Skipping insertion.")

        print(f"Replacing original table: {table_name}")
        conn.execute(text(f"DROP TABLE {table_name}"))
        conn.execute(text(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}"))
        print(f"Replacement complete. {table_name} now has a primary key.\n")


def fix_all_primary_keys():
    ParkDatabase.instance().init()
    engine = ParkDatabase.instance().get_engine()

    for table_name, pk_fields in PRIMARY_KEYS.items():
        fix_primary_key(engine, table_name, pk_fields)




def replace_fixed_tables():
    engine = ParkDatabase.instance().get_engine()
    pairs = [
        ("coasters", "coasters_fixed"),
        ("parks", "parks_fixed"),
        ("rides", "rides_fixed"),
        ("ride_history_by_year", "ride_history_by_year_fixed"),
        ("ride_history_by_month", "ride_history_by_month_fixed"),
        ("ride_history_by_day", "ride_history_by_day_fixed"),
        ("ride_history_by_hour", "ride_history_by_hour_fixed"),
    ]

    with engine.begin() as conn:
        for original, fixed in pairs:
            print(f"Attempting to replace {original} with {fixed}")
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {original}"))
                conn.execute(text(f"ALTER TABLE {fixed} RENAME TO {original}"))
                print(f"Success: {original} replaced.")
            except SQLAlchemyError as e:
                print(f"Failed to replace {original}: {e}")


if __name__ == "__main__":
    fix_all_primary_keys()


