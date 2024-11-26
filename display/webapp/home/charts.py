import logging
import time
from typing import List

from flask import render_template
from flask_login import login_required
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import select

from . import home
from ..app.models import Defacements
from ..config import Config
from ..run import db
from ...core.charts.scatter_data import ScatterChartData, DefacementsContainer
from ...core.parsers.display_config_parser import DisplayConfigParser

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

display_config_parser = DisplayConfigParser()


def get_defacements_from_database() -> List[ScatterChartData]:

    graph_time_range = int(time.time()) - config.DISPLAY_GRAPH_TIME_RANGE * 60 * 60

    all_data = db.session.scalars(
        select(Defacements)
        .filter(Defacements.created_at >= graph_time_range)
        .order_by(Defacements.created_at)
    ).all()

    dc = DefacementsContainer(data=all_data)

    return dc.scatterchartdata_per_header


@home.route("/chart")
@login_required
def charts():

    display_config = display_config_parser.get_display_config_obj()
    target_count = display_config.target_count

    scatter_data = get_defacements_from_database()

    return render_template("pages/charts.html", header="Defacement Chart", **locals())
