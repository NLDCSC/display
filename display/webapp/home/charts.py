import logging

from flask import render_template
from flask_login import login_required
from nldcsc.loggers.app_logger import AppLogger

from . import home
from ..config import Config
from ...core.parsers.display_config_parser import DisplayConfigParser

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

display_config_parser = DisplayConfigParser()


@home.route("/chart")
@login_required
def charts():
    return render_template("pages/charts.html", header="Defacement Chart")
