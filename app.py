import eventlet

if __name__ == "__main__":
    eventlet.monkey_patch()

from dotenv import load_dotenv  # noqa: E402

load_dotenv(".env")

import logging  # noqa: E402

from nldcsc.flask_managers.flask_app_manager import FlaskAppManager
from display.webapp.run import create_app  # noqa: E402
from set_version import VERSION  # noqa: E402

__version__ = VERSION

# Effectively disabling the following loggers
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app, socketio = create_app(version=__version__)

if __name__ == "__main__":
    fam = FlaskAppManager(version=__version__, app=app, init_sql_database=False)
    fam.run()