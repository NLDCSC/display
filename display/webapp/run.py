import logging
import time
from datetime import datetime

import colors
import rfc3339 as rfc3339
from flask import Flask, render_template, request, g
from flask_bootstrap import Bootstrap
from flask_fontawesome import FontAwesome

from display.helpers.app_logger import AppLogger
from display.webapp.config import Config
from display.webapp.helpers.utils.times import timestampTOdatetimestring
from flask_socketio import SocketIO

logging.setLoggerClass(AppLogger)

fa = FontAwesome()
bootstrap = Bootstrap()

socketio = SocketIO()

config = Config()


def create_app(version):
    global socketio

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_url_path=f"{config.WEB_ROOT}/static",
    )

    app.config["version"] = "{}".format(version)

    if not config.DEBUG:
        app.config["SESSION_COOKIE_NAME"] = "trigram.session"
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.config.from_object(config)

    fa.init_app(app)
    bootstrap.init_app(app)

    socketio.init_app(app, message_queue=app.config["REDIS_URL"])

    from display.webapp.home import home as home_blueprint

    app.register_blueprint(home_blueprint, url_prefix=app.config["WEB_ROOT"])

    from display.webapp.errors import errors as error_blueprint

    app.register_blueprint(error_blueprint, url_prefix=app.config["WEB_ROOT"])

    @app.context_processor
    def version():
        def get_version():
            return app.config["version"]

        return dict(get_version=get_version)

    @app.context_processor
    def TSToDatetime():
        def TSToDatetime(ts):
            return timestampTOdatetimestring(ts)

        return dict(TSToDatetime=TSToDatetime)

    @app.errorhandler(404)
    def page_not_found(error):
        return (
            render_template("errors/404.html", header="Page Not Found", error=True),
            404,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        return (
            render_template(
                "errors/500.html", header="Internal Server Error", error=True
            ),
            500,
        )

    @app.before_request
    def start_timer():
        g.start = time.time()

    @app.after_request
    def log_request(response):

        now = time.time()
        duration = round(now - g.start, 2)
        dt = datetime.fromtimestamp(now)
        timestamp = rfc3339.rfc3339(dt, utc=True)

        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        host = request.host.split(":", 1)[0]
        args = dict(request.args)

        log_params = [
            ("method", request.method, "blue"),
            ("path", request.path, "blue"),
            ("status", response.status, "yellow"),
            ("duration", duration, "green"),
            ("time", timestamp, "magenta"),
            ("ip", ip, "gray"),
            ("host", host, "gray"),
            ("params", args, "blue"),
        ]

        request_id = request.headers.get("X-Request-ID")
        if request_id:
            log_params.append(("request_id", request_id, "yellow"))

        parts = []
        for name, value, color in log_params:
            part = colors.color("{}={}".format(name, value), fg=color)
            parts.append(part)
        line = " ".join(parts)

        app.logger.info(line)

        return response

    return app, socketio
