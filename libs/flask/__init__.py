import logging
from flask import Flask
from libs.flask.db import __init__ as init_db
from libs.flask.sessions import __init__ as init_sessions
from libs.flask.authorization import __init__ as init_authorization
from libs.flask.jsonapi import __init__ as init_jsonapi

# LOG = logging.getLogger('azure')
# LOG.setLevel(logging.WARN)


app = Flask(__name__)
# init_sessions(app)
permission = init_authorization(app)
db = init_db(app)
jsonapi = init_jsonapi(app, db, permission)
