import hashlib
import os

from flask import current_app
from jinja2 import pass_eval_context

from . import home
from ..config import Config
from ..helpers.utils.times import timestampTOdatetimestring

config = Config()


@pass_eval_context
@home.app_template_filter()
def md5(eval_ctx, value):
    return hashlib.md5(value.encode("utf-8")).hexdigest()[:6]


@home.context_processor
def get_last_bt_number():
    def get_last_bt_number():
        return config.LAST_BLUE_TEAM

    return dict(get_last_bt_number=get_last_bt_number)


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
