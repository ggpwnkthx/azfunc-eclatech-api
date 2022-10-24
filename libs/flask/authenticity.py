from urllib.parse import urlparse
from flask import request
import jwt
from .galactus import issuers as Galactus

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
    else:
        return None
    
    return {
        **Galactus[issuer](token),
        "issuer": issuer
    }