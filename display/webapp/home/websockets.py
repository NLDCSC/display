import hashlib
import logging

from flask import copy_current_request_context, request, render_template
from flask_socketio import emit, disconnect, join_room, leave_room

from display.core.screenshot_handler import ScreenShotHandler
from display.helpers.client_pool import ClientPool
from display.helpers.logger_class import HelperLogger
from display.objects.client_connection import ClientConnection
from display.webapp.helpers.utils.screenshots import getB64_screenshot
from display.webapp.helpers.utils.sources import get_display_sources
from display.webapp.run import socketio
from display.celery_app.display_daemon import create_custom_screenshot

logging.setLoggerClass(HelperLogger)

logging.getLogger("socketio.server").setLevel("ERROR")
logging.getLogger("geventwebsocket.handler").setLevel("ERROR")
logging.getLogger("engineio.server").setLevel("ERROR")

logger = logging.getLogger(__name__)

clients = ClientPool()


@socketio.on("disconnect_request", namespace="/display")
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
def ping_pong():
    emit("my_pong", room=request.sid)


@socketio.on("async_mode", namespace="/display")
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

    logger.debug(f"Client details: {clients.fetch_client_details()}")


@socketio.on("active_connect", namespace="/display")
def active_connect():
    global clients

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_CFM
    logger.info(f"Client connected: {request.sid}")

    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.debug(f"Client details: {clients.fetch_client_details()}")


@socketio.on("disconnect", namespace="/display")
def do_disconnect():
    global clients

    clients.remove(request.sid)

    leave_room(request.sid)

    logger.info(f"Client disconnected: {request.sid}")
    logger.info(f"Total clients connected: {len(clients.fetch_clients())}")

    logger.debug(f"Client details: {clients.fetch_client_details()}")


@socketio.on("change_display_tab", namespace="/display")
def do_change_display_tab(tab_name):
    global clients

    req_client = clients.get(request.sid)

    if req_client.current_tab is not None:
        leave_room(req_client.current_tab)

    join_room(tab_name["data"])
    old_tab = req_client.current_tab
    req_client.current_tab = tab_name["data"]

    logger.info(
        f"Client: {req_client.sid} is changing room from {old_tab} to {tab_name['data']}"
    )

    sh = ScreenShotHandler()

    tab_data = sh.get_all_screenshots(tab_name=tab_name["data"])

    emit("push_all_screenshots", {"data": tab_data})

    logger.debug(f"Client details: {req_client.client_details()}")


@socketio.on("rebuild_request", namespace="/display")
def do_rebuild_request():
    global clients

    req_client = clients.get(request.sid)

    display_sources = get_display_sources()

    html_data = render_template("partials/content.html", **locals())

    logger.info(f"Client: {req_client.sid} is rebuilding page...")

    emit(
        "rebuild_page",
        {
            "data": html_data,
            "tab": hashlib.md5(req_client.current_tab.encode("utf-8")).hexdigest()[:6],
        },
        room=request.sid,
    )

    logger.debug(f"Client details: {req_client.client_details()}")


@socketio.on("create_custom_screenshot", namespace="/display")
def do_change_display_tab(data):
    logger.info(f"Client: {request.sid} is creating custom screenshot...")

    create_custom_screenshot.delay(data=data)


@socketio.on("see_custom_screenshot", namespace="/display")
def do_change_display_tab(reqdata):
    logger.info(f"Client: {request.sid} is requesting to see custom screenshot...")

    sh = ScreenShotHandler()

    sh.set_timestamp_to_picture(filename=reqdata["data"])

    data = getB64_screenshot(filename=reqdata["data"], with_timestamp=True)

    emit(
        "show_screenshot",
        {
            "data": data,
            "hash": reqdata["data"],
        },
        room=request.sid,
    )

    logger.info(f"Request from Client: {request.sid} is send...")
