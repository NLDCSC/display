# this module primary focus is for use inside the docker container of spectacles.
from gevent import monkey

monkey.patch_all()

from dotenv import load_dotenv

load_dotenv("./.env")

import click
from flask.cli import with_appcontext
import logging
import os

from gevent.pywsgi import WSGIServer

from set_version import VERSION
from display.helpers.app_logger import AppLogger
from display.webapp.run import create_app

__version__ = VERSION

app = create_app(version=__version__)

logging.setLoggerClass(AppLogger)

logger = logging.getLogger("display")

current_dir = os.path.dirname(os.path.realpath(__file__))


@click.command()
@with_appcontext
def runserver():
    if os.path.exists(app.config["WEB_TLS_KEY_PATH"]) and os.path.exists(
        app.config["WEB_TLS_KEY_PATH"]
    ):

        http_server = WSGIServer(
            ("", 5050),
            app,
            certfile=app.config["WEB_TLS_CERT_PATH"],
            keyfile=app.config["WEB_TLS_KEY_PATH"],
            log=logger,
        )
    else:
        http_server = WSGIServer(("", 5050), app, log=logger)

    logger.info(f"Initialized display version {__version__}")
    logger.info("Starting display server...")

    http_server.serve_forever()


app.cli.add_command(runserver)
