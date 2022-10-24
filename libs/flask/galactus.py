# All-knowing user service provider aggregator

import requests
import jwt


def MicrosoftGraph(token):
    auth = jwt.decode(token, options={"verify_signature": False})
    r = requests.post(
        "https://graph.microsoft.com/beta/$batch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "requests": [
                {
                    "url": "/me",
                    "method": "GET",
                    "id": "1"
                },
                {
                    "url": "/me/transitiveMemberOf/microsoft.graph.group",
                    "method": "GET",
                    "id": "2"
                }
            ]
        }
    ).json()

    if "responses" in r.keys():
        subject = next((x["body"]
                       for x in r["responses"] if x["id"] == "1"), None)
        subject["groups"] = next(
            (x["body"]["value"] for x in r["responses"] if x["id"] == "2"), None
        )
        subject["groups"] = list(map(lambda x: x["id"], subject["groups"]))
    else:
        subject = r
    return subject


issuers = {
    "sts.windows.net": MicrosoftGraph,
    "login.microsoftonline.com": MicrosoftGraph
}
