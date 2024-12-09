import collections
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dataclasses_json import config as json_config, dataclass_json
from nldcsc.loggers.app_logger import AppLogger

from display.core.cache.display_cache import cache
from display.core.general.utils import exclude_optional_dict
from display.core.parsers.display_config_parser import Target, DisplayConfigParser
from display.core.parsers.screenshot_source_config_parser import (
    ScreenshotSourceConfigParser,
)
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()


class IndentDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


def exclude_default_protocol(value):
    return value == "https"


def exclude_default_wait_on_id(value):
    return value == ""


def exclude_default_wait_time(value):
    return value == config.SCREENSHOT_DEFAULT_WAIT


def exclude_default_timeout(value):
    return value == config.SCREENSHOT_DEFAULT_TIMEOUT


@dataclass_json
@dataclass
class DisplayTargetSettings:
    name: str
    zone: str
    wait: Optional[int] = field(
        metadata=json_config(exclude=exclude_default_wait_time),
        default=config.SCREENSHOT_DEFAULT_WAIT,
    )
    timeout: Optional[int] = field(
        metadata=json_config(exclude=exclude_default_timeout),
        default=config.SCREENSHOT_DEFAULT_TIMEOUT,
    )
    wait_on_id: Optional[str] = field(
        metadata=json_config(exclude=exclude_default_wait_on_id), default=""
    )
    protocol: Optional[str] = field(
        metadata=json_config(exclude=exclude_default_protocol), default="https"
    )
    stem: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    screenshot_config: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class TeamSettings:
    display_team_count: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    display_gt_start_at: Optional[int] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    display_root_domain: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class DisplaySettings:
    targets: List[DisplayTargetSettings]
    team_settings: Optional[TeamSettings] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    def create_target_lists_and_screenshot_config(self):
        target_dict = collections.defaultdict(list)
        screenshot_config_dict = collections.defaultdict(list)
        for each in self.targets:
            if self.team_settings is not None:
                total_teams = (
                    self.team_settings.display_team_count
                    if self.team_settings.display_team_count is not None
                    else config.DISPLAY_TEAM_COUNT
                )
                start_green = (
                    self.team_settings.display_gt_start_at
                    if self.team_settings.display_gt_start_at is not None
                    else config.DISPLAY_GT_START_AT
                )
                display_root_domain = (
                    self.team_settings.display_root_domain
                    if self.team_settings.display_root_domain is not None
                    else config.DISPLAY_ROOT_DOMAIN
                )
            else:
                total_teams = config.DISPLAY_TEAM_COUNT
                start_green = config.DISPLAY_GT_START_AT
                display_root_domain = config.DISPLAY_ROOT_DOMAIN

            for i in range(1, total_teams + 1):
                # noinspection PyUnresolvedReferences
                target_dict[each.name].append(
                    Target(
                        url=f"{each.protocol}://{each.name if each.stem is None else each.stem}.{each.zone}"
                        f".{'{:02d}'.format(i)}.{display_root_domain}",
                        header=f"BT{'{:02d}'.format(i)}",
                        wait=each.wait,
                        timeout=each.timeout,
                        wait_on_id=each.wait_on_id,
                        team="blue" if i <= start_green - 1 else "green",
                    ).to_dict()
                )
                i += 1

            if each.screenshot_config is not None:
                screenshot_config_dict[each.screenshot_config].append(each.name)

        return dict(target_dict), dict(screenshot_config_dict)


@cache.cache(ttl=config.CACHE_DEFAULT_TIMEOUT)
def get_display_settings_file(
    settings_location: Path = None,
) -> dict[str, dict[str, dict[str, str | int]]]:
    return get_direct_display_settings_file(settings_location=settings_location)


def get_direct_display_settings_file(
    settings_location: Path = None,
) -> dict[str, dict[str, dict[str, str | int]]]:
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
                f.write(
                    yaml.dump(
                        {"targets": []},
                        Dumper=IndentDumper,
                        default_flow_style=False,
                        explicit_start=True,
                    )
                )

            display_settings_file = {"targets": []}
            return display_settings_file
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

        self.display_config_parser = DisplayConfigParser()
        self.screenshot_source_config_parser = ScreenshotSourceConfigParser()

    def get_settings_obj(self, force: bool = False) -> DisplaySettings:
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

        target_settings_list = []
        team_settings_obj = None

        for conf_var, targets in data.items():
            if conf_var == "targets":
                for target_settings in data["targets"]:
                    target_settings_list.append(
                        DisplayTargetSettings(**target_settings)
                    )
            if conf_var == "team_settings":
                team_settings_obj = TeamSettings(**data["team_settings"])
        return DisplaySettings(
            targets=target_settings_list, team_settings=team_settings_obj
        )

    def write_to_settings(
        self, input_obj: DisplaySettings, store_file_location: Path = None
    ) -> bool:

        if store_file_location is not None:
            file_location_store = store_file_location
        else:
            file_location_store = self.settings_location

        try:
            with open(file_location_store, "w") as f:
                # noinspection PyUnresolvedReferences
                f.write(
                    yaml.dump(
                        input_obj.to_dict(),
                        Dumper=IndentDumper,
                        default_flow_style=False,
                        explicit_start=True,
                    )
                )
            return True
        except FileNotFoundError:
            raise
        except PermissionError:
            raise
        except Exception:
            raise

    def write_to_configs(
        self, input_obj: DisplaySettings, invalidate_cache: bool = True
    ) -> bool:

        target_config, screenshot_config = (
            input_obj.create_target_lists_and_screenshot_config()
        )

        try:
            with open(
                os.path.join(
                    config.DISPLAY_CONFIG_PATH, config.SCREENSHOT_SOURCE_CONFIG_FILE
                ),
                "wb",
            ) as f:
                f.write(json.dumps(screenshot_config).encode("utf-8"))
            if invalidate_cache:
                self.screenshot_source_config_parser.invalidate_config_file_cache()

            with open(
                os.path.join(config.DISPLAY_CONFIG_PATH, config.DISPLAY_CONFIG_FILE),
                "wb",
            ) as f:
                f.write(json.dumps(target_config).encode("utf-8"))

            if invalidate_cache:
                self.display_config_parser.invalidate_config_file_cache()
        except FileNotFoundError:
            raise
        except PermissionError:
            raise
        except Exception:
            raise
