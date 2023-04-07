import base64
from urllib.parse import urlparse

from flask import request
from flask_restx import Namespace, Resource, abort
from werkzeug.exceptions import BadRequestKeyError

from display.celery_app.display_daemon import create_custom_screenshot
from display.core.screenshot_handler import ScreenShotHandler
from .models.general import error
from .models.screenshots import (
    screenshot_data,
    screenshot_create_data,
)
from ..auth.permissions import require_apikey

api = Namespace(
    "Screenshots", description="Endpoints for screenshots", path="/screenshot"
)


@api.route("/")
@api.response(400, "Error processing request", model=error)
@api.response(401, "Unauthorized or missing access token header!", model=error)
@api.response(500, "Uh oh....", model=error)
class Screenshots(Resource):
    @api.marshal_with(screenshot_data, skip_none=True)
    @api.param(
        name="display-url",
        description="The url to retrieve the screenshot from",
        example="https://av.baf.27.berylia.org",
        required=True,
    )
    @require_apikey
    def get(self):
        """
        download screenshot
        This endpoint is used to retrieve the latest screenshot / evidence shot from a given url.
        """
        req = request

        try:
            requested_url = req.values["display-url"]
        except BadRequestKeyError:
            abort(400, "Missing mandatory parameter: 'display-url'")
        except Exception as err:
            abort(400, f"Unknown error requesting screenshot: {err}")

        if not urlparse(requested_url):
            abort(400, "Submitted url is malformed and cannot be parsed....")

        sh = ScreenShotHandler()

        try:

            url_hash = sh.get_hash_by_url(requested_url)

            screenshot_data = sh.set_timestamp_to_picture(
                filename=url_hash, send_buffer=True
            )

            screenshot_data = base64.b64encode(screenshot_data.getvalue()).decode(
                "utf-8"
            )

            ret_data = {"URL": requested_url, "DATA": screenshot_data}

            return ret_data
        except ValueError as err:
            abort(400, f"{err}")
        except FileNotFoundError:
            abort(
                400, "Submitted url has no screenshots on file or is non-existent...."
            )

    @api.marshal_with(screenshot_create_data, skip_none=True)
    @api.param(
        "display-url", description="URL to request new screenshot on", _in="formData"
    )
    @require_apikey
    def put(self):
        """
        create new screenshot
        This endpoint should be used to request the creation of a new screenshot / evidence shot to the display server.
        """

        req = request

        try:
            requested_url = req.form["display-url"]
        except BadRequestKeyError:
            abort(400, "Missing mandatory parameter: 'display-url'")
        except Exception as err:
            abort(400, f"Unknown error requesting screenshot: {err}")

        if not urlparse(requested_url):
            abort(400, "Submitted url is malformed and cannot be parsed....")

        sh = ScreenShotHandler()

        try:

            url_hash = sh.get_hash_by_url(requested_url)

            data = {"data": url_hash}

            create_custom_screenshot.delay(data=data)

            return {"URL": requested_url, "DATA": "Create new screenshot submitted"}
        except ValueError as err:
            abort(400, f"{err}")
