from gevent import monkey

monkey.patch_all()

from dotenv import load_dotenv

load_dotenv("./.env_dev")

import logging
from set_version import VERSION
from display.webapp.run import create_app
from display.helpers.app_logger import AppLogger

__version__ = VERSION

logging.setLoggerClass(AppLogger)

# Effectively disabling the werkzeug logger
logging.getLogger("werkzeug").setLevel(logging.ERROR)

logger = logging.getLogger("display")

logger.info("Fetching config...")

logger.info("Running version: {}".format(__version__))

app, socketio = create_app(version=__version__)

logger.info("Fetched {} config".format(app.config["ENV"]))

logger.info("Running async mode: {}".format(socketio.async_mode))

try:

    logger.info("Trying to start the app...")

    # socketio.run(app, port=6050)
    socketio.run(
        app, port=6050, keyfile="test.key.pem", certfile="test.cert.pem"
    )
    # app.run()

except Exception:

    raise
