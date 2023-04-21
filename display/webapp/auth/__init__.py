from flask import Blueprint

from ..config import Config

auth = Blueprint("auth", __name__)

from . import views

if Config().OPENID_LOGIN:
    from . import openid_login  # noqa: F401
