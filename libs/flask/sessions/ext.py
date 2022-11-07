import os
import logging
from flask import Flask
from flask.wrappers import Request, Response
from flask.sessions import SessionMixin
from flask_session import (
    Session as FlaskSession,
    RedisSessionInterface,
    MemcachedSessionInterface,
    FileSystemSessionInterface,
    MongoDBSessionInterface,
    SqlAlchemySessionInterface,
    NullSessionInterface,
)
from typing import Union, Optional

# logger = logging.getLogger("azure")
# logger.setLevel(logging.WARNING)


class Session(FlaskSession):
    def _get_interface(self, app):
        config = app.config.copy()
        config.setdefault("SESSION_TYPE", "null")
        config.setdefault("SESSION_PERMANENT", True)
        config.setdefault("SESSION_USE_SIGNER", False)
        config.setdefault("SESSION_KEY_PREFIX", "session:")
        config.setdefault("SESSION_REDIS", None)
        config.setdefault("SESSION_MEMCACHED", None)
        config.setdefault(
            "SESSION_FILE_DIR", os.path.join(os.getcwd(), "flask_session")
        )
        config.setdefault("SESSION_FILE_THRESHOLD", 500)
        config.setdefault("SESSION_FILE_MODE", 384)
        config.setdefault("SESSION_MONGODB", None)
        config.setdefault("SESSION_MONGODB_DB", "flask_session")
        config.setdefault("SESSION_MONGODB_COLLECT", "sessions")
        config.setdefault("SESSION_SQLALCHEMY", None)
        config.setdefault("SESSION_SQLALCHEMY_TABLE", "sessions")
        config.setdefault(
            "SESSION_AZURE_STORAGE_TABLE_CONNECTION_STRING",
            os.environ["AzureWebJobsStorage"],
        )
        config.setdefault("SESSION_AZURE_STORAGE_TABLE_NAME", "sessions")

        if config["SESSION_TYPE"] == "redis":
            session_interface = RedisSessionInterface(
                config["SESSION_REDIS"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        elif config["SESSION_TYPE"] == "memcached":
            session_interface = MemcachedSessionInterface(
                config["SESSION_MEMCACHED"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        elif config["SESSION_TYPE"] == "filesystem":
            session_interface = FileSystemSessionInterface(
                config["SESSION_FILE_DIR"],
                config["SESSION_FILE_THRESHOLD"],
                config["SESSION_FILE_MODE"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        elif config["SESSION_TYPE"] == "mongodb":
            session_interface = MongoDBSessionInterface(
                config["SESSION_MONGODB"],
                config["SESSION_MONGODB_DB"],
                config["SESSION_MONGODB_COLLECT"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        elif config["SESSION_TYPE"] == "sqlalchemy":
            session_interface = SqlAlchemySessionInterface(
                app,
                config["SESSION_SQLALCHEMY"],
                config["SESSION_SQLALCHEMY_TABLE"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        elif config["SESSION_TYPE"] == "azurestoragetable":
            session_interface = AzureStorageTableSessionInterface(
                config["SESSION_AZURE_STORAGE_TABLE_CONNECTION_STRING"],
                config["SESSION_AZURE_STORAGE_TABLE_NAME"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"],
            )
        else:
            session_interface = NullSessionInterface()

        return session_interface


from flask_session.sessions import ServerSideSession, SessionInterface


class AzureStorageTableSession(ServerSideSession):
    pass


import pickle
from datetime import datetime
from itsdangerous import BadSignature, want_bytes
from azure.data.tables import TableServiceClient


class AzureStorageTableSessionInterface(SessionInterface):
    """Uses Azure Storage Tables as a session backend.

    :param connection_string: Azure Storage connection string.
    :param table: The table name you want to use.
    :param key_prefix: A prefix that is added to all store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    """

    serializer = pickle
    session_class = AzureStorageTableSession

    def __init__(
        self, connection_string, table, key_prefix, use_signer=False, permanent=True
    ):
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent
        self.has_same_site_capability = hasattr(self, "get_cookie_samesite")
        table_service = TableServiceClient.from_connection_string(connection_string)
        table_service.create_table_if_not_exists(table)
        self.table_client = table_service.get_table_client(table)

    def get_session(self, id: str) -> Union[dict, None]:
        try:
            session: dict = self.table_client.get_entity(
                partition_key=self.key_prefix, row_key=id
            )
            for key, value in session.items():
                try:
                    session[key] = self.serializer.loads(want_bytes(value))
                except:
                    pass
            if session["expiry"].timestamp() <= datetime.utcnow().timestamp():
                self.delete_session(id)
                return None
            return session
        except:
            return None

    def delete_session(self, id: str):
        self.table_client.delete_entity(partition_key=self.key_prefix, row_key=id)

    def open_session(self, app: Flask, request: Request) -> Optional[SessionMixin]:
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=self.permanent)
        if self.use_signer:
            signer = self._get_signer(app)
            if signer is None:
                return None
            try:
                sid_as_bytes = signer.unsign(sid)
                sid = sid_as_bytes.decode()
            except BadSignature:
                sid = self._generate_sid()
                return self.session_class(sid=sid, permanent=self.permanent)
        saved_session = self.get_session(sid)
        if saved_session:
            return self.session_class(saved_session, sid=sid)
        return self.session_class(sid=sid, permanent=self.permanent)

    def save_session(
        self, app: Flask, session: SessionMixin, response: Response
    ) -> None:
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        saved_session = self.get_session(session.sid)
        if not session:
            if session.modified:
                # Delete expired session
                self.delete_session(saved_session['RowKey'])
                response.delete_cookie(
                    app.session_cookie_name, domain=domain, path=path
                )
            return

        conditional_cookie_kwargs = {}
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        if self.has_same_site_capability:
            conditional_cookie_kwargs["samesite"] = self.get_cookie_samesite(app)
        expires = self.get_expiration_time(app, session)

        data = dict(session)
        data["expiry"] = expires
        self.table_client.upsert_entity(
            {
                "PartitionKey": self.key_prefix,
                "RowKey": session.sid,
                **{
                    key: self.serializer.dumps(value) 
                    for key, value in data.items()
                    if key not in ['PartitionKey', 'RowKey']
                },
            }
        )
        if self.use_signer:
            session_id = str(self._get_signer(app).sign(want_bytes(session.sid)))
        else:
            session_id = session.sid
        response.set_cookie(
            app.session_cookie_name,
            session_id,
            expires=expires,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            **conditional_cookie_kwargs
        )
        return
