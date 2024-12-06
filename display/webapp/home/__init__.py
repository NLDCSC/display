from flask import Blueprint

home = Blueprint("home", __name__)

from . import views  # noqa: F401
from . import cps  # noqa: F401
from . import websockets  # noqa: F401
from . import charts  # noqa: F401
