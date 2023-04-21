import logging
from functools import wraps

from flask import abort, request
from flask_login import current_user

from display.helpers.app_logger import AppLogger
from display.webapp.app.models import users

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)


def admin_required(fn):
    """
    Decorator (@admin_required) that enforces that only users with the ADMIN role are allowed on a specific endpoint.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user.role.lower() != "admin":
            logger.warning(
                "User {} tried to perform illegal action to "
                "admin protected endpoints!!".format(current_user.username)
            )
            abort(403)
        else:
            return fn(*args, **kwargs)

    return wrapper


def get_apiauth_object_by_key(key):
    """
    Check if the key matches the configured key
    """

    api_user = users.query.filter_by(api_key=key).first()

    if api_user is not None:
        return True
    else:
        return False


def match_api_keys(key):
    """
    Match API keys and discard ip

    @param key: API key from request
    @return: boolean
    """
    return get_apiauth_object_by_key(key)


def require_apikey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.headers.get("Access-Token") and match_api_keys(
            request.headers.get("Access-Token")
        ):
            return view_function(*args, **kwargs)
        else:
            logger.warning(
                "Unauthorized address trying to use API: " + request.remote_addr
            )
            abort(401)

    return decorated_function
