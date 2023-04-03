# App is needed for database migrations
from dotenv import load_dotenv

load_dotenv("./.env")

from display.webapp.run import create_app
from set_version import VERSION

__version__ = VERSION

app, socketio = create_app(version=__version__)
