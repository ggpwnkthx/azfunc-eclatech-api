import azure.durable_functions as df
import azure.functions as func
import logging
from libs.flask import app,permission,db,jsonapi

from libs.flask.jsonapi.blueprints import (
    register_blueprints as register_blueprints_jsonapi,
)
from pprint import pformat
from urllib.parse import urlparse
from flask import request


async def main(
    req: func.HttpRequest, context: func.Context, starter: str
) -> func.HttpResponse:
    if len(app.url_map._rules) <= 1:
        prefix = urlparse(req.url).path.removesuffix(
            "/" + str(req.route_params.get("flask_route"))
        )
        register_blueprints_jsonapi(app, db, jsonapi, permission, f"{prefix}/jsonapi")

        @app.route(f"{prefix}/test")
        @permission.gatekeeper(
            resource={"name": f"schema.{req.headers.get('Host')}"},
            action={"method": "GET"},
        )
        def add():
            return "test"

        for rule in app.url_map._rules:
            logging.warning(f'{",".join(rule.methods)}: {rule}')

    # Inject durable function starter string into the request header
    req = func.HttpRequest(
        method=req.method,
        url=req.url,
        headers={**req.headers, "durable-starter": starter},
        params=req.params,
        route_params=req.route_params,
        body=req.get_body(),
    )
    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)
