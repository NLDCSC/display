import hashlib
import os

from flask import current_app
from jinja2 import pass_eval_context, pass_environment
from nldcsc.generic.times import timestampTOdatetimestring

from . import home
from ..config import Config

config = Config()


@pass_environment
@home.app_template_test()
def greenteam(env, val: str) -> bool:
    if val.startswith("GT"):
        return True
    return False


@pass_environment
@home.app_template_test()
def blueteam(env, val: str) -> bool:
    if val.startswith("BT"):
        return True
    return False


@pass_eval_context
@home.app_template_filter()
def md5(eval_ctx, value):
    # noinspection InsecureHash
    return hashlib.md5(value.encode("utf-8")).hexdigest()[:6]


@pass_eval_context
@home.app_template_filter()
def timestamptodatetime(eval_ctx, value):
    return timestampTOdatetimestring(value)


@pass_eval_context
@home.app_template_filter()
def mod_time(eval_ctx, path_to_file):
    try:
        time = timestampTOdatetimestring(
            int(
                os.path.getmtime(
                    os.path.join(
                        current_app.config["SCREENSHOT_LOCATION"], f"{path_to_file}.png"
                    )
                )
            ),
            True,
        )
        return time
    except FileNotFoundError:
        return "never"
