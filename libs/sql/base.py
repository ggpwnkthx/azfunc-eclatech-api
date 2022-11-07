from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.sql import func

db = SQLAlchemy()
Base = db.Model

def genUUID():
    return str(uuid.uuid4().hex)

class Abstract(Base):
    """
    Abstract model for database tables
    """
    id = db.Column(String, primary_key=True, default=genUUID)
    time_created = db.Column(TIMESTAMP, server_default=func.now(), __read_only__=True)
    time_modified = db.Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp(), __read_only__=True)
    
    JSONAPI = {
        "methods": ['GET','POST','DELETE','PATCH'],
        "allow_to_many_replacement": True,
        "allow_delete_from_to_many_relationships": True
    }
