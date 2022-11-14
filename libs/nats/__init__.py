import requests
import os
from requests.auth import AuthBase
from typing import Union, Literal


class Auth(AuthBase):
    def __init__(
        self,
        username: Union[str, None] = os.environ.get("nats_username"),
        apikey: Union[str, None] = os.environ.get("nats_apikey"),
    ):
        if not username or not apikey:
            raise Exception("NATS authorization missing username or password.")
        self.username = username
        self.apikey = apikey

    def __call__(self, r: requests.PreparedRequest):
        r.prepare_headers(
            headers={"api-key": self.apikey, "api-username": self.username, **r.headers}
        )
        return r


class SDK:
    def __init__(
        self,
        username: Union[str, None] = os.environ.get("nats_username"),
        apikey: Union[str, None] = os.environ.get("nats_apikey"),
    ):
        self.auth = Auth(username, apikey)

    def get(
        self,
        endpoint: Literal[
            "adtool",
            "affiliate",
            "biller",
            "codes",
            "config",
            "include",
            "mailing",
            "maintenance",
            "member",
            "message",
            "notification",
            "option",
            "payment",
            "program",
            "report",
            "reward",
            "service",
            "site",
            "skin",
        ],
        action: str,
        **kwargs,
    ):
        return requests.get(
            url=f"{os.environ['nats_instance']}/api/{endpoint}/{action}",
            auth=self.auth,
            params={**kwargs},
        ).json()

    def post(
        self,
        endpoint: Literal[
            "member",
        ],
        action: Literal["login", "note"],
        **kwargs,
    ):
        return requests.post(
            url=f"{os.environ['nats_instance']}/api/{endpoint}/{action}",
            auth=self.auth,
            data={**kwargs},
        ).json()
