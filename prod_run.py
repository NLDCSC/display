# this module primary focus is for use inside the docker container of spectacles.
from gevent import monkey

monkey.patch_all()

from dotenv import load_dotenv

load_dotenv("./.env")

import logging
import os

from set_version import VERSION
from display.helpers.app_logger import AppLogger
from display.webapp.run import create_app

__version__ = VERSION

app, socketio = create_app(version=__version__)

logging.setLoggerClass(AppLogger)

logger = logging.getLogger("display")

current_dir = os.path.dirname(os.path.realpath(__file__))

logger.info(f"Initialized display version {__version__}")
logger.info("Running async mode: {}".format(socketio.async_mode))
logger.info("Starting display server...")

if os.path.exists(app.config["WEB_TLS_KEY_PATH"]) and os.path.exists(
    app.config["WEB_TLS_KEY_PATH"]
):
    socketio.run(
        app,
        host="0.0.0.0",
        port=5050,
        certfile=app.config["WEB_TLS_CERT_PATH"],
        keyfile=app.config["WEB_TLS_KEY_PATH"],
    )
else:
    socketio.run(app, host="0.0.0.0", port=5050)
