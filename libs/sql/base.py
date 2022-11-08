import uuid
from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.sql import func
from ..flask import db

Base = db.Model

def genUUID():
    return str(uuid.uuid4())

class Abstract(Base):
    """
    Abstract model for database tables
    """
    id = Column(String, primary_key=True, default=genUUID)
    time_created = Column(TIMESTAMP, server_default=func.now(), __read_only__=True)
    time_modified = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp(), __read_only__=True)
    
    JSONAPI = {
        "methods": ['GET','POST','DELETE','PATCH'],
        "allow_to_many_replacement": True,
        "allow_delete_from_to_many_relationships": True
    }
