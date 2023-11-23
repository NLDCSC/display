import base64
import os

import cv2

from display.core.screenshots.compare_screenshots import CompareScreenshots
from display.webapp.config import Config
from display.webapp.helpers.utils.times import timestampTOdatetimestring

config = Config()

my_file_location = os.path.dirname(os.path.abspath(__file__))


def getB64_screenshot(filename, with_timestamp=False):
    try:
        if with_timestamp:
            the_filename = os.path.join(
                config.SCREENSHOT_LOCATION, f"{filename}_ts.png"
            )
        else:
            the_filename = os.path.join(
                config.SCREENSHOT_LOCATION, f"{filename}_min.png"
            )

        with open(the_filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return f"data:image/png;base64, {encoded_string.decode('utf-8')}"
    except Exception:
        with open(
            os.path.join(my_file_location, "../../static", "img/noScreenShot.png"), "rb"
        ) as image_file:
            encoded_string = base64.b64encode(image_file.read())
        return f"data:image/png;base64, {encoded_string.decode('utf-8')}"


def get_mod_time(
    filename,
    no_timezone: bool = True,
    filename_is_full_path: bool = False,
    evidence_shot: bool = False,
):
    try:
        if filename_is_full_path:
            time = timestampTOdatetimestring(
                int(os.path.getmtime(filename)),
                no_timezone,
            )
        else:
            if evidence_shot:
                time = timestampTOdatetimestring(
                    int(
                        os.path.getmtime(
                            os.path.join(
                                config.SCREENSHOT_LOCATION, f"{filename}_eve.png"
                            )
                        )
                    ),
                    no_timezone,
                )
            else:
                time = timestampTOdatetimestring(
                    int(
                        os.path.getmtime(
                            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png")
                        )
                    ),
                    no_timezone,
                )
        return time
    except FileNotFoundError:
        return "never"


def get_compare_image(filename):
    cs = CompareScreenshots()

    try:
        not_changed = cs.compare_images(
            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png"),
            os.path.join(config.SCREENSHOT_LOCATION, f"{filename}_old.png"),
        )
        if not_changed:
            return "1"
        else:
            return "0"
    except FileNotFoundError:
        return "0"
    except cv2.error:
        return "0"
    except ValueError:
        return "0"
