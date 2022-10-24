from flask import jsonify
from authlib.integrations.flask_client import OAuth

def register_blueprints(app, prefix):
    with app.app_context():
        oauth = OAuth(app)
        nats = oauth.register('nats', {...})

        @app.route(f"{prefix}/login")
        def login():
            redirect_uri = app.url_for(f"{prefix}/authorize", _external=True)
            return nats.authorize_redirect(redirect_uri)

        @app.route(f"{prefix}/authorize")
        def authorize():
            token = nats.authorize_access_token()
            # you can save the token into database
            profile = nats.get('/user', token=token)
            return jsonify(profile)
