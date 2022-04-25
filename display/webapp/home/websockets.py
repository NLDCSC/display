import logging
from threading import Lock

from flask import copy_current_request_context, request
from flask_socketio import emit, disconnect, join_room, leave_room

from display.helpers.client_pool import ClientPool
from display.helpers.logger_class import HelperLogger
from display.objects.client_connection import ClientConnection
from display.webapp.run import socketio

logging.setLoggerClass(HelperLogger)

logging.getLogger("socketio.server").setLevel("ERROR")
logging.getLogger("geventwebsocket.handler").setLevel("ERROR")
logging.getLogger("engineio.server").setLevel("ERROR")

logger = logging.getLogger(__name__)

thread = None
thread_lock = Lock()

clients = ClientPool()


def background_thread(client_sid):
    """
    Background task responsible for pushing loglines to connected clients
    """
    global clients

    logger.info("Starting background task for: {}".format(client_sid))
    x = 0
    while True:
        socketio.sleep(1)

        try:
            current_client = clients.get(client_sid)
        except KeyError:
            logger.info(
                "Client disconnected, killing background task for: {}".format(
                    client_sid
                )
            )
            break

        if x % 100 == 0:
            x = 0
            logger.debug(current_client.client_details)

        x += 1


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
    logger.info("Async mode request from: {}".format(request.sid))

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
    logger.info("Client {} received data: {}".format(client_id, data))


@socketio.on("connect", namespace="/display")
def connect():
    global thread, clients

    logger.info("New connections request from: {}".format(request.sid))

    clients.add(ClientConnection(sid=request.sid))

    join_room(request.sid)

    @copy_current_request_context
    def can_connect():
        active_connect()

    with thread_lock:
        thread = socketio.start_background_task(background_thread, request.sid)
    emit("con_request", {"data": "Connected"}, callback=can_connect, room=request.sid)

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_ACK

    logger.debug("Client details: {}".format(clients.fetch_client_details))


@socketio.on("active_connect", namespace="/display")
def active_connect():
    global clients

    this_client = clients.get(request.sid)

    this_client.con_status = this_client.connection_status.CON_CFM
    logger.info("Client connected: {}".format(request.sid))

    logger.info("Total clients connected: {}".format(len(clients.fetch_clients)))

    logger.debug("Client details: {}".format(clients.fetch_client_details))


@socketio.on("disconnect", namespace="/display")
def do_disconnect():
    global clients

    clients.remove(request.sid)

    leave_room(request.sid)

    logger.info("Client disconnected: {}".format(request.sid))
    logger.info("Total clients connected: {}".format(len(clients.fetch_clients)))

    logger.debug("Client details: {}".format(clients.fetch_client_details))
