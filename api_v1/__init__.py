import azure.functions as func
import logging
from libs.flask import app, db
from libs.flask.db import current_session
from libs.sql.models.Geoframing.GeoFrames import GeoFrames
from urllib.parse import urlparse
from pprint import pformat

from libs.flask.jsonapi.blueprints import register_blueprints as register_blueprints_jsonapi


async def main(req: func.HttpRequest, context: func.Context, starter: str) -> func.HttpResponse:
    
    if len(app.url_map._rules) <= 1:
        prefix = urlparse(req.url).path.removesuffix("/" + str(req.route_params.get("flask_route")))
        
        register_blueprints_jsonapi(f'{prefix}/jsonapi')
        
        @app.route(f"{prefix}/test")
        def test():
            res = db.get_or_404(GeoFrames,'70f0a831-7eea-4fbb-986e-ffbd6663f1de')
            logging.warn(pformat(res))
            return "test"
        
        
        
        for rule in app.url_map._rules:
            logging.warning(f'{",".join(rule.methods)}: {rule}')

    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)
