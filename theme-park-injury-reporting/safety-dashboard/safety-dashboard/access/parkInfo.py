import pandas as pd
from sqlalchemy import Column, Integer, String, delete, inspect, Float, text
from access.db import ParkDatabase, ParkBase


# https://www.kaggle.com/code/mcpenguin/rollercoaster-database-data-collection/notebook
class Coaster(ParkBase):
    __tablename__ = "coasters"


    Ride_Name = Column(String)
    Park_Name = Column(String)
    Opening_Date = Column(String)
    Type = Column(String)
    Manufacturer = Column(String)
    Height = Column(Float)
    Length = Column(Float)
    Speed = Column(Float)
    Inversions = Column(String)
    Duration = Column(String)
    Capacity = Column(Float)
    Cost = Column(String)
    Drop = Column(Float)
    Max_Vertical_Angle = Column(String)
    Park_Number = Column(Integer)
    Ride_Number = Column(Float, primary_key=True)

    launched = Column(Integer)
    inverted = Column(Integer)
    powered = Column(Integer)
    bobsled = Column(Integer)
    junior = Column(Integer)
    dive = Column(Integer)
    suspended = Column(Integer)
    flying = Column(Integer)
    family = Column(Integer)
    enclosed = Column(Integer)
    boomerang = Column(Integer)
    shuttle = Column(Integer)
    motorbike = Column(Integer)
    spinning = Column(Integer)
    wing = Column(Integer)
    stand_up = Column(Integer)
    steel = Column(Integer)
    wood = Column(Integer)
    unknown = Column(Integer)

    material = Column(String)
    Opening_Year = Column(String)

    G_force = Column("G-force", String)
    stand_up = Column("stand-up", Integer)
    fourth_dimension = Column("4th dimension", Integer)
    mine_train = Column("mine train", Integer)
    virtual_reality = Column("virtual reality", Integer)
    wild_mouse = Column("wild mouse", Integer)
    out_and_back = Column("out and back", Integer)
    dual_tracked = Column("dual-tracked", Integer)
    single_rail = Column("single-rail", Integer)
    euro_fighter = Column("euro-fighter", Integer)


class Ride(ParkBase):
    __tablename__ = "rides"

    Ride_Number = Column(Integer, primary_key=True, autoincrement=True)
    Park_Number = Column(Integer)

    Ride_Name = Column(String)
    Ride_Link = Column(String)


class Park(ParkBase):
    __tablename__ = "parks"

    Park_Number = Column(Integer, primary_key=True)
    Park_Name = Column(String)
    Owner_Name = Column(String)
    Owner_ID = Column(Integer)
    City = Column(String)
    State = Column(String)
    Country = Column(String)
    Continent = Column(String)
    Country_Code = Column(String)
    Latitude = Column(String)
    Longitude = Column(String)
    Time_Zone = Column(String)

    _2006 = Column("2006", Integer)
    _2007 = Column("2007", Integer)
    _2008 = Column("2008", Integer)
    _2009 = Column("2009", Integer)
    _2010 = Column("2010", Integer)
    _2011 = Column("2011", Integer)
    _2012 = Column("2012", Integer)
    _2013 = Column("2013", Integer)
    _2014 = Column("2014", Integer)
    _2015 = Column("2015", Integer)
    _2016 = Column("2016", Integer)
    _2017 = Column("2017", Integer)
    _2018 = Column("2018", Integer)
    _2019 = Column("2019", Integer)
    _2020 = Column("2020", Integer)
    _2021 = Column("2021", Integer)
    _2022 = Column("2022", Integer)


class RideHistoryByYear(ParkBase):
    __tablename__ = "ride_history_by_year"

    Ride_Number = Column(String, primary_key=True)
    Park_Number = Column(Integer, primary_key=True)
    Year = Column(Integer, primary_key=True)
    Average_Wait = Column(Float)
    Average_Maximum_Wait = Column(Float)



class RideHistoryByMonth(ParkBase):
    __tablename__ = "ride_history_by_month"

    Ride_Number = Column(String, primary_key=True)
    Park_Number = Column(Integer, primary_key=True)
    Year = Column(Integer, primary_key=True)
    Month = Column(String, primary_key=True)
    Average_Wait = Column(Integer)
    Average_Maximum_Wait = Column(Integer)


class RideHistoryByDay(ParkBase):
    __tablename__ = "ride_history_by_day"

    Ride_Number = Column(String, primary_key=True)
    Park_Number = Column(Integer, primary_key=True)
    Day_of_Week = Column(String, primary_key=True)
    Year = Column(Integer, primary_key=True)
    Average_Wait = Column(Integer)
    Average_Maximum_Wait = Column(Integer)


class RideHistoryByHour(ParkBase):
    __tablename__ = "ride_history_by_hour"

    Ride_Number = Column(String, primary_key=True)
    Park_Number = Column(Integer, primary_key=True)
    Year = Column(Integer, primary_key=True)
    Hour = Column(Integer, primary_key=True)
    Average_Wait = Column(Integer)
    Average_Maximum_Wait = Column(Integer)

def clean_orphaned_records():
    db = ParkDatabase.instance()
    session = db.get_session()

    session.execute(delete(Coaster).where(Coaster.Park_Number == None))
    session.execute(delete(Ride).where(Ride.Park_Number == None))
    session.commit()
    session.close()

