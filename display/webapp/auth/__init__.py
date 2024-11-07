from flask import Blueprint

from ..config import Config

auth = Blueprint("auth", __name__)

from . import views

if Config().SSO_LOGIN_ENABLE:
    from . import sso_login  # noqa: F401
