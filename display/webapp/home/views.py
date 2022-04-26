import json
import logging
import os

from flask import render_template, send_from_directory, current_app

from display.helpers.app_logger import AppLogger
from . import home
from ..config import Config

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
            f.write(json.dumps({"none": [{}]}))

        display_sources = {"none": [{}]}

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
