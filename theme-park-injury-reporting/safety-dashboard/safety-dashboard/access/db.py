import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

IncidentBase = declarative_base()
ParkBase = declarative_base()

class IncidentDatabase:
    _instance = None

    def __init__(self):
        self._engine = None
        self._SessionLocal = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init(self):
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set!")

        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self._engine = create_engine(database_url, echo=False)
        self._SessionLocal = sessionmaker(bind=self._engine)

    def get_engine(self):
        if not self._engine:
            raise RuntimeError("Database engine not initialized. Call `init()` first.")
        return self._engine

    def get_session(self):
        if not self._SessionLocal:
            raise RuntimeError("Database session factory not initialized. Call `init()` first.")
        return self._SessionLocal()


class ParkDatabase:
    _instance = None

    def __init__(self):
        self._engine = None
        self._SessionLocal = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def init(self):
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "park_info.db")
        db_url = f"sqlite:///{os.path.abspath(db_path)}"

        self._engine = create_engine(db_url, echo=False)
        self._SessionLocal = sessionmaker(bind=self._engine)

    def get_engine(self):
        if not self._engine:
            raise RuntimeError("Park database engine not initialized. Call `init()` first.")
        return self._engine

    def get_session(self):
        if not self._SessionLocal:
            raise RuntimeError("Park database session not initialized. Call `init()` first.")
        return self._SessionLocal()
