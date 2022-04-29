import logging

from flask import render_template, send_from_directory, current_app

from display.helpers.app_logger import AppLogger
from . import home
from ..config import Config
from ..helpers.utils.sources import get_display_sources
from ...core.screenshot_handler import ScreenShotHandler

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()


@home.route("/")
def index():
    display_sources = get_display_sources()

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
