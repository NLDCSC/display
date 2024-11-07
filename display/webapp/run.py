import logging
from datetime import timedelta

from flask import Flask, render_template, g, session
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_socketio import SocketIO
from nldcsc.flask_midddleware.debug_logging import DebugLoggingMiddleware
from nldcsc.flask_midddleware.middleware_manager import MiddlewareManager
from nldcsc.flask_plugins.flask_sqlalchemy import FlaskSQLAlchemy
from nldcsc.loggers.app_logger import AppLogger

from display.webapp.config import Config
from display.webapp.helpers.utils.times import timestampTOdatetimestring

logging.setLoggerClass(AppLogger)
config = Config()

login_manager = LoginManager()
db = FlaskSQLAlchemy()
migrate = Migrate(compare_type=True)
socketio = SocketIO()
mwm = MiddlewareManager()

if config.SSO_LOGIN_ENABLE:
    from nldcsc.sso.flask_sso import SSOConnection

    sso = SSOConnection()


def create_app(version):
    global socketio

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_url_path=f"{config.WEB_ROOT}/static",
    )

    app.config["version"] = "{}".format(version)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299, "pool_timeout": 20}

    app.config["SWAGGER_UI_DOC_EXPANSION"] = "list"
    app.config["RESTX_MASK_SWAGGER"] = False

    if not config.DEBUG:
        app.config["SESSION_COOKIE_NAME"] = "display.session"
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)

    if config.SSO_LOGIN_ENABLE:
        sso.init_app(app)

    socketio_async_mode = "eventlet"
    if config.DEBUG:
        mwm.add_middleware(DebugLoggingMiddleware, 100, app=app)
        socketio_async_mode = "threading"

    mwm.init_app(app=app)
    socketio.init_app(
        app,
        message_queue=config.REDIS_URL,
        async_mode=socketio_async_mode,
        cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS,
    )

    login_manager.init_app(app)
    login_manager.login_message = "Sorry, login required!"
    login_manager.login_message_category = "danger"
    login_manager.login_view = "auth.func_login"
    login_manager.session_protection = "strong"

    from display.webapp.home import home as home_blueprint

    app.register_blueprint(home_blueprint, url_prefix=app.config["WEB_ROOT"])

    from display.webapp.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix=app.config["WEB_ROOT"])

    from display.webapp.api import api_bp as api_blueprint

    app.register_blueprint(api_blueprint, url_prefix=f"{app.config['WEB_ROOT']}/api")

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

    @app.errorhandler(403)
    def page_not_found(error):
        return (
            render_template("errors/403.html", header="Forbidden", error=True),
            403,
        )

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
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)
        session.modified = True
        g.user = current_user

    return app, socketio
