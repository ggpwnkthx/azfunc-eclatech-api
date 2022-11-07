from flask_restless import APIManager
from flask import request

def __init__(app, db, permission):
    manager = APIManager(app, db.session)

    def check_auth(*args, **kwargs):
        permission.check(
            resource={"name":f"{request.path.split('/')[3]}.{request.host}"},
            action={"method":request.method}
        )

    manager.api_preprocessors = {
        "GET_COLLECTION": [check_auth],
        "GET_RESOURCE": [check_auth],
        "GET_RELATION": [check_auth],
        "GET_RELATED_RESOURCE": [check_auth],
        "DELETE_RESOURCE": [check_auth],
        "POST_RESOURCE": [check_auth],
        "PATCH_RESOURCE": [check_auth],
        "GET_RELATIONSHIP": [check_auth],
        "DELETE_RELATIONSHIP": [check_auth],
        "POST_RELATIONSHIP": [check_auth],
        "PATCH_RELATIONSHIP": [check_auth]
    }

    return manager
