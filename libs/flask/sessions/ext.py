from flask_session import (
    Session as FlaskSession,
    RedisSessionInterface,
    MemcachedSessionInterface,
    FileSystemSessionInterface,
    MongoDBSessionInterface,
    SqlAlchemySessionInterface,
    NullSessionInterface
)
import os
import logging

logger = logging.getLogger("azure")
logger.setLevel(logging.WARNING)

class Session(FlaskSession):
    def _get_interface(self, app):
        config = app.config.copy()
        config.setdefault("SESSION_TYPE", "null")
        config.setdefault("SESSION_PERMANENT", True)
        config.setdefault("SESSION_USE_SIGNER", False)
        config.setdefault("SESSION_KEY_PREFIX", "session:")
        config.setdefault("SESSION_REDIS", None)
        config.setdefault("SESSION_MEMCACHED", None)
        config.setdefault("SESSION_FILE_DIR",
                          os.path.join(os.getcwd(), "flask_session"))
        config.setdefault("SESSION_FILE_THRESHOLD", 500)
        config.setdefault("SESSION_FILE_MODE", 384)
        config.setdefault("SESSION_MONGODB", None)
        config.setdefault("SESSION_MONGODB_DB", "flask_session")
        config.setdefault("SESSION_MONGODB_COLLECT", "sessions")
        config.setdefault("SESSION_SQLALCHEMY", None)
        config.setdefault("SESSION_SQLALCHEMY_TABLE", "sessions")
        config.setdefault("SESSION_AZURE_STORAGE_TABLE_CONNECTION_STRING", os.environ.get("AzureWebJobsStorage"))
        config.setdefault("SESSION_AZURE_STORAGE_TABLE_NAME", "flasksessions")

        if config["SESSION_TYPE"] == "redis":
            session_interface = RedisSessionInterface(
                config["SESSION_REDIS"], config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"], config["SESSION_PERMANENT"])
        elif config["SESSION_TYPE"] == "memcached":
            session_interface = MemcachedSessionInterface(
                config["SESSION_MEMCACHED"], config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"], config["SESSION_PERMANENT"])
        elif config["SESSION_TYPE"] == "filesystem":
            session_interface = FileSystemSessionInterface(
                config["SESSION_FILE_DIR"], config["SESSION_FILE_THRESHOLD"],
                config["SESSION_FILE_MODE"], config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"], config["SESSION_PERMANENT"])
        elif config["SESSION_TYPE"] == "mongodb":
            session_interface = MongoDBSessionInterface(
                config["SESSION_MONGODB"], config["SESSION_MONGODB_DB"],
                config["SESSION_MONGODB_COLLECT"],
                config["SESSION_KEY_PREFIX"], config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"])
        elif config["SESSION_TYPE"] == "sqlalchemy":
            session_interface = SqlAlchemySessionInterface(
                app, config["SESSION_SQLALCHEMY"],
                config["SESSION_SQLALCHEMY_TABLE"],
                config["SESSION_KEY_PREFIX"], config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"])
        elif config["SESSION_TYPE"] == "azurestoragetable":
            session_interface = AzureStorageTableSessionInterface(
                config["SESSION_AZURE_STORAGE_TABLE_CONNECTION_STRING"],
                config["SESSION_AZURE_STORAGE_TABLE_NAME"],
                config["SESSION_KEY_PREFIX"],
                config["SESSION_USE_SIGNER"],
                config["SESSION_PERMANENT"])
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

    .. versionadded:: 0.1

    :param connection_string: Azure Storage connection string.
    :param table: The table name you want to use.
    :param key_prefix: A prefix that is added to all store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    """

    serializer = pickle
    session_class = AzureStorageTableSession

    def __init__(self, connection_string, table, key_prefix, use_signer=False, permanent=True):
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent
        self.has_same_site_capability = hasattr(self, "get_cookie_samesite")
        table_service = TableServiceClient.from_connection_string(connection_string)
        table_service.create_table_if_not_exists(table)
        self.table_client = table_service.get_table_client(table)
        
    def get_session(self, store_id):
        data = {}
        for row in self.table_client.query_entities(f"PartitionKey eq '{store_id}'"):
            data[row["RowKey"]] = self.serializer.loads(want_bytes(row["Value"]))
        if data is not {}:
            return data
        else:
            return None

    def open_session(self, app, request):
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

        store_id = self.key_prefix + sid
        saved_session = self.get_session(store_id)
        if saved_session and saved_session["expiry"].timestamp() <= datetime.utcnow().timestamp():
            # Delete expired session
            for row in self.table_client.query_entities(f"PartitionKey eq '{store_id}'"):
                self.table_client.delete_entity(partition_key=store_id,row_key=row["RowKey"])
            saved_session = None
        if saved_session:
            return self.session_class(initial=saved_session, sid=sid, permanent=self.permanent)
        return self.session_class(sid=sid, permanent=self.permanent)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        store_id = self.key_prefix + session.sid
        saved_session = self.get_session(store_id)
        if not session:
            if session.modified:
                # Delete expired session
                for row in self.table_client.query_entities(f"PartitionKey eq '{store_id}'"):
                    self.table_client.delete_entity(partition_key=row["PartitionKey"],row_key=row["RowKey"])
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain, path=path)
            return

        conditional_cookie_kwargs = {}
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        if self.has_same_site_capability:
            conditional_cookie_kwargs["samesite"] = self.get_cookie_samesite(app)
        expires = self.get_expiration_time(app, session)

        data = dict(session)
        data["expiry"] = expires
        for key in data.keys():
            if key[0] != "_":
                self.table_client.upsert_entity({
                    "PartitionKey": store_id,
                    "RowKey": key,
                    "Value": self.serializer.dumps(data[key])
                })
        # self.table_client.upsert_entity({
        #     "PartitionKey": store_id,
        #     "RowKey": "expiry",
        #     "Value": self.serializer.dumps(self.get_expiration_time(app, session))
        # })
        if self.use_signer:
            session_id = self._get_signer(app).sign(want_bytes(session.sid))
        else:
            session_id = session.sid
        response.set_cookie(app.session_cookie_name, session_id,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure,
                            **conditional_cookie_kwargs)