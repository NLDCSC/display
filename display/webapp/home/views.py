import logging

from flask import render_template, send_from_directory, current_app

from display.helpers.app_logger import AppLogger
from . import home
from ..config import Config
from ..helpers.utils.sources import get_display_sources

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
        data = send_from_directory(
            current_app.config["SCREENSHOT_LOCATION"], f"{filename}.png"
        )
        return data
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")
