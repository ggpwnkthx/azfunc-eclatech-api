from ..flask import app
from flask import jsonify, request, session
from libs.nats import SDK as NATS_SDK

nats = NATS_SDK()


def register_blueprints(prefix: str):
    with app.app_context():

        @app.route(f"{prefix}/login")
        def login():
            member = nats.get(
                endpoint="member",
                action="details",
                username=request.args.get("username"),
            )
            if "password" in member.keys() and member["password"] == request.args.get(
                "password"
            ):
                login = nats.post(
                    endpoint="member",
                    action="login",
                    username=request.args.get("username"),
                    siteid=request.args.get("site"),
                    ip=str(request.headers.get("X-Forward-For")).split(":")[0]
                    if request.headers.get("X-Forward-For")
                    else "127.0.0.1",
                )
                if (
                    "result" in login.keys()
                    and login["result"].split(":")[0] == "SUCCESS"
                ):
                    if (
                        len(
                            nats.get(
                                "member",
                                "flags",
                                memberid=int(login["result"].split(":")[1]),
                            )
                        )
                        == 0
                    ):
                        session["issuer"] = "nats"
                        session[f"{session['issuer']}_account"] = member
                        return jsonify(
                            {
                                "result": "Authorized",
                            }
                        )
            return jsonify({"result": "Unauthorized"}), 401

        @app.route(f"{prefix}/site")
        def site():
            return jsonify(nats.get("member", "available_flags"))
