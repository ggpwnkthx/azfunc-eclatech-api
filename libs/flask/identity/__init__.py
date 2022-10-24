from flask import session
from datetime import datetime, timedelta
from ..authenticity import validate

def whoami():
    identity = session.get("identity")
    if identity is None or "error" in identity.keys():
        subject = validate()
        if subject is not None:
            session["identity"] = {
                **subject,
                "cached": datetime.utcnow().isoformat()
            }
        else:
            session["identity"] = {
                "error": {
                    "code": "Unidentifiable",
                    "message": "Unable to identify the requesting entity."
                },
                "issuer": "unknown"
            }
        identity = session.get("identity")
    elif "cached" not in identity.keys() \
    or datetime.fromisoformat(identity["cached"]).timestamp() < (datetime.utcnow() - timedelta(minutes=5)).timestamp():
        session.pop("identity",None)
        return whoami()
    
    return identity