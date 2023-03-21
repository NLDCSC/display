import base64
from urllib.parse import urlparse

from flask import request

from display.celery_app.display_daemon import create_custom_screenshot
from display.core.screenshot_handler import ScreenShotHandler
from . import api


@api.get("/screenshot")
def get_screenshot():

    req = request

    try:
        requested_url = req.headers["display-url"]
    except KeyError:
        return {"ERROR": "Missing mandatory header: 'display_url'"}
    except Exception as err:
        return {"ERROR": f"Unknown error requesting screenshot: {err}"}

    if not urlparse(requested_url):
        return {"ERROR": "Submitted url is malformed and cannot be parsed...."}

    sh = ScreenShotHandler()

    url_hash = sh.get_hash_by_url(requested_url)

    screenshot_data = sh.set_timestamp_to_picture(filename=url_hash, send_buffer=True)

    screenshot_data = base64.b64encode(screenshot_data.getvalue()).decode("utf-8")

    ret_data = {"URL": requested_url, "DATA": screenshot_data}

    return ret_data


@api.put("/screenshot")
def put_screenshot():

    req = request

    try:
        requested_url = req.headers["display-url"]
    except KeyError:
        return {"ERROR": "Missing mandatory header: 'display_url'"}
    except Exception as err:
        return {"ERROR": f"Unknown error submitting screenshot: {err}"}

    if not urlparse(requested_url):
        return {"ERROR": "Submitted url is malformed and cannot be parsed...."}

    sh = ScreenShotHandler()

    url_hash = sh.get_hash_by_url(requested_url)

    data = {'data': url_hash}

    create_custom_screenshot.delay(data=data)

    return {"URL": requested_url, "DATA": "Create new screenshot submitted"}
