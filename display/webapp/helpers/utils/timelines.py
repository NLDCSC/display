import os
from pathlib import Path

from display.webapp.config import Config
from display.webapp.helpers.utils.times import timestampTOdatetimestring

config = Config()


def get_mtime_sorted_timeline_dir_from_hash(url_hash: str):
    paths = sorted(Path(os.path.join(config.TIMELINE_LOCATION, url_hash)).iterdir(), key=os.path.getmtime, reverse=True)

    return paths


def get_mod_time_from_path(file_path: str, no_timezone: bool = True):
    try:
        time = timestampTOdatetimestring(
            int(
                os.path.getmtime(file_path)
            ),
            no_timezone,
        )
        return time
    except FileNotFoundError:
        return "never"
