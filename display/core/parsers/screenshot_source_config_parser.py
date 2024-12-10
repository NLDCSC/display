import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dataclasses_json import dataclass_json
from nldcsc.loggers.app_logger import AppLogger

from display.core.cache.display_cache import cache
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()


@dataclass_json
@dataclass
class ScreenshotSource:
    name: str
    targets: List[str]

    def serialize(self):
        return {self.name: sorted(self.targets)}


@dataclass_json
@dataclass
class ScreenshotSourceConfig:
    screenshot_source: List[ScreenshotSource]

    @property
    def config_hash(self):
        # noinspection InsecureHash
        return hashlib.md5(json.dumps(self.screenshot_sources()).encode()).hexdigest()

    def iterate_all(self) -> ScreenshotSource:
        for x in self.screenshot_source:
            yield x

    def screenshot_sources(self) -> dict[str, List[str]]:
        ret_dict = {}
        for screenshot_source in self.iterate_all():
            ret_dict.update(screenshot_source.serialize())
        return ret_dict


@cache.cache(ttl=config.CACHE_DEFAULT_TIMEOUT)
def get_screenshot_source_config_file(
    config_location: str = None,
) -> dict[str, List[str]]:
    return get_direct_screenshot_source_config_file(config_location=config_location)


def get_direct_screenshot_source_config_file(
    config_location: str = None,
) -> dict[str, List[str]]:
    if config_location is None:

        if not os.path.exists(config.DISPLAY_CONFIG_PATH):
            os.mkdir(config.DISPLAY_CONFIG_PATH)

        try:
            with open(
                os.path.join(
                    config.DISPLAY_CONFIG_PATH, config.SCREENSHOT_SOURCE_CONFIG_FILE
                ),
                "r",
            ) as f:
                screenshot_config_json = json.loads(f.read())
            return screenshot_config_json

        except FileNotFoundError:
            with open(
                os.path.join(
                    config.DISPLAY_CONFIG_PATH, config.SCREENSHOT_SOURCE_CONFIG_FILE
                ),
                "w",
            ) as f:
                f.write(json.dumps({"none": ["none"]}))

            screenshot_config_json = {"none": ["none"]}
            return screenshot_config_json
    else:
        try:
            with open(config_location, "r") as f:
                config_json = json.loads(f.read())

            return config_json
        except FileNotFoundError:
            raise


class ScreenshotSourceConfigParser(object):

    def __init__(self, config_dict: dict = None, config_location: Path = None):
        self.logger = logging.getLogger(__name__)

        self.config_dict = config_dict
        self.config_location = config_location

    def get_screenshot_source_config_obj(
        self, force: bool = False
    ) -> ScreenshotSourceConfig:
        if self.config_dict is None:
            try:
                if force:
                    data = get_direct_screenshot_source_config_file(
                        config_location=self.config_location
                    )
                else:
                    data = get_screenshot_source_config_file(
                        config_location=self.config_location
                    )
            except FileNotFoundError:
                self.logger.warning(f"The provided config location does not exist!")
                raise
        else:
            data = self.config_dict

        screenshot_source_list = []

        for key, value in data.items():
            screenshot_source_list.append(ScreenshotSource(key, value))

        return ScreenshotSourceConfig(screenshot_source_list)

    @staticmethod
    def invalidate_config_file_cache() -> None:
        get_screenshot_source_config_file.invalidate()

    def __repr__(self):
        return f"<< ScreenshotSourceConfigParser >>"
