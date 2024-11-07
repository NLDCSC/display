import os
import random
from typing import List

from nldcsc.generic.utils import getenv_bool, getenv_list, getenv_dict


class Config(object):
    DEBUG: bool = getenv_bool("DEBUG", "False")

    APP_WORKING_DIR: str = os.getenv("APP_WORKING_DIR", "/app")

    # How to call this app; will also be appended to each log record when using GELF for transmitting syslog
    APP_NAME: str = os.getenv("APP_NAME", "YADA")

    BIND_HOST: str = os.getenv("BIND_HOST", "localhost")
    BIND_PORT: int = int(os.getenv("BIND_PORT", 5050))

    WEB_MAX_WORKERS: int = int(os.getenv("WEB_MAX_WORKERS", 1))
    WEB_WORKER_TIMEOUT: int = int(os.getenv("WEB_WORKER_TIMEOUT", 60))
    WEB_WORKER_CLASS: str = os.getenv("WEB_WORKER_CLASS", "eventlet")
    SECRET_KEY: str = os.getenv("SECRET_KEY", str(random.getrandbits(256)))
    SOCKETIO_CORS_ALLOWED_ORIGINS: str = os.getenv("SOCKETIO_CORS_ALLOWED_ORIGINS", "*")

    # redirect settings
    ALLOWED_REDIRECT_HOSTS: List[str] = getenv_list(
        "ALLOWED_REDIRECT_HOSTS", ["localhost"]
    )

    WEB_ROOT: str = os.getenv("WEB_ROOT", "")

    PROPAGATE_EXCEPTIONS: bool = getenv_bool("PROPAGATE_EXCEPTIONS", "True")

    DB_HOST: str = os.getenv("DB_HOST", "mysql")

    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "certexmon")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "certexmon")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "SomethingSuperSecret")

    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{MYSQL_DATABASE}",
    )

    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/app/data/logs/")
    LOG_FILE_NAME: str = os.getenv("LOG_FILE_NAME", "certexmon.log")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOGS_PURGE_TIME: int = int(os.getenv("LOGS_PURGE_TIME", 730))  # in days

    SYSLOG_ENABLE: bool = getenv_bool("SYSLOG_ENABLE", "False")
    GELF_SYSLOG: bool = getenv_bool("GELF_SYSLOG", "True")

    # GELF format allows for additional fields to be submitted with each log record; Key values of this dict should
    # start with underscores; e.g. {"_environment": "SPECIAL"} would append an environment field with the value of
    # 'SPECIAL' to each log record.
    GELF_SYSLOG_ADDITIONAL_FIELDS: dict = getenv_dict(
        "GELF_SYSLOG_ADDITIONAL_FIELDS", None
    )

    SYSLOG_SERVER: str = os.getenv("SYSLOG_SERVER", "172.16.1.1")
    SYSLOG_PORT: int = int(os.getenv("SYSLOG_PORT", 5140))

    CONFIG_PATH: str = os.getenv("CONFIG_PATH", "/app/data/config/")
    CONFIG_FILE: str = os.getenv("CONFIG_FILE", "config.json")
    SCREENSHOT_SOURCE_CONFIG_FILE: str = os.getenv(
        "SCREENSHOT_SOURCE_CONFIG_FILE", "screenshot_config.json"
    )

    SPLASH_HOST: str = os.getenv("SPLASH_HOST", "ha-proxy")
    SPLASH_PORT: int = int(os.getenv("SPLASH_PORT", 8050))

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/")
    REDIS_CACHE_DB: int = int(os.getenv("REDIS_CACHE_DB", 0))
    REDIS_KWARGS: dict = getenv_dict("REDIS_KWARGS", None)
    REDIS_BROKER_DB: int = int(os.getenv("REDIS_BROKER_DB", 5))
    REDIS_BACKEND_DB: int = int(os.getenv("REDIS_BACKEND_DB", 6))

    SCREENSHOT_LOCATION: str = os.getenv(
        "SCREENSHOT_LOCATION", "/app/data/screenshots/"
    )
    TIMELINE_LOCATION: str = os.getenv("TIMELINE_LOCATION", "/app/data/timeline")
    DAYS_TO_KEEP_TIMELINE_SCREENSHOTS: int = int(
        os.getenv("DAYS_TO_KEEP_TIMELINE_SCREENSHOTS", 5)
    )

    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    )

    SCREENSHOT_REFRESH: int = int(os.getenv("SCREENSHOT_REFRESH", 30))
    SCREENSHOT_CHUNK_SIZE: int = int(os.getenv("SCREENSHOT_CHUNK_SIZE", 6))
    SCREENSHOT_NODES: int = int(os.getenv("SCREENSHOT_NODES", 5))

    SCREENSHOT_HEADER_TABS: bool = getenv_bool("SCREENSHOT_HEADER_TABS", "True")

    SCREENSHOT_EVIDENCE_ENABLED: bool = getenv_bool(
        "SCREENSHOT_EVIDENCE_ENABLED", "True"
    )

    TAB_ROTATE_TIMER: int = int(os.getenv("TAB_ROTATE_TIMER", 90))

    SSO_LOGIN_ENABLE: bool = getenv_bool("SSO_LOGIN_ENABLE", "False")
    SSO_ISSUER: str = os.getenv("SSO_ISSUER", "http://localhost:8000")
    SSO_CLIENT_ID: str = os.getenv("SSO_CLIENT_ID", "sso-client")
    SSO_CLIENT_SECRET: str = os.getenv("SSO_CLIENT_SECRET", "secret!")
    SSO_CALLBACK_ENDPOINT: str = os.getenv("SSO_CALLBACK_ENDPOINT", None)
    SSO_SCOPES: List[str] = getenv_list("SSO_SCOPES", ["openid", "profile", "email"])

    ALLOWED_USER_GROUPS: List[str] = getenv_list("ALLOWED_USER_GROUPS", [])
