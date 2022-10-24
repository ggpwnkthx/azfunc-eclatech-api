import azure.functions as func
import logging
from flask import Flask
from libs.flask.db import __init__ as init_db
from libs.flask.jsonapi import __init__ as init_jsonapi
from libs.flask.jsonapi.blueprints import register_blueprints as register_blueprints_jsonapi
from urllib.parse import urlparse

# This only runs if the flask instance does not have any blueprints
# Which means, this should ONLY run once
async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    app = Flask(__name__)
    prefix = urlparse(req.url).path.removesuffix('/'+str(req.route_params.get('flask_route')))
    app.db = init_db(app)
    
    init_jsonapi(app)
    register_blueprints_jsonapi(app, f'{prefix}/jsonapi')
    
    # @app.errorhandler(403)
    # def internal_error(error):
    #     error = {
    #         'status': '403',
    #         'title': 'Permission Error',
    #         'detail': 'Requesting entity does not have permission to perform the requested action.'
    #     }
    #     identity = whoami()
    #     if 'error' in identity.keys():
    #         error['reason'] = {
    #             'detail': identity['error']['message']
    #         }
    #     return {'errors':[error]}, 403
    
    logging.warning(app.url_map)
    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)