def check_park_duplicates(engine):
    query = """
    SELECT Park_Number, COUNT(*) as cnt
    FROM parks
    GROUP BY Park_Number
    HAVING cnt > 1
    """
    with engine.connect() as conn:
        results = conn.execute(text(query)).fetchall()
        if not results:
            print("No duplicated Park_Number values.")
        else:
            print(f"Found {len(results)} duplicated parks:")
            for row in results:
                print(row)

def orm_objects_to_dataframe(results, model_class):
    """
    Convert a list of ORM objects to a DataFrame using the actual SQL column names
    (including those with dashes or reserved keywords), while accessing them through
    their corresponding Python-safe attribute names.
    """
    # Create a mapping from database column name → Python attribute name
    column_map = {
        column.name: attr.key
        for attr in model_class.__mapper__.attrs
        for column in attr.columns
    }

    null_count = sum(1 for r in results if r is None)
    if null_count:
        print(f"Warning: {null_count} null rows in query results.")

    records = []
    for obj in results:
        record = {
            db_col: getattr(obj, attr_name)
            for db_col, attr_name in column_map.items()
        }
        records.append(record)

    return pd.DataFrame(records)

def load_rides_from_db():
    session = ParkDatabase.instance().get_session()
    try:
        results = session.query(Ride).all()
        return orm_objects_to_dataframe(results, Ride)
    finally:
        session.close()

def load_parks_from_db():
    session = ParkDatabase.instance().get_session()
    try:
        results = session.query(Park).all()
        return orm_objects_to_dataframe(results, Park)
    finally:
        session.close()

def load_coasters_from_db():
    session = ParkDatabase.instance().get_session()
    try:
        results = session.query(Coaster).all()

        # Debugging: Check for None entries and summarize
        nulls = [i for i, r in enumerate(results) if r is None]
        print(f"Retrieved {len(results)} coasters from DB.")
        if nulls:
            print(f"Found {len(nulls)} null entries at positions: {nulls}")
        else:
            print("No null coaster records found.")

        return orm_objects_to_dataframe(results, Coaster)
    finally:
        session.close()


def drop_null_coasters():
    engine = ParkDatabase.instance().get_engine()
    with engine.connect() as conn:
        # Drop any coaster where critical fields are NULL
        result = conn.execute(text("""
            DELETE FROM coasters
            WHERE Ride_Name IS NULL
               OR Ride_Number IS NULL
               OR Park_Name IS NULL
        """))
        print(f"Deleted {result.rowcount} bad coaster row(s).")

from sqlalchemy import text

def drop_null_parks():
    engine = ParkDatabase.instance().get_engine()
    with engine.connect() as conn:
        # Drop any coaster where critical fields are NULL
        result = conn.execute(text("""
            DELETE FROM parks
            WHERE Park_Name IS NULL
               OR Park_Number IS NULL
        """))
        print(f"Deleted {result.rowcount} bad park row(s).")



if __name__ == "__main__":
    # Initialize the park database
    park_db = ParkDatabase.instance()
    park_db.init()
    park_engine = park_db.get_engine()

    # List of expected tables
    expected_tables = [
        "coasters", "parks", "rides",
        "ride_history_by_year", "ride_history_by_month",
        "ride_history_by_day", "ride_history_by_hour"
    ]

    # Check for presence of tables
    inspector = inspect(park_engine)
    for table_name in expected_tables:
        if not inspector.has_table(table_name):
            print(f"Table '{table_name}' does NOT exist in park_info.db")
        else:
            print(f"Table '{table_name}' is present in park_info.db")


    engine = ParkDatabase.instance().get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT Ride_Number, COUNT(*) as cnt
            FROM coasters
            GROUP BY Ride_Number
            HAVING cnt > 1
        """)).fetchall()

        print(f"Found {len(result)} duplicates.")
        for row in result:
            print(row)

    DUPLICATE_RIDE_NUMBERS_QUERY = """
    SELECT *
    FROM coasters
    WHERE Ride_Number IN (
        SELECT Ride_Number
        FROM coasters
        GROUP BY Ride_Number
        HAVING COUNT(*) > 1
    )
    ORDER BY Ride_Number
    """

    with engine.connect() as conn:
        rows = conn.execute(text(DUPLICATE_RIDE_NUMBERS_QUERY)).mappings().all()
        for row in rows:
            print(dict(row))

    check_park_duplicates(engine)

    # remove duplicate coasters

    with engine.begin() as conn:  # <-- commits automatically on success
        # Keep only Space Mountain at Disneyland
        conn.execute(text("""
            DELETE FROM coasters
            WHERE Ride_Number = 284.0
            AND NOT (Ride_Name = 'Space Mountain' AND Park_Name = 'Disneyland')
        """))

        # Drop all of the corrupted 6548.0 entries
        conn.execute(text("""
            DELETE FROM coasters
            WHERE Ride_Number = 6548.0
        """))

    # If key tables exist, run cleaning
    if inspector.has_table("coasters") and inspector.has_table("parks"):
        print("Cleaning orphaned coaster and ride records...")
        clean_orphaned_records()

