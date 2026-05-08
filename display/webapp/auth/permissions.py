import logging
from functools import wraps

from flask import abort, request
from flask_login import current_user
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import select

from display.core.general.constants import user_active
from display.webapp.app.models import Users
from display.webapp.run import db

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)


def _sanitize_for_log(value):
    return str(value).replace("\r", "").replace("\n", "")


def admin_required(fn):
    """
    Decorator (@admin_required) that enforces that only users within the ADMIN group are allowed on that specific
    endpoint.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin():
            logger.warning(
                f"User {current_user.username} tried to perform illegal action to admin protected endpoints!!"
            )
            abort(403)

        return fn(*args, **kwargs)

    return wrapper


def approval_required(fn):
    """
    Decorator (@approval_required) that enforces that only users with the approval role set are allowed on that
    specific endpoint.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if (
            not current_user.can_approve()
            and not current_user.is_admin()
            and not current_user.is_superuser()
        ):
            logger.warning(
                f"User {current_user.username} tried to perform illegal action to approval protected endpoints!!"
            )
            abort(403)

        return fn(*args, **kwargs)

    return wrapper


def groups_allowed(groups: list):
    """
    Decorator (@groups_allowed) that enforces that only users within the groups variable are allowed on that
    specific endpoint.
    """

    def inner_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if (
                current_user.get_user_group() not in groups
                and not current_user.is_admin()
                and not current_user.is_superuser()
            ):
                logger.warning(
                    f"User {current_user.username} tried to perform illegal action on protected endpoints!!"
                )
                abort(403)

            return fn(*args, **kwargs)

        return wrapper

    return inner_decorator


def read_protected(decorator_name):
    def inner_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.is_admin() or current_user.is_superuser():
                return fn(*args, **kwargs)

            decorators = decorator_name.split(",")
            for decorator in decorators:
                if current_user.get_permission_by_decorator(decorator) >= 1:
                    return fn(*args, **kwargs)

            logger.warning(
                f"User {current_user.username} tried to perform illegal action "
                f"to {decorator_name} protected endpoints!!"
            )
            abort(403)

        return wrapper

    return inner_decorator


def write_protected(decorator_name):
    def inner_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_user.is_admin() or current_user.is_superuser():
                return fn(*args, **kwargs)

            decorators = decorator_name.split(",")
            for decorator in decorators:
                if current_user.get_permission_by_decorator(decorator) >= 2:
                    return fn(*args, **kwargs)

            logger.warning(
                f"User {current_user.username} tried to perform illegal action "
                f"to {decorator_name} protected endpoints!!"
            )
            abort(403)

        return wrapper

    return inner_decorator


def get_apiauth_object_by_key(key, return_raw_user=False):
    """
    Check if the key matches the configured key
    """

    api_user = db.session.scalar(
        select(Users).filter(
            Users.api_key_lookup == key[:8], Users.active == user_active.ENABLED
        )
    )

    if return_raw_user:
        return api_user

    if api_user is not None:
        return api_user.verify_api_key(key)
    else:
        return False


def get_admin_apiauth_object_by_key(key, return_raw_user=False):
    """
    Check if the key matches the configured key
    """

    api_user = db.session.scalar(
        select(Users).filter(
            Users.api_key_lookup == key[:8], Users.active == user_active.ENABLED
        )
    )

    if return_raw_user:
        return api_user

    if api_user is not None:
        if api_user.is_admin():
            return api_user.verify_api_key(key)
        else:
            return False
    else:
        return False


def get_apiauth_object_by_key_and_decorator(key: str, decorator_name: str, level: int):
    """
    Check if the key matches the configured key
    """

    api_user = db.session.scalar(
        select(Users).filter(
            Users.api_key_lookup == key[:8], Users.active == user_active.ENABLED
        )
    )

    if api_user is not None:
        if api_user.is_admin() or api_user.is_superuser():
            return api_user.verify_api_key(key)
        elif api_user.get_permission_by_decorator(decorator_name) >= level:
            return api_user.verify_api_key(key)
        else:
            return False
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
                f"Unauthorized address trying to use API: {_sanitize_for_log(request.remote_addr)}"
            )
            abort(401)

    return decorated_function


def require_admin_apikey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.headers.get("Access-Token") and match_api_keys(
            request.headers.get("Access-Token")
        ):
            if not get_admin_apiauth_object_by_key(request.headers.get("Access-Token")):
                logger.warning(
                    f"Unauthorized address trying to use admin protected "
                    f"endpoints: {_sanitize_for_log(request.remote_addr)}"
                )
                abort(401)
            else:
                return view_function(*args, **kwargs)
        else:
            logger.warning(
                f"Unauthorized address trying to use API: {_sanitize_for_log(request.remote_addr)}"
            )
            abort(401)

    return decorated_function


def api_read_protected(decorator_name):
    def inner_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.headers.get("Access-Token") and match_api_keys(
                request.headers.get("Access-Token")
            ):
                if not get_apiauth_object_by_key_and_decorator(
                    request.headers.get("Access-Token"), decorator_name, 1
                ):
                    logger.warning(
                        f"Unauthorized address trying to use {decorator_name} protected "
                        f"endpoints: {_sanitize_for_log(request.remote_addr)}"
                    )
                    abort(403)
                else:
                    return fn(*args, **kwargs)
            else:
                logger.warning(
                    f"Missing API key or API key is incorrect: {_sanitize_for_log(request.remote_addr)}"
                )
                abort(401)

        return wrapper

    return inner_decorator


def api_write_protected(decorator_name):
    def inner_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.headers.get("Access-Token") and match_api_keys(
                request.headers.get("Access-Token")
            ):
                if not get_apiauth_object_by_key_and_decorator(
                    request.headers.get("Access-Token"), decorator_name, 2
                ):
                    logger.warning(
                        f"Unauthorized address trying to use {decorator_name} protected "
                        f"endpoints: {_sanitize_for_log(request.remote_addr)}"
                    )
                    abort(403)
                else:
                    return fn(*args, **kwargs)
            else:
                logger.warning(
                    f"Missing API key or API key is incorrect: {_sanitize_for_log(request.remote_addr)}"
                )
                abort(401)

        return wrapper

    return inner_decorator
