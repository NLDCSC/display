import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml
from nldcsc.loggers.app_logger import AppLogger

from display.core.cache.display_cache import cache
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()

# @dataclass
# class DisplaySettings:
#     targets:
#     screenshot_config:


@cache.cache(ttl=config.CACHE_DEFAULT_TIMEOUT)
def get_display_settings_file(
    settings_location: Path = None,
) -> dict[str, List[dict[str, str | int]]]:
    return get_direct_display_settings_file(settings_location=settings_location)


def get_direct_display_settings_file(
    settings_location: Path = None,
) -> dict[str, List[dict[str, str | int]]]:
    if settings_location is None:
        if not os.path.exists(config.DISPLAY_CONFIG_PATH):
            os.mkdir(config.DISPLAY_CONFIG_PATH)

        try:
            with open(
                os.path.join(config.DISPLAY_CONFIG_PATH, config.DISPLAY_SETTINGS_FILE),
                "r",
            ) as f:
                config_json = f.read()

            return yaml.safe_load(config_json)
        except FileNotFoundError:
            with open(
                os.path.join(config.DISPLAY_CONFIG_PATH, config.DISPLAY_SETTINGS_FILE),
                "w",
            ) as f:
                f.write(yaml.safe_dump({"none": [{}]}))

            display_sources = {"none": [{}]}
            return display_sources
    else:
        try:
            with open(settings_location, "r") as f:
                config_json = f.read()

            return yaml.safe_load(config_json)
        except FileNotFoundError:
            raise


class DisplaySettingsParser(object):
    def __init__(self, settings_location: Path = None):
        self.logger = logging.getLogger(__name__)

        self.settings_location = settings_location

    def get_settings_obj(self, force: bool = False):
        try:
            if force:
                data = get_direct_display_settings_file(
                    settings_location=self.settings_location
                )
            else:
                data = get_display_settings_file(
                    settings_location=self.settings_location
                )
        except FileNotFoundError:
            self.logger.warning(f"The provided config location does not exist!")
            raise
