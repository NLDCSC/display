import collections
import json
import logging
import os
import re

from flask import (
    render_template,
    send_from_directory,
    current_app,
    make_response,
    request,
)
from flask_login import login_required
from nldcsc.datatables.server_side_dt_sql import SQLServerSideDataTable
from nldcsc.loggers.app_logger import AppLogger

from display.core.screenshots.screenshot_handler import ScreenShotHandler
from display.core.timelines.utils import (
    get_mtime_sorted_timeline_dir_from_hash,
    get_mod_time_from_path,
)
from . import home
from ..app.models import Tracelog
from ..config import Config
from ..run import db, rediswrap
from ...core.parsers.display_config_parser import DisplayConfigParser
from ...core.screenshots.utils import get_mod_time

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)

config = Config()

display_config_parser = DisplayConfigParser()

_SAFE_PATH_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _is_safe_path_token(value: str) -> bool:
    return isinstance(value, str) and bool(_SAFE_PATH_TOKEN_RE.fullmatch(value))


@home.route("/")
@login_required
def index():

    display_config = display_config_parser.get_display_config_obj()
    display_sources = display_config.display_sources()

    all_display_sources = display_sources
    try:
        header_tabs = [
            header
            for header in all_display_sources
            if all_display_sources[header][0]["header"] == header
        ]

        normal_tabs = [
            header
            for header in all_display_sources
            if all_display_sources[header][0]["header"] != header
        ]
    except KeyError:
        pass

    display_sources = {}

    tab_rotate_timer = config.TAB_ROTATE_TIMER

    return render_template("pages/index.html", header="Display", **locals())


@home.get("/status")
@login_required
def get_status():
    logger.info("Fetching display status...")
    node_status = rediswrap.get("node_status")

    if node_status is not None:
        node_status = json.loads(node_status)
        # sort the data before returning
        od = collections.OrderedDict(sorted(node_status["data"].items()))
        node_status["data"] = od
    else:
        logger.info("No node status found, returning empty dict.")
        node_status = {}

    splash_cluster_status = rediswrap.get("splash_cluster_status")

    if splash_cluster_status is None:
        splash_cluster_status = 1

    return render_template(
        "partials/display_status.html",
        node_status=node_status,
        splash_cluster_status=int(splash_cluster_status),
    )


@home.route("/screenshot/<path:filename>")
@login_required
def get_screenshot(filename):
    safe_filename_for_log = filename.replace("\r", "").replace("\n", "")
    logger.info("Fetching screenshot from: %s", safe_filename_for_log)
    if not _is_safe_path_token(filename):
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")

    sh = ScreenShotHandler()

    try:
        sh.set_timestamp_to_picture(filename=filename)

        data = send_from_directory(
            current_app.config["SCREENSHOT_LOCATION"], f"{filename}_ts.png"
        )
        # set filename to include BT
        filename_data = data.headers.get("Content-Disposition")
        filename_data = filename_data.replace(
            filename, f"{filename}_{'_'.join(sh.get_tab_by_hash(filename))}"
        )
        data.headers.set("Content-Disposition", filename_data)
        return data
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")


def get_timeline_data(url_hash):
    safe_url_hash = str(url_hash).replace("\r", "").replace("\n", "")
    logger.info(f"Fetching timeline data for hash: {safe_url_hash}")
    ret_data = []

    # cap the timeline_data to the first 250 items
    path_list = get_mtime_sorted_timeline_dir_from_hash(url_hash=url_hash)[:250]

    for each in path_list:
        ret_data.append(
            {
                "url_hash": url_hash,
                "filename": each.stem,
                "modtime": get_mod_time_from_path(str(each)),
            }
        )

    return ret_data


@home.route("/timeline/<url_hash>")
@login_required
def timeline(url_hash):
    sh = ScreenShotHandler()

    timeline_url = sh.get_url_by_hash(the_hash=url_hash)

    last_screenshot_time = get_mod_time(filename=url_hash)

    try:
        timeline_data = get_timeline_data(url_hash=url_hash)
    except FileNotFoundError:
        timeline_data = []

    return render_template("pages/timeline.html", header="Display", **locals())


@home.route("/last_screenshot/<path:filename>")
@login_required
def get_last_screenshot(filename):
    try:
        return get_screenshot(filename=filename)
    except Exception:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")


@home.route("/timeline/get_picture/<path:url_hash>/<path:filename>")
@login_required
def get_timeline_picture(url_hash, filename):
    return download_picture(url_hash=url_hash, filename=filename)


@home.route("/timeline/download_picture/<path:url_hash>/<path:filename>")
@login_required
def download_picture(url_hash, filename):
    if not _is_safe_path_token(url_hash) or not _is_safe_path_token(filename):
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")

    sh = ScreenShotHandler()

    timeline_root = os.path.realpath(current_app.config["TIMELINE_LOCATION"])
    requested_path = os.path.realpath(
        os.path.join(timeline_root, f"{url_hash}/{filename}.png")
    )
    if os.path.commonpath([timeline_root, requested_path]) != timeline_root:
        return send_from_directory(current_app.static_folder, "img/noScreenShot.png")

    data = sh.set_timestamp_to_picture(
        filename=requested_path,
        filename_is_full_path=True,
        url_hash=url_hash,
    )

    # forming a Response object with Headers to return from flask
    response = make_response(data.getvalue())
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{filename}_{"_".join(sh.get_tab_by_hash(the_hash=url_hash))}.png"'
    )
    response.mimetype = "image/png"
    # return the Response object
    return response


@home.post("/fetch_log_data")
@login_required
def fetch_nodes_data():
    ssd = SQLServerSideDataTable(
        request=request,
        backend=db,
        target_model="tracelog",
        model_mapping={"tracelog": Tracelog},
    )

    return_data = ssd.output_result()

    return return_data
