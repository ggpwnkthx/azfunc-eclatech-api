import os
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base,genUUID,db

#Location table
class Abstract(Base):
    """
    Abstract model for database tables
    """
    __tablename__ = 'abstract_base_table'
    id = db.Column(String, primary_key=True, default=genUUID)
    time_created = db.Column(TIMESTAMP, server_default=func.now(), read_only=True)
    time_modified = db.Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp(), read_only=True)
    
    JSONAPI = {
        "methods": ['GET','POST','DELETE','PATCH'],
        "allow_to_many_replacement": True,
        "allow_delete_from_to_many_relationships": True
    }