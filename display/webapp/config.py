import os
import ast
import random


def getenv_bool(name: str, default: str = "False"):
    raw = os.getenv(name, default).title()
    return ast.literal_eval(raw)


class Config(object):
    DEBUG = getenv_bool("DEBUG", "False")

    WEB_TLS_KEY_PATH = os.getenv("WEB_TLS_KEY_PATH", "/app/certs/key.pem")
    WEB_TLS_CERT_PATH = os.getenv("WEB_TLS_CERT_PATH", "/app/certs/cert.pem")

    SECRET_KEY = os.getenv("SECRET_KEY", str(random.getrandbits(256)))

    WEB_ROOT = os.getenv("WEB_ROOT", "")

    PROPAGATE_EXCEPTIONS = getenv_bool("PROPAGATE_EXCEPTIONS", "True")

    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/app/data/logs/")
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "display.log")

    SYSLOG_ENABLE = getenv_bool("SYSLOG_ENABLE", "False")
    SYSLOG_SERVER = os.getenv("SYSLOG_SERVER", "172.16.1.1")
    SYSLOG_PORT = os.getenv("SYSLOG_PORT", "5140")

    OPENID_LOGIN = getenv_bool("OPENID_LOGIN", "True")

    CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/data/config/")
    CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")

    LAST_BLUE_TEAM = os.getenv("LAST_BLUE_TEAM", 24)

    SPLASH_HOST = os.getenv("SPLASH_HOST", "ha_proxy")
    SPLASH_PORT = os.getenv("SPLASH_PORT", 8050)

    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/")
    REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", 5)
    REDIS_BACKEND_DB = os.getenv("REDIS_BACKEND_DB", 6)

    SCREENSHOT_LOCATION = os.getenv("SCREENSHOT_LOCATION", "/app/data/screenshots/")
