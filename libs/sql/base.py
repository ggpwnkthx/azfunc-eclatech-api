from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()
Base = db.Model


def genUUID():
    return str(uuid.uuid4().hex)
