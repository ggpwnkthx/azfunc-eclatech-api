import azure.functions as func
from libs.flask import app
from urllib.parse import urlparse
from libs.flask.jsonapi.blueprints import register_blueprints as register_blueprints_jsonapi
from libs.nats.blueprints import register_blueprints as register_blueprints_nats


async def main(
    req: func.HttpRequest, context: func.Context, starter: str
) -> func.HttpResponse:

    if len(app.url_map._rules) <= 1:
        prefix = urlparse(req.url).path.removesuffix(
            '/' + str(req.route_params.get('flask_route'))
        )
        register_blueprints_nats(f'{prefix}/nats')
        register_blueprints_jsonapi(f'{prefix}/jsonapi')

        # for rule in app.url_map._rules:
        #     logging.warning(f"{','.join(rule.methods)}: {rule}")

    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)
