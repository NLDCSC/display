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

    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "display")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "display")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "SomethingSuperSecret")

    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{MYSQL_DATABASE}",
    )

    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "/app/data/logs/")
    LOG_FILE_NAME: str = os.getenv("LOG_FILE_NAME", "certexmon.log")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_PURGE_TIME: int = int(os.getenv("LOG_PURGE_TIME", 4))  # in days

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

    DISPLAY_CONFIG_PATH: str = os.getenv("DISPLAY_CONFIG_PATH", "/app/data/config/")
    DISPLAY_CONFIG_FILE: str = os.getenv("DISPLAY_CONFIG_FILE", "config.json")
    DISPLAY_SETTINGS_FILE: str = os.getenv("DISPLAY_SETTINGS_FILE", "settings.yml")

    SPLASH_HOST: str = os.getenv("SPLASH_HOST", "ha_proxy")
    SPLASH_PORT: int = int(os.getenv("SPLASH_PORT", 8050))
    SPLASH_PROTOCOL: int = os.getenv("SPLASH_PROTOCOL", "http")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/")
    REDIS_CACHE_DB: int = int(os.getenv("REDIS_CACHE_DB", 0))
    REDIS_KWARGS: dict = getenv_dict("REDIS_KWARGS", None)
    REDIS_BROKER_DB: int = int(os.getenv("REDIS_BROKER_DB", 5))
    REDIS_BACKEND_DB: int = int(os.getenv("REDIS_BACKEND_DB", 6))

    # CACHE_SETTINGS
    CACHE_KEY_PREFIX: str = os.getenv("CACHE_KEY_PREFIX", "display_cache")
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 1800))

    TIMELINE_LOCATION: str = os.getenv("TIMELINE_LOCATION", "/app/data/timeline")
    DAYS_TO_KEEP_TIMELINE_SCREENSHOTS: int = int(
        os.getenv("DAYS_TO_KEEP_TIMELINE_SCREENSHOTS", 5)
    )

    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    )

    # SCREENSHOT SETTINGS
    SCREENSHOT_LOCATION: str = os.getenv(
        "SCREENSHOT_LOCATION", "/app/data/screenshots/"
    )
    SCREENSHOT_SOURCE_CONFIG_FILE: str = os.getenv(
        "SCREENSHOT_SOURCE_CONFIG_FILE", "screenshot_config.json"
    )
    SCREENSHOT_REFRESH: int = int(os.getenv("SCREENSHOT_REFRESH", 30))
    SCREENSHOT_CHUNK_SIZE: int = int(os.getenv("SCREENSHOT_CHUNK_SIZE", 7))
    SCREENSHOT_NODES: int = int(os.getenv("SCREENSHOT_NODES", 5))
    SCREENSHOT_HEADER_TABS: bool = getenv_bool("SCREENSHOT_HEADER_TABS", "True")
    SCREENSHOT_EVIDENCE_ENABLED: bool = getenv_bool(
        "SCREENSHOT_EVIDENCE_ENABLED", "True"
    )
    SCREENSHOT_DEFAULT_WAIT: int = int(os.getenv("SCREENSHOT_DEFAULT_WAIT", 2))
    SCREENSHOT_DEFAULT_TIMEOUT: int = int(os.getenv("SCREENSHOT_DEFAULT_TIMEOUT", 15))

    TAB_ROTATE_TIMER: int = int(os.getenv("TAB_ROTATE_TIMER", 90))  # in seconds

    # SSO SETTINGS
    SSO_LOGIN_ENABLE: bool = getenv_bool("SSO_LOGIN_ENABLE", "False")
    SSO_ISSUER: str = os.getenv("SSO_ISSUER", "http://localhost:8000")
    SSO_CLIENT_ID: str = os.getenv("SSO_CLIENT_ID", "sso-client")
    SSO_CLIENT_SECRET: str = os.getenv("SSO_CLIENT_SECRET", "secret!")

    SSO_CALLBACK_ENDPOINT: str = os.getenv("SSO_CALLBACK_ENDPOINT", "sso_callback")
    SSO_OVERWRITE_REDIRECT_URI: str = os.getenv("SSO_OVERWRITE_REDIRECT_URI", None)
    SSO_SCOPES: List[str] = getenv_list(
        "SSO_SCOPES", ["openid", "resources", "profile"]
    )
    SSO_USERNAME_ATTRIBUTE: str = os.getenv(
        "SSO_USERNAME_ATTRIBUTE", "preferred_username"
    )
    SSO_FULLNAME_ATTRIBUTE: str = os.getenv("SSO_FULLNAME_ATTRIBUTE", "name")
    SSO_USERGROUPS_ATTRIBUTE: str = os.getenv("SSO_USERGROUPS_ATTRIBUTE", "resources")

    ALLOWED_USER_GROUPS: List[str] = getenv_list("ALLOWED_USER_GROUPS", [])
    ALLOWED_ADMIN_GROUPS: List[str] = getenv_list("ALLOWED_ADMIN_GROUPS", [])

    # DAEMON TASK STORAGE SETTINGS
    CELERY_TASK_FAILED_ERROR_CODE: int = int(
        os.getenv("CELERY_TASK_FAILED_ERROR_CODE", 1337)
    )
    CELERY_KEEP_TASK_RESULT: int = int(
        os.getenv("CELERY_KEEP_TASK_RESULT", 7)
    )  # in days
    CELERY_TASK_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_TIME_LIMIT", 900)
    )  # in seconds
    CELERY_RESULT_EXPIRES: int = int(
        os.getenv("CELERY_RESULT_EXPIRES", 300)
    )  # in seconds

    # DEFACEMENT SETTINGS
    DISPLAY_ASSUME_NO_TEXT_DEFACED: bool = getenv_bool(
        "DISPLAY_ASSUME_NO_TEXT_DEFACED", "True"
    )
    DISPLAY_ASSUME_TEMPLATE_AS_DEFACED: bool = getenv_bool(
        "DISPLAY_ASSUME_TEMPLATE_AS_DEFACED", "False"
    )
    DISPLAY_GRAPH_TIME_RANGE: int = int(
        os.getenv("DISPLAY_GRAPH_TIME_RANGE", 4)
    )  # in hours
    DISPLAY_DEFACEMENT_PURGE_TIME: int = int(
        os.getenv("DISPLAY_DEFACEMENT_PURGE_TIME", 2)
    )  # in days

    # GENERAL SETTINGS
    DISPLAY_TEAM_COUNT: int = int(os.getenv("DISPLAY_TEAM_COUNT", 28))
    DISPLAY_TEAM_START_AT: int = int(os.getenv("DISPLAY_TEAM_START_AT", 1))
    DISPLAY_GT_START_AT: int = int(os.getenv("DISPLAY_GT_START_AT", 25))
    DISPLAY_ROOT_DOMAIN: str = os.getenv("DISPLAY_ROOT_DOMAIN", "test.com")

    DISPLAY_FILTER_FROM_CHUNKS: list[str] = getenv_list(
        "DISPLAY_FILTER_FROM_CHUNKS", ["bt", "gt"]
    )
