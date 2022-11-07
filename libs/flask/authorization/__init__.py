# from py_abac.storage.sql import SQLStorage
from .azure.table.storage import AzureTableStorage
from py_abac import PDP, Policy, AccessRequest
from flask import Flask
from ..authenticity import whoami
from functools import wraps
from flask import abort
import os

class Authorization:
    def __init__(self, app:Flask):
        self.app = app
        self.storage = AzureTableStorage(
            table_name=str(os.environ.get('flask_abac_table') if os.environ.get('flask_abac_table') else 'pyabac'),
            conn_str=os.environ['AzureWebJobsStorage']
        )
        
        @app.errorhandler(403)
        def auth_error(error):
            error = {
                'status': '403',
                'title': 'Permission Error',
                'detail': 'Requesting entity does not have permission to perform the requested action.'
            }
            identity = whoami()
            if 'error' in identity.keys():
                error['reason'] = {
                    'detail': identity['error']['message']
                }
            return {'errors':[error]}, 403
        
    def is_allowed(self, resource, action, context={}):
        return PDP(self.storage).is_allowed(
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
        
    def check(self, resource, action, context={}):
        if not self.is_allowed(resource, action, context):
            abort(403)
    
    def can(self, resource, action, context={}):
        def wrapper(function):
            @wraps(function)
            def inner(*args, **kwargs):
                self.check(resource, action, context)
                return function(*args, **kwargs, )
            return inner
        return wrapper
    
    gatekeeper = can
    
    def add_policy(self, name:str, rules: dict, description:str = "", effect:str = "allow", targets:dict = {}, priority:int = 0):
        policy = Policy.from_json({
            "uid": name,
            "description": description,
            "effect": effect,
            "rules": rules,
            "targets": targets,
            "priority": priority
        })
        self.storage.add(policy)

    def delete_policy(self, name:str):
        self.storage.delete(name)
    
def __init__(app:Flask) -> Authorization:
    # app.permission.add_policy(
    #     name="AllowAllForEclatech",
    #     rules={
    #         "subject": [
    #             {"$.groups": {"condition": "AnyIn", "values": ["031b4b97-8db8-48c3-a5f7-10fd7e48fc6b"]}},
    #         ],
    #         "resource": {"$.name": {"condition": "RegexMatch", "value": ".*"}},
    #         "action": [
    #             {"$.method": {"condition": "RegexMatch", "value": ".*"}},
    #         ],
    #         "context": {}
    #     }
    # )
    return Authorization(app)
