from flask_restless import APIManager
from flask import request

def __init__(app):
    manager = APIManager(app, app.db.session)
    app.jsonapi = manager

    # def check_auth(*args, **kwargs):
    #     app.permission.check(
    #         resource={"name":f"{request.path.split('/')[3]}.esquireadvertising.com"},
    #         action={"method":request.method}
    #     )

    app.jsonapi.api_preprocessors = {
        # "GET_COLLECTION": [check_auth],
        # "GET_RESOURCE": [check_auth],
        # "GET_RELATION": [check_auth],
        # "GET_RELATED_RESOURCE": [check_auth],
        # "DELETE_RESOURCE": [check_auth],
        # "POST_RESOURCE": [check_auth],
        # "PATCH_RESOURCE": [check_auth],
        # "GET_RELATIONSHIP": [check_auth],
        # "DELETE_RELATIONSHIP": [check_auth],
        # "POST_RELATIONSHIP": [check_auth],
        # "PATCH_RELATIONSHIP": [check_auth]
    }

