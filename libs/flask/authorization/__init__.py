from py_abac.storage.sql import SQLStorage
from py_abac import PDP, Policy, AccessRequest
from .. import app
from ..identity import whoami
from functools import wraps
from flask import abort
import os

from sqlalchemy.orm import sessionmaker, scoped_session
def get_storage(app, bind=None):
    return SQLStorage(
        scoped_session=scoped_session(
            sessionmaker(
                bind=app.db.engines[bind]
            )
        )
    )

class DynObj:
    None
    
app.permission = DynObj()
def is_allowed(resource, action, context={}):
    return PDP(get_storage(app, bind=os.environ.get("abac_sql_bind"))).is_allowed(
        AccessRequest.from_json({
            "subject": {
                "id": "",
                "attributes": whoami()
            },
            "resource": {
                "id": "",
                "attributes": resource
            },
            "action": {
                "id": "",
                "attributes": action
            },
            "context": context
        })
    )
def check(resource, action, context={}):
    if not is_allowed(resource, action, context):
        abort(403)
app.permission.check = check
    
# Wrapper function to simplify permission checks
def can(resource, action, context={}):
    def wrapper(function):
        @wraps(function)
        def inner(*args, **kwargs):
            check(resource, action, context)
            return function(*args, **kwargs)
        return inner
    return wrapper
app.permission.gatekeeper = can

def add_policy(name:str, rules: dict, description:str = "", effect:str = "allow", targets:dict = {}, priority:int = 0):
    storage = get_storage(app, bind=os.environ.get("abac_sql_bind"))
    policy = Policy.from_json({
        "uid": name,
        "description": description,
        "effect": effect,
        "rules": rules,
        "targets": targets,
        "priority": priority
    })
    storage.add(policy)

def delete_policy(name:str):
    storage = get_storage(app, bind=os.environ.get("abac_sql_bind"))
    storage.delete(name)
    storage.session.commit()
    

    
# from ..flask.authorization import (
#     add_policy as abac_add_policy,
#     delete_policy as abac_delete_policy
# )
# add_policy(
#     name="AllowAllForDevOps",
#     rules={
#         "subject": [
#             {"$.groups": {"condition": "AnyIn", "values": ["1d20defe-43a7-4831-93e0-68ada1afc646"]}},
#         ],
#         "resource": {"$.name": {"condition": "RegexMatch", "value": ".*"}},
#         "action": [
#             {"$.method": {"condition": "RegexMatch", "value": ".*"}},
#         ],
#         "context": {}
#     }
# )