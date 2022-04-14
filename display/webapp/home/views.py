import json
import logging
import os

import cv2
from flask import render_template, send_from_directory, current_app

from display.helpers.app_logger import AppLogger
from . import home
from ..config import Config
from ..helpers.utils.times import timestampTOdatetimestring
from ...core.compare_screenshots import CompareScreenshots

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()


@home.route("/")
def index():
    try:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "r") as f:
            config_json = json.loads(f.read())

        display_sources = config_json

    except FileNotFoundError:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "w") as f:
            f.write(json.dumps([{}]))

        display_sources = [{}]

    index_refresh = config.INDEX_REFRESH

    return render_template("pages/index.html", header="Display", **locals())


@home.route("/screenshot/<path:filename>")
def get_screenshot(filename):
    try:
        data = send_from_directory(
            current_app.config["SCREENSHOT_LOCATION"], f"{filename}.png"
        )
        return data
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")


@home.route("/mod_time/<path:filename>")
def get_mod_time(filename):
    try:
        time = timestampTOdatetimestring(
            int(
                os.path.getmtime(
                    os.path.join(
                        current_app.config["SCREENSHOT_LOCATION"], f"{filename}.png"
                    )
                )
            ),
            True,
        )
        return time
    except FileNotFoundError:
        return "never"


@home.route("/compare_image/<path:filename>")
def get_compare_image(filename):
    cs = CompareScreenshots()

    try:
        changed = cs.compare_images(
            os.path.join(current_app.config["SCREENSHOT_LOCATION"], f"{filename}.png"),
            os.path.join(
                current_app.config["SCREENSHOT_LOCATION"], f"{filename}_old.png"
            ),
        )
        if changed:
            return "1"
        else:
            return "0"
    except FileNotFoundError:
        return "0"
    except cv2.error:
        return "0"
    except ValueError:
        return "0"
