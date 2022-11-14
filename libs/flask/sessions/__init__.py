import os
from .ext import Session
from flask import Flask


'''
    WARNING: 
    
    This adds stateful behavior, which is usually frowned upon when used in a
    serverless context.
    
    This also adds a couple houndred ms of overhead.
    
    This should avoid if at all possible.
'''


def __init__(app:Flask) -> Session:
    app.config["SECRET_KEY"] = os.environ["flask_secret_key"]
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_COOKIE_SECURE"] = False if os.environ.get("dev") else True
    app.config["REMEMBER_COOKIE_SECURE"] = False if os.environ.get("dev") else True
    app.config["SESSION_TYPE"] = "azurestoragetable"
    app.config["SESSION_AZURE_STORAGE_TABLE_NAME"] = os.environ.get('flask_session_table') if os.environ.get('flask_session_table') else 'flask_sessions'

    return Session(app)

