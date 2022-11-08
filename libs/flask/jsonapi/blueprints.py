from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from flask_restless import APIManager
from .. import app, permission, db
from flask import request

def check_auth(*args, **kwargs):
    permission.check(
        resource={"name":f"{request.path.split('/')[3]}.{request.host}"},
        action={"method":request.method}
    )

def register_blueprints(prefix):
    jsonapi_defaults = {
        "url_prefix": prefix, 
        "preprocessors": {
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
        },
        "page_size": 100,
        "max_page_size": 2000,
    }
    with app.app_context():
        jsonapi = APIManager(app, db.session)
        for model in db.autoloaded_models:
            jsonapi.create_api(
                model,
                collection_name=model.__collection_name__ if hasattr(model,"__collection_name__") else model.__name__,
                **jsonapi_defaults,
                **model.JSONAPI
            )
        @app.route(f"{prefix}/schema")
        @permission.gatekeeper(
            resource={"name":f"schema"},
            action={"method":"GET"}
        )
        def get_schema():
            return {
                model.__collection_name__ if hasattr(model,"__collection_name__") else model.__name__ : {
                    "type": model.__collection_name__ 
                        if hasattr(model,"__collection_name__") 
                        else model.__name__,
                    "fields": {
                        column.key: {
                            "type": column.type.__visit_name__,
                            "readOnly": True 
                                if (hasattr(column,"__read_only__") and column.__read_only__)
                                else False
                        }
                        for column in sqlalchemy_inspect(model).columns
                        if "_id" not in column.key
                    },
                    "relationships": {
                        rel[0]:{
                            "type": rel[1].mapper.class_.__collection_name__ 
                                if hasattr(rel[1].mapper.class_,"__collection_name__") 
                                else rel[1].mapper.class_.__name__
                        }
                        for rel in sqlalchemy_inspect(model).relationships.items()
                    }
                }
                for model in db.autoloaded_models
            }