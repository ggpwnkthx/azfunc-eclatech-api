import sys
import os
import pathlib
import inspect
import importlib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from libs.azure.sql import GenerateAzSQLConnectionString

def __init__(app:Flask) -> SQLAlchemy:
    db = SQLAlchemy(app)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if os.environ.get('flask_sql_instance') and os.environ.get('flask_sql_database')
    app.config['SQLALCHEMY_DATABASE_URI'] = GenerateAzSQLConnectionString(os.environ.get('flask_sql_instance'), os.environ.get('flask_sql_database'))
    app.config['SQLALCHEMY_BINDS'] = {
        f'{server}:{database}':GenerateAzSQLConnectionString(server, database)
        for server, database in [
            (key, os.environ[f'sql_database_{key}'])
            for key in [
                key.replace('SQL_INSTANCE_', '').lower()
                for key in os.environ.keys()
                if key.startswith('SQL_INSTANCE')
            ]
        ]
        if f'{server}:{database}' != f"{os.environ.get('flask_sql_instance')}:{os.environ.get('flask_sql_database')}"
    }

    # Get all the defined SQLAlchemy models
    db.autoloaded_models = []
    cwd = pathlib.Path(os.getcwd())
    walk_path = pathlib.Path(f"{__file__}/../../sql/models")
    for root, dirs, files in os.walk(walk_path.resolve(), topdown=False):
        for file in files:
            path_parts = file.split('.')
            if path_parts[-1] == "py":
                if path_parts[0] != "base" and path_parts[0] != "__base__":
                    absolute_path = pathlib.Path(f"{root}/{file}").resolve()
                    relative_path = str(absolute_path).replace(str(cwd.resolve()),"")[1:]
                    module_name = ".".join(pathlib.Path(os.path.splitext(relative_path)[0]).parts)
                    module = importlib.import_module(module_name)
                    for class_name, class_object in inspect.getmembers(sys.modules[module_name], lambda x: inspect.isclass(x) and (x.__module__ == module_name)):
                        db.autoloaded_models.append(class_object)
                        class_object.create_all(checkfirst=True)
    
    return db