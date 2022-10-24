from .. import app
from .ext import Session
# from flask_session import Session
import os

app.config["SECRET_KEY"] = os.environ["flask_secret_key"]
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["REMEMBER_COOKIE_SECURE"] = True
app.config["SESSION_TYPE"] = "azurestoragetable"
# app.config["SESSION_TYPE"] = "sqlalchemy"
# app.config["SESSION_SQLALCHEMY_TABLE"] = "flask_sessions"

session = Session(app)
app.session = session

