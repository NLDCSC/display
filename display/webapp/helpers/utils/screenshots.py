import base64
import os

import cv2

from display.core.compare_screenshots import CompareScreenshots
from display.webapp.config import Config
from display.webapp.helpers.utils.times import timestampTOdatetimestring

config = Config()

my_file_location = os.path.dirname(os.path.abspath(__file__))


def getB64_screenshot(filename):
    try:
        with open(
            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png"), "rb"
        ) as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return f"data:image/png;base64, {encoded_string.decode('utf-8')}"
    except Exception:
        with open(
            os.path.join(my_file_location, "../../static", "img/noScreenShot.png"), "rb"
        ) as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return f"data:image/png;base64, {encoded_string.decode('utf-8')}"


def get_mod_time(filename):
    try:
        time = timestampTOdatetimestring(
            int(
                os.path.getmtime(
                    os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png")
                )
            ),
            True,
        )
        return time
    except FileNotFoundError:
        return "never"


def get_compare_image(filename):
    cs = CompareScreenshots()

    try:
        changed = cs.compare_images(
            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png"),
            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}_old.png"),
        )
        if changed:
            return "1"
        else:
            return "0"
    except FileNotFoundError:
        return "0"
    except cv2.error:
        return "0"
    except ValueError:
        return "0"
