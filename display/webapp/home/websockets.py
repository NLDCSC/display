import logging

from flask import copy_current_request_context, request, render_template
from flask_login import login_required, current_user
# noinspection PyUnresolvedReferences
from flask_socketio import emit, disconnect, join_room, leave_room, call
from nldcsc.loggers.app_logger import AppLogger
from socketio.exceptions import TimeoutError as SocketIOTimeOutError
from sqlalchemy import select

from display.celery_app.display_daemon import (
    create_custom_screenshot,
    create_custom_evidence,
)
from display.core.clients.client_pool import ClientPool
from display.core.connections.client_connection import ClientConnection
from display.core.database_logging.trace_log import TraceLogEntry
from display.core.general.constants import (
    tracelog_action,
    tracelog_result,
)
from display.core.parsers.display_config_parser import DisplayConfigParser
from display.core.screenshots.screenshot_handler import ScreenShotHandler
from display.core.screenshots.utils import getB64_screenshot
from display.webapp.app.models import DefacementTracker
from display.webapp.run import socketio, db

logging.setLoggerClass(AppLogger)

logging.getLogger("socketio.server").setLevel("ERROR")
logging.getLogger("geventwebsocket.handler").setLevel("ERROR")
logging.getLogger("engineio.server").setLevel("ERROR")

logger = logging.getLogger(__name__)

clients = ClientPool()

display_config_parser = DisplayConfigParser()
sh = ScreenShotHandler()


# noinspection PyUnresolvedReferences
@socketio.on("disconnect_request", namespace="/display")
@login_required
def disconnect_request() -> None:
    @copy_current_request_context
    def can_disconnect() -> None:
        disconnect()

    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been received, and it is safe to disconnect
    emit(
        "server_disconnect",
        {"data": "Disconnected!"},
        callback=can_disconnect,
        to=request.sid,
    )


# noinspection PyUnresolvedReferences
@socketio.on("my_ping", namespace="/display")
@login_required
def ping_pong() -> None:
    emit("my_pong", to=request.sid)


# noinspection PyUnresolvedReferences
@socketio.on("async_mode", namespace="/display")
@login_required
def get_async_mode() -> None:
    logger.info(f"Async mode request from: {request.sid}")

    @copy_current_request_context
    def cfm_received(client_id: str, data: dict) -> None:
        cfm_received_data(client_id=client_id, data=data)

    emit(
        "async_request",
        {"data": socketio.async_mode},
        to=request.sid,
        callback=cfm_received(
            client_id=request.sid, data={"async_mode": socketio.async_mode}
        ),
    )


def cfm_received_data(client_id: str, data: dict) -> None:
    logger.info(f"Client {client_id} received data: {data}")


# noinspection PyUnresolvedReferences
@socketio.on("connect", namespace="/display")
@login_required
def connect() -> None:
    global clients

    logger.info(f"New connections request from: {request.sid}")

    clients.add(ClientConnection(sid=request.sid))

    join_room(request.sid)

    @copy_current_request_context
    def can_connect() -> None:
        active_connect()

    emit("con_request", {"data": "Connected"}, callback=can_connect, to=request.sid)

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_ACK

    logger.info(f"Client details: {clients.fetch_client_details()}")


# noinspection PyUnresolvedReferences
@socketio.on("active_connect", namespace="/display")
@login_required
def active_connect() -> None:
    global clients

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_CFM

    logger.info(f"Client connected: {request.sid}")

    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.info(f"Client details: {clients.fetch_client_details()}")


# noinspection PyUnresolvedReferences
@socketio.on("disconnect", namespace="/display")
@login_required
def do_disconnect() -> None:
    global clients

    req_client = clients.get(request.sid)

    clients.remove(request.sid)

    leave_room(request.sid)
    if req_client.current_tab is not None:
        leave_room(req_client.current_tab)

    logger.info(f"Client disconnected: {request.sid}")
    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.info(f"Client details: {clients.fetch_client_details()}")


# noinspection PyUnresolvedReferences
@socketio.on("change_display_tab", namespace="/display")
@login_required
def do_change_display_tab(data: dict) -> None:
    global clients

    req_client = clients.get(request.sid)

    if req_client.current_tab is not None:
        leave_room(req_client.current_tab)

    join_room(data["tab_name"])
    old_tab = req_client.current_tab
    req_client.current_tab = data["tab_name"]
    req_client.current_tab_hash = data["tab_hash"]

    logger.info(
        f"Client: {req_client.sid} is changing room from {old_tab} to {data['tab_name']}"
    )

    display_config = display_config_parser.get_display_config_obj()
    display_sources = display_config.display_sources()

    display_sources = {data["tab_name"]: display_sources[data["tab_name"]]}

    key = data["tab_name"]

    html_data = render_template(
        "partials/content_rows.html", display_sources=display_sources, key=key
    )

    @copy_current_request_context
    def cfm_received(client_id: str, recv_data: dict) -> None:
        cfm_received_data(client_id=client_id, data=recv_data)

    # using call here to wait for the callback of the client; timeout error is raised is callback is not received in
    # time; retrying the second time with the emit event
    try:
        call(
            "push_all_screenshots",
            {
                "html_data": html_data,
                "tab_hash": sh.get_hash(data["tab_name"].encode("utf-8")),
            },
            to=req_client.sid,
            timeout=10,
        )
        logger.info(f"Client {req_client.sid} received data on tab: {data['tab_name']}")
    except SocketIOTimeOutError:
        logger.warning(f"Timeout error on client: {req_client}; retrying!")
        emit(
            "push_all_screenshots",
            {
                "html_data": html_data,
                "tab_hash": sh.get_hash(data["tab_name"].encode("utf-8")),
            },
        )

    logger.info(f"Client details: {req_client.client_details()}")


