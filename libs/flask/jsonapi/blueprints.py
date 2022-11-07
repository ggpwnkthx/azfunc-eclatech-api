from sqlalchemy.inspection import inspect

def register_blueprints(app, db, jsonapi, permission, prefix):
    with app.app_context():
        jsonapi_defaults = {
            "url_prefix": prefix, 
            "preprocessors": jsonapi.api_preprocessors,
            "page_size": 100,
            "max_page_size": 2000,
        }
        for model in db.autoloaded_models:
            jsonapi.create_api(
                model,
                collection_name=model.__collection_name__ if hasattr(model,"__collection_name__") else model.__name__,
                **jsonapi_defaults,
                **model.JSONAPI
            )
        
        @app.route(f"{prefix}/schema")
        @permission.gatekeeper(
            resource={"name":f"schema.esquireadvertising.com"},
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
                        for column in inspect(model).columns
                        if "_id" not in column.key
                    },
                    "relationships": {
                        rel[0]:{
                            "type": rel[1].mapper.class_.__collection_name__ 
                                if hasattr(rel[1].mapper.class_,"__collection_name__") 
                                else rel[1].mapper.class_.__name__
                        }
                        for rel in inspect(model).relationships.items()
                    }
                }
                for model in db.autoloaded_models
            }