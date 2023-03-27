import logging
import os

from flask import render_template, send_from_directory, current_app, make_response

from display.helpers.app_logger import AppLogger
from . import home
from ..config import Config
from ..helpers.utils.screenshots import get_mod_time
from ..helpers.utils.sources import get_display_sources
from ..helpers.utils.timelines import (
    get_mtime_sorted_timeline_dir_from_hash,
    get_mod_time_from_path,
)
from ...core.screenshot_handler import ScreenShotHandler

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()


@home.route("/")
def index():
    display_sources = get_display_sources(config.SCREENSHOT_HEADER_TABS)

    all_display_sources = display_sources

    header_tabs = [
        header
        for header in all_display_sources
        if all_display_sources[header][0]["header"] == header
    ]

    normal_tabs = [
        header
        for header in all_display_sources
        if all_display_sources[header][0]["header"] != header
    ]

    display_sources = {}

    tab_rotate_timer = config.TAB_ROTATE_TIMER

    return render_template("pages/index.html", header="Display", **locals())


@home.route("/screenshot/<path:filename>")
def get_screenshot(filename):
    try:
        sh = ScreenShotHandler()

        sh.set_timestamp_to_picture(filename=filename)

        data = send_from_directory(
            current_app.config["SCREENSHOT_LOCATION"], f"{filename}_ts.png"
        )
        return data
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")


def get_timeline_data(url_hash):
    ret_data = []

    path_list = get_mtime_sorted_timeline_dir_from_hash(url_hash=url_hash)

    for each in path_list:
        ret_data.append(
            {
                "url_hash": url_hash,
                "filename": each.stem,
                "modtime": get_mod_time_from_path(str(each)),
            }
        )

    return ret_data


@home.route("/timeline/<url_hash>")
def timeline(url_hash):
    sh = ScreenShotHandler()

    timeline_url = sh.get_url_by_hash(the_hash=url_hash)

    last_screenshot_time = get_mod_time(filename=url_hash)

    timeline_data = get_timeline_data(url_hash=url_hash)

    return render_template("pages/timeline.html", header="Display", **locals())


@home.route("/last_screenshot/<path:filename>")
def get_last_screenshot(filename):
    try:
        data = send_from_directory(
            current_app.config["SCREENSHOT_LOCATION"], f"{filename}.png"
        )
        return data
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")


@home.route("/timeline/get_picture/<path:url_hash>/<path:filename>")
def get_timeline_picture(url_hash, filename):
    data = send_from_directory(
        current_app.config["TIMELINE_LOCATION"], f"{url_hash}/{filename}.png"
    )
    return data


@home.route("/timeline/download_picture/<path:url_hash>/<path:filename>")
def download_picture(url_hash, filename):

    sh = ScreenShotHandler()

    data = sh.set_timestamp_to_picture(
        filename=os.path.join(
            current_app.config["TIMELINE_LOCATION"], f"{url_hash}/{filename}.png"
        ),
        filename_is_full_path=True,
        url_hash=url_hash,
    )

    # forming a Response object with Headers to return from flask
    response = make_response(data.getvalue())
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}.png"'
    response.mimetype = "image/png"
    # return the Response object
    return response