# noinspection PyUnresolvedReferences
@socketio.on("get_hash_screenshot", namespace="/display")
@login_required
def do_get_hash_screenshot(
    url_hash: str, tab_hash: str, last_element: bool = False
) -> None:
    global clients

    req_client = clients.get(request.sid)

    if req_client.current_tab_hash == tab_hash:

        url_screenshot = sh.get_hash_screenshot(url_hash=url_hash)

        @copy_current_request_context
        def cfm_received(client_id: str, data: dict) -> None:
            cfm_received_data(client_id=client_id, data=data)

        # using call here to wait for the callback of the client; timeout error is raised if callback is not received in
        # time; retrying the second time with the emit event
        try:
            call(
                "push_hash_screenshot",
                {
                    "url_screenshot": url_screenshot,
                    "tab_hash": tab_hash,
                    "last_element": last_element,
                },
                to=req_client.sid,
                timeout=10,
            )
            logger.info(
                f"Client {req_client.sid} received data on screenshot hash: {url_hash}"
            )
        except SocketIOTimeOutError:
            logger.warning(f"Timeout error on client: {req_client}; retrying!")
            emit(
                "push_hash_screenshot",
                {
                    "url_screenshot": url_screenshot,
                    "tab_hash": tab_hash,
                    "last_element": last_element,
                },
            )
    else:
        logger.warning(f"Client {req_client.sid} has changed tabs; disregarding...")


# noinspection PyUnresolvedReferences
@socketio.on("rebuild_request", namespace="/display")
@login_required
def do_rebuild_request() -> None:
    global clients

    req_client = clients.get(request.sid)

    display_config = display_config_parser.get_display_config_obj()
    display_sources = display_config.display_sources()

    all_display_sources = display_sources

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

    display_sources = {}

    html_data = render_template("partials/content.html", **locals())

    selector_data = render_template("partials/tab_selector.html", **locals())

    logger.info(f"Client: {req_client.sid} is rebuilding page...")
    try:
        sel_tab = ScreenShotHandler.get_hash(req_client.current_tab.encode("utf-8"))
        emit(
            "rebuild_page",
            {
                "data": {"content": html_data, "tab_selector": selector_data},
                "tab": sel_tab,
            },
            to=request.sid,
        )
    except AttributeError:
        # no tab has been selected (coming from an empty config?); fallback first tab by setting tab to None
        emit(
            "rebuild_page",
            {
                "data": {"content": html_data, "tab_selector": selector_data},
                "tab": None,
            },
            to=request.sid,
        )

    logger.info(f"Client details: {req_client.client_details()}")


# noinspection PyUnresolvedReferences
@socketio.on("create_custom_evidence", namespace="/display")
@login_required
def do_create_custom_evidence(data: dict) -> None:
    logger.info(f"Client: {request.sid} is creating custom evidence...")

    create_custom_evidence.delay(data=data)


# noinspection PyUnresolvedReferences
@socketio.on("create_custom_screenshot", namespace="/display")
@login_required
def do_create_custom_screenshot(data: dict) -> None:
    logger.info(f"Client: {request.sid} is creating custom screenshot...")

    create_custom_screenshot.delay(data=data)


# noinspection PyUnresolvedReferences
@socketio.on("see_custom_screenshot", namespace="/display")
@login_required
def do_see_custom_screenshot(req_data: dict) -> None:
    logger.info(f"Client: {request.sid} is requesting to see custom screenshot...")

    sh.set_timestamp_to_picture(filename=req_data["data"])

    data = getB64_screenshot(filename=req_data["data"], with_timestamp=True)

    emit(
        "show_screenshot",
        {
            "data": data,
            "url": sh.get_url_by_hash(req_data["data"]),
            "tab-hash": req_data["tab-hash"],
            "url-hash": req_data["data"],
        },
        to=request.sid,
    )

    logger.info(f"Request from Client: {request.sid} is send...")


# noinspection PyUnresolvedReferences
@socketio.on("set_defaced", namespace="/display")
@login_required
def do_set_defaced(req_data: dict) -> None:
    logger.info(
        f"Client: {request.sid} is setting {req_data['data']} "
        f"to {'defaced' if int(req_data['data-state']) ==1 else 'not defaced'}..."
    )

    picture_hash = sh.get_picture_hash(req_data["data"])
    def_tracker: DefacementTracker = db.session.scalar(
        select(DefacementTracker).filter(DefacementTracker.picture_hash == picture_hash)
    )

    if def_tracker is None:
        def_tracker = DefacementTracker(
            hash=req_data["data"], picture_hash=picture_hash, created=int(time.time())
        )

    def_tracker.force = 1
    def_tracker.defaced = int(req_data["data-state"])

    TraceLogEntry(
        url=sh.get_url_by_hash(req_data["data"]),
        user=current_user.username,
        hash=req_data["data"],
        action=tracelog_action.DEFACEMENT,
        result=tracelog_result.OK,
        reason=f"Defacement: {True if def_tracker.defaced == 1 else False} -> Manually set defacement!",
    ).save()

    db.session.add(def_tracker)
    db.session.commit()
