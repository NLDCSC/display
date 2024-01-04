import hashlib
import logging

from flask import copy_current_request_context, request, render_template
from flask_login import login_required
from flask_socketio import emit, disconnect, join_room, leave_room, call
from socketio.exceptions import TimeoutError as SocketIOTimeOutError

from display.celery_app.display_daemon import create_custom_screenshot, create_custom_evidence
from display.core.screenshots.screenshot_handler import ScreenShotHandler
from display.helpers.client_pool import ClientPool
from display.helpers.logger_class import HelperLogger
from display.objects.client_connection import ClientConnection
from display.webapp.helpers.utils.screenshots import getB64_screenshot
from display.webapp.helpers.utils.sources import get_display_sources
from display.webapp.home.views import config
from display.webapp.run import socketio

logging.setLoggerClass(HelperLogger)

logging.getLogger("socketio.server").setLevel("ERROR")
logging.getLogger("geventwebsocket.handler").setLevel("ERROR")
logging.getLogger("engineio.server").setLevel("ERROR")

logger = logging.getLogger(__name__)

clients = ClientPool()


@socketio.on("disconnect_request", namespace="/display")
@login_required
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit(
        "server_disconnect",
        {"data": "Disconnected!"},
        callback=can_disconnect,
        room=request.sid,
    )


@socketio.on("my_ping", namespace="/display")
@login_required
def ping_pong():
    emit("my_pong", room=request.sid)


@socketio.on("async_mode", namespace="/display")
@login_required
def get_async_mode():
    logger.info(f"Async mode request from: {request.sid}")

    @copy_current_request_context
    def cfm_received(client_id, data):
        cfm_received_data(client_id=client_id, data=data)

    emit(
        "async_request",
        {"data": socketio.async_mode},
        room=request.sid,
        callback=cfm_received(
            client_id=request.sid, data={"async_mode": socketio.async_mode}
        ),
    )


def cfm_received_data(client_id, data):
    logger.info(f"Client {client_id} received data: {data}")


@socketio.on("connect", namespace="/display")
@login_required
def connect():
    global clients

    logger.info(f"New connections request from: {request.sid}")

    clients.add(ClientConnection(sid=request.sid))

    join_room(request.sid)

    @copy_current_request_context
    def can_connect():
        active_connect()

    emit("con_request", {"data": "Connected"}, callback=can_connect, room=request.sid)

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_ACK

    logger.info(f"Client details: {clients.fetch_client_details()}")


@socketio.on("active_connect", namespace="/display")
@login_required
def active_connect():
    global clients

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_CFM

    logger.info(f"Client connected: {request.sid}")

    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.info(f"Client details: {clients.fetch_client_details()}")


@socketio.on("disconnect", namespace="/display")
@login_required
def do_disconnect():
    global clients

    req_client = clients.get(request.sid)

    clients.remove(request.sid)

    leave_room(request.sid)
    if req_client.current_tab is not None:
        leave_room(req_client.current_tab)

    logger.info(f"Client disconnected: {request.sid}")
    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.info(f"Client details: {clients.fetch_client_details()}")


@socketio.on("change_display_tab", namespace="/display")
@login_required
def do_change_display_tab(data):
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

    display_sources = get_display_sources(config.SCREENSHOT_HEADER_TABS)

    display_sources = {data["tab_name"]: display_sources[data["tab_name"]]}

    key = data["tab_name"]

    html_data = render_template(
        "partials/content_rows.html", display_sources=display_sources, key=key
    )

    @copy_current_request_context
    def cfm_received(client_id, data):
        cfm_received_data(client_id=client_id, data=data)

    # using call here to wait for the callback of the client; timeout error is raised is callback is not received in
    # time; retrying the second time with the emit event
    try:
        call(
            "push_all_screenshots",
            {
                "html_data": html_data,
                "tab_hash": hashlib.md5(data["tab_name"].encode("utf-8")).hexdigest()[
                    :6
                ],
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
                "tab_hash": hashlib.md5(data["tab_name"].encode("utf-8")).hexdigest()[
                    :6
                ],
            },
        )

    logger.info(f"Client details: {req_client.client_details()}")


@socketio.on("get_hash_screenshot", namespace="/display")
@login_required
def do_get_hash_screenshot(url_hash, tab_hash, last_element: bool = False):
    global clients

    req_client = clients.get(request.sid)

    if req_client.current_tab_hash == tab_hash:
        sh = ScreenShotHandler()

        url_screenshot = sh.get_hash_screenshot(url_hash=url_hash)

        @copy_current_request_context
        def cfm_received(client_id, data):
            cfm_received_data(client_id=client_id, data=data)

        # using call here to wait for the callback of the client; timeout error is raised is callback is not received in
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


@socketio.on("rebuild_request", namespace="/display")
@login_required
def do_rebuild_request():
    global clients

    req_client = clients.get(request.sid)

    display_sources = get_display_sources(config.SCREENSHOT_HEADER_TABS)

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

    emit(
        "rebuild_page",
        {
            "data": {"content": html_data, "tab_selector": selector_data},
            "tab": hashlib.md5(req_client.current_tab.encode("utf-8")).hexdigest()[:6],
        },
        room=request.sid,
    )

    logger.info(f"Client details: {req_client.client_details()}")


@socketio.on("create_custom_evidence", namespace="/display")
@login_required
def do_create_custom_evidence(data):
    logger.info(f"Client: {request.sid} is creating custom evidence...")

    create_custom_evidence.delay(data=data)


@socketio.on("create_custom_screenshot", namespace="/display")
@login_required
def do_create_custom_screenshot(data):
    logger.info(f"Client: {request.sid} is creating custom screenshot...")

    create_custom_screenshot.delay(data=data)


@socketio.on("see_custom_screenshot", namespace="/display")
@login_required
def do_see_custom_screenshot(reqdata):
    logger.info(f"Client: {request.sid} is requesting to see custom screenshot...")

    sh = ScreenShotHandler()

    sh.set_timestamp_to_picture(filename=reqdata["data"])

    data = getB64_screenshot(filename=reqdata["data"], with_timestamp=True)

    emit(
        "show_screenshot",
        {
            "data": data,
            "url": sh.get_url_by_hash(reqdata["data"]),
            "tab-hash": reqdata["tab-hash"],
            "url-hash": reqdata["data"],
        },
        room=request.sid,
    )

    logger.info(f"Request from Client: {request.sid} is send...")
