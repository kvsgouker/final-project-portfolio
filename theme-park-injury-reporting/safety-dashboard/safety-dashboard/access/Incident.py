from sqlalchemy import Column, Integer, String, Float
from access.db import IncidentDatabase, IncidentBase


class RealIncident(IncidentBase):
    __tablename__ = "real_incidents"
    id = Column(Integer, primary_key=True)
    ride_number = Column(Float)
    park_number = Column(Integer)
    company = Column(String)
    theme_park = Column(String)
    ride_name = Column(String)
    incident_date = Column(String)
    age_group = Column(String)
    gender = Column(String)
    injury_location = Column(String)
    severity = Column(String)
    medical_attention = Column(String)
    injury_type = Column(String)
    ride_status = Column(String)
    contributing_factor = Column(String)
    description = Column(String)
    submission_time = Column(String)

class SyntheticIncident(IncidentBase):
    __tablename__ = "synthetic_incidents"
    id = Column(Integer, primary_key=True)
    ride_number = Column(Float)
    park_number = Column(Integer)
    company = Column(String)
    theme_park = Column(String)
    ride_name = Column(String)
    incident_date = Column(String)
    age_group = Column(String)
    gender = Column(String)
    injury_location = Column(String)
    severity = Column(String)
    medical_attention = Column(String)
    injury_type = Column(String)
    ride_status = Column(String)
    contributing_factor = Column(String)
    description = Column(String)
    submission_time = Column(String)

if __name__ == "__main__":
    IncidentDatabase.instance().init()
    IncidentBase.metadata.create_all(bind=IncidentDatabase.instance().get_engine())

