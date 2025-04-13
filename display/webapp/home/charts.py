import logging
import time
import uuid
import json

from flask import render_template, request, abort
from flask_login import login_required
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import select

from . import home
from ..app.models import Defacements
from ..config import Config
from ..run import db, rediswrap
from ...core.charts.scatter_data import ScatterChartData, DefacementsContainer
from ...core.parsers.display_config_parser import DisplayConfigParser

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

display_config_parser = DisplayConfigParser()


def get_defacements_from_database() -> list[ScatterChartData]:

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

    return render_template("pages/charts.html", header="Defacement Chart", **locals())


@home.route("_scatter_data")
@login_required
def get_scatter_data():
    view_id = request.args.get("view-id", None)
    if view_id in [None, "null"]:
        return get_defacements_from_database()

    view_name = f"defacement-view:{view_id}"
    data = rediswrap.redis_client.hgetall(name=view_name)
    if data is None or len(data) == 0:
        abort(404, "View not found")

    # Reset expiration on timer, apparently people are still using it...
    rediswrap.redis_client.expire(name=view_name, time=60 * 60)
    return {k.decode("utf-8"): json.loads(v) for k, v in data.items()}


@home.route("/_save_custom_view", methods=["POST"])
@login_required
def create_custom_view():
    view_data = request.json
    data = view_data.get("data")
    layout = view_data.get("layout")
    if data is None or layout is None:
        abort(400, description="Creating view failed - required data missing")

    # Absolutely tiny chance of collisions with uuid4 but check just to be safe:
    for attempt in range(6):
        view_id = str(uuid.uuid4())
        view_name = f"defacement-view:{view_id}"
        if not rediswrap.redis_client.exists(view_name):
            break
    if attempt >= 5:
        raise abort(500, description="Failed to generate unique uuid")

    rediswrap.redis_client.hset(
        name=view_name, mapping={"data": json.dumps(data), "layout": json.dumps(layout)}
    )
    rediswrap.redis_client.expire(name=view_name, time=60 * 60)

    return {"view-id": view_id}
