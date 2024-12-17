import eventlet

if __name__ == "__main__":
    eventlet.monkey_patch()

from dotenv import load_dotenv  # noqa: E402

load_dotenv(".env")

import logging  # noqa: E402

from nldcsc.loggers.app_logger import AppLogger
from display.webapp.run import create_app  # noqa: E402
from set_version import VERSION  # noqa: E402

logging.setLoggerClass(AppLogger)

__version__ = VERSION

# Effectively disabling the following loggers
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app, socketio = create_app(version=__version__)

if __name__ == "__main__":
    logger = logging.getLogger("display")

    logger.info(f"Initialized display version {__version__}")
    logger.info("Running async mode: {}".format(socketio.async_mode))
    logger.info("Starting display server...")
    socketio.run(app, host="0.0.0.0", port=5050)
