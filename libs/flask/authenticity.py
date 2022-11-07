import jwt
import requests
from datetime import datetime
from flask import request
from urllib.parse import urlparse
from typing import Union

import logging


def whoami():
    identity = validate()
    if identity is None:
        identity = {
            "error": {
                "code": "Unidentifiable",
                "message": "Unable to identify the requesting entity.",
            },
            "issuer": "unknown",
        }
    return identity


def validate():
    # Determine issuer
    issuer = None
    if request.headers.get("Authorization"):
        token = str(request.headers.get("Authorization")).removeprefix("Bearer ")
        if token:
            auth = jwt.decode(token, options={"verify_signature": False})
            if auth:
                if "iss" in auth.keys():
                    issuer = urlparse(auth["iss"]).hostname
                    return {**Galactus[issuer](token, auth), "issuer": issuer}
    return None


def MicrosoftGraph(token, auth):
    if (
        datetime.now() < datetime.fromtimestamp(auth["exp"])
        and "MicrosoftGraph" in auth_cache.keys()
        and auth["appid"] in auth_cache["MicrosoftGraph"].keys()
        and auth["oid"] in auth_cache["MicrosoftGraph"][auth["appid"]].keys()
        and auth['ipaddr'] in auth_cache["MicrosoftGraph"][auth["appid"]][auth["oid"]].keys()
        and 'error' not in auth_cache["MicrosoftGraph"][auth["appid"]][auth["oid"]][auth['ipaddr']].keys()
    ):
        return auth_cache["MicrosoftGraph"][auth["appid"]][auth["oid"]][auth['ipaddr']]
    
    r = requests.post(
        "https://graph.microsoft.com/beta/$batch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "requests": [
                {"url": "/me", "method": "GET", "id": "1"},
                {
                    "url": "/me/transitiveMemberOf/microsoft.graph.group",
                    "method": "GET",
                    "id": "2",
                },
            ]
        },
    ).json()

    if "responses" in r.keys():
        subject: Union[dict, None] = next(
            (x["body"] for x in r["responses"] if x["id"] == "1"), None
        )
        if subject:
            subject["groups"] = next(
                (x["body"]["value"] for x in r["responses"] if x["id"] == "2"), None
            )
            if subject["groups"]:
                subject["groups"] = list(map(lambda x: x["id"], subject["groups"]))
    else:
        subject = r
    
    if 'error' not in subject.keys():
        if "MicrosoftGraph" not in auth_cache.keys():
            auth_cache["MicrosoftGraph"] = {}
        if auth["appid"] not in auth_cache["MicrosoftGraph"].keys():
            auth_cache["MicrosoftGraph"][auth["appid"]] = {}
        if auth["oid"] not in auth_cache["MicrosoftGraph"][auth["appid"]].keys():
            auth_cache["MicrosoftGraph"][auth["appid"]][auth["oid"]] = {}
        auth_cache["MicrosoftGraph"][auth["appid"]][auth["oid"]][auth['ipaddr']] = subject
    
    return subject


auth_cache = {}

Galactus: dict = {
    "sts.windows.net": MicrosoftGraph,
    "login.microsoftonline.com": MicrosoftGraph,
}
