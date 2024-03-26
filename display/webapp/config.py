import ast
import json
import os
import random
from json import JSONDecodeError


def getenv_bool(name: str, default: str = "False"):
    raw = os.getenv(name, default).title()
    try:
        the_bool = ast.literal_eval(raw)

        if not isinstance(the_bool, bool):
            raise ValueError
    except ValueError:
        raise

    return the_bool


def getenv_list(name: str, default: list = None):
    if default is None:
        default = []

    raw = os.getenv(name, default)

    if not isinstance(raw, list):
        try:
            the_list = json.loads(raw)
            return the_list
        except JSONDecodeError:
            raise

    return default


def getenv_dict(name: str, default: dict = None):
    if default is None:
        default = {}

    raw = os.getenv(name, default)

    if not isinstance(raw, dict):
        try:
            the_dict = json.loads(raw)
            return the_dict
        except JSONDecodeError:
            raise

    return default


class Config(object):
    DEBUG = getenv_bool("DEBUG", "False")

    WEB_TLS_KEY_PATH = os.getenv("WEB_TLS_KEY_PATH", "/app/certs/key.pem")
    WEB_TLS_CERT_PATH = os.getenv("WEB_TLS_CERT_PATH", "/app/certs/cert.pem")

    SECRET_KEY = os.getenv("SECRET_KEY", str(random.getrandbits(256)))

    WEB_ROOT = os.getenv("WEB_ROOT", "")

    DB_HOST = os.getenv("DB_HOST", "mysql")

    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "display")
    MYSQL_USER = os.getenv("MYSQL_USER", "display")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{MYSQL_DATABASE}",
    )

    PROPAGATE_EXCEPTIONS = getenv_bool("PROPAGATE_EXCEPTIONS", "True")

    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/app/data/logs/")
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "display.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_PURGE_TIME = int(os.getenv("LOG_PURGE_TIME", 120))  # in minutes

    SYSLOG_ENABLE = getenv_bool("SYSLOG_ENABLE", "False")
    SYSLOG_SERVER = os.getenv("SYSLOG_SERVER", "172.16.1.1")
    SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 5140))

    CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/data/config/")
    CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")
    SCREENSHOT_SOURCE_CONFIG_FILE = os.getenv(
        "SCREENSHOT_SOURCE_CONFIG_FILE", "screenshot_config.json"
    )

    SPLASH_HOST = os.getenv("SPLASH_HOST", "ha-proxy")
    SPLASH_PORT = int(os.getenv("SPLASH_PORT", 8050))

    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/")
    REDIS_BROKER_DB = int(os.getenv("REDIS_BROKER_DB", 5))
    REDIS_BACKEND_DB = int(os.getenv("REDIS_BACKEND_DB", 6))

    SCREENSHOT_LOCATION = os.getenv("SCREENSHOT_LOCATION", "/app/data/screenshots/")
    TIMELINE_LOCATION = os.getenv("TIMELINE_LOCATION", "/app/data/timeline")
    DAYS_TO_KEEP_TIMELINE_SCREENSHOTS = int(
        os.getenv("DAYS_TO_KEEP_TIMELINE_SCREENSHOTS", 5)
    )

    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    )

    SCREENSHOT_REFRESH = int(os.getenv("SCREENSHOT_REFRESH", 30))
    SCREENSHOT_CHUNK_SIZE = int(os.getenv("SCREENSHOT_CHUNK_SIZE", 6))
    SCREENSHOT_NODES = int(os.getenv("SCREENSHOT_NODES", 5))

    SCREENSHOT_HEADER_TABS = getenv_bool("SCREENSHOT_HEADER_TABS", "True")

    SCREENSHOT_EVIDENCE_ENABLED = getenv_bool("SCREENSHOT_EVIDENCE_ENABLED", "True")

    TAB_ROTATE_TIMER = int(os.getenv("TAB_ROTATE_TIMER", 90))

    OPENID_LOGIN = getenv_bool("OPENID_LOGIN", "True")

    OIDC_CLIENT_SECRETS = os.getenv("OIDC_CLIENT_SECRETS", "client_secrets.json")
    OIDC_COOKIE_SECURE = getenv_bool("OIDC_COOKIE_SECURE", "True")
    OIDC_REQUIRE_VERIFIED_EMAIL = getenv_bool("OIDC_REQUIRE_VERIFIED_EMAIL", "False")
    OIDC_USER_INFO_ENABLED = getenv_bool("OIDC_USER_INFO_ENABLED", "True")
    OIDC_OPENID_REALM = os.getenv("OIDC_OPENID_REALM", "CR14")
    OIDC_SCOPES = os.getenv("OIDC_SCOPES", ["openid", "resources"])
    OIDC_INTROSPECTION_AUTH_METHOD = os.getenv(
        "OIDC_INTROSPECTION_AUTH_METHOD", "client_secret_post"
    )
    OIDC_VALID_ISSUERS = os.getenv("OIDC_VALID_ISSUERS", "https://OIDC_VALID_ISSUERS")
    OVERWRITE_REDIRECT_URI = os.getenv("OVERWRITE_REDIRECT_URI", False)
    OIDC_CALLBACK_ROUTE = os.getenv("OIDC_CALLBACK_ROUTE", "/oidc_callback")
    OIDC_ID_TOKEN_COOKIE_PATH = os.getenv("OIDC_ID_TOKEN_COOKIE_PATH", "/")
    OIDC_ID_TOKEN_COOKIE_NAME = os.getenv(
        "OIDC_ID_TOKEN_COOKIE_NAME", "display_oidc_cookie"
    )

    ALLOWED_USER_GROUPS = getenv_list("ALLOWED_USER_GROUPS", [])
