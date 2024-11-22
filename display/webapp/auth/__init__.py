from flask import Blueprint

from display.webapp.config import Config

config = Config()

auth = Blueprint("auth", __name__)

from . import views

if config.SSO_LOGIN_ENABLE:
    from . import sso_login  # noqa: F401
