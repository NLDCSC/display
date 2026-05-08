import base64
import os
import re

import cv2
from nldcsc.generic.times import timestampTOdatetimestring

from display.core.screenshots.compare_screenshots import CompareScreenshots
from display.webapp.config import Config

config = Config()
my_file_location = os.path.dirname(os.path.abspath(__file__))


def _safe_join_under_root(root_path: str, *parts: str) -> str:
    base = os.path.realpath(root_path)
    candidate = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, candidate]) != base:
        raise FileNotFoundError("Invalid path")
    return candidate


def _validate_full_path_under_allowed_roots(path: str) -> str:
    candidate = os.path.realpath(path)
    allowed_roots = [
        os.path.realpath(config.SCREENSHOT_LOCATION),
        os.path.realpath(config.TIMELINE_LOCATION),
    ]
    for root in allowed_roots:
        try:
            if os.path.commonpath([root, candidate]) == root:
                return candidate
        except ValueError:
            continue
    raise FileNotFoundError("Invalid path")


def _validate_safe_segment(value: str) -> str:
    if not isinstance(value, str):
        raise FileNotFoundError("Invalid path")
    if value.startswith(("/", "\\")) or os.path.isabs(value):
        raise FileNotFoundError("Invalid path")
    if ".." in value or "/" in value or "\\" in value:
        raise FileNotFoundError("Invalid path")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        raise FileNotFoundError("Invalid path")
    return value


def _screenshot_path(filename: str, suffix: str) -> str:
    safe_filename = _validate_safe_segment(filename)
    return _safe_join_under_root(
        config.SCREENSHOT_LOCATION, f"{safe_filename}{suffix}.png"
    )


def get_mod_time(
    filename,
    no_timezone: bool = True,
    filename_is_full_path: bool = False,
    evidence_shot: bool = False,
):
    try:
        if filename_is_full_path:
            safe_full_path = _validate_full_path_under_allowed_roots(filename)
            time = timestampTOdatetimestring(
                int(os.path.getmtime(safe_full_path)),
                no_timezone,
            )
        else:
            if evidence_shot:
                time = timestampTOdatetimestring(
                    int(
                        os.path.getmtime(
                            _screenshot_path(filename, "_eve")
                        )
                    ),
                    no_timezone,
                )
            else:
                time = timestampTOdatetimestring(
                    int(
                        os.path.getmtime(
                            _screenshot_path(filename, "")
                        )
                    ),
                    no_timezone,
                )
        return time
    except FileNotFoundError:
        return "never"


def get_compare_image(filename):
    cs = CompareScreenshots()

    current_sc_location = _screenshot_path(filename, "")
    old_sc_location = _screenshot_path(filename, "_old")

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
            the_filename = _screenshot_path(filename, "_ts")
        else:
            the_filename = _screenshot_path(filename, "_min")

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
