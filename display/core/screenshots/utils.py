import base64
import os

import cv2
from nldcsc.generic.times import timestampTOdatetimestring

from display.core.screenshots.compare_screenshots import CompareScreenshots
from display.webapp.config import Config

config = Config()
my_file_location = os.path.dirname(os.path.abspath(__file__))


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

    current_sc_location = os.path.join(config.SCREENSHOT_LOCATION, f"{filename}.png")
    old_sc_location = os.path.join(config.SCREENSHOT_LOCATION, f"{filename}_old.png")

    if os.path.exists(current_sc_location) and os.path.exists(old_sc_location):
        try:
            not_changed = cs.compare_images(
                current_sc_location,
                old_sc_location,
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
    else:
        return "0"


def get_b64_screenshot(filename, with_timestamp=False):
    try:
        if with_timestamp:
            the_filename = os.path.join(
                config.SCREENSHOT_LOCATION, f"{filename}_ts.png"
            )
        else:
            the_filename = os.path.join(
                config.SCREENSHOT_LOCATION, f"{filename}_min.png"
            )

        if os.path.exists(the_filename):
            with open(the_filename, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
            return f"data:image/png;base64, {encoded_string.decode('utf-8')}"
        else:
            return get_no_screenshot_b64_image_string()
    except Exception as e:
        return get_no_screenshot_b64_image_string()


def get_no_screenshot_b64_image_string() -> str:
    with open(
        os.path.join(my_file_location, "../../webapp/static", "img/noScreenShot.png"),
        "rb",
    ) as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f"data:image/png;base64, {encoded_string.decode('utf-8')}"
