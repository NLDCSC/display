import collections
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from operator import itemgetter
from pathlib import Path
from typing import List, Optional

from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json
from nldcsc.loggers.app_logger import AppLogger

from display.core.general.data_class_validations import Validations
from display.core.general.utils import exclude_optional_dict
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()


@dataclass_json
@dataclass
class Target(Validations):
    url: str
    header: str
    wait: int = 2
    timeout: int = 15
    wait_on_id: str = ""
    team: str = "blue"
    alt_header: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    @property
    def target_hash(self):
        return self.get_hash(self.url.encode("utf-8"))

    @staticmethod
    def get_hash(hash_input: bytes) -> str:
        # noinspection InsecureHash
        return hashlib.md5(hash_input).hexdigest()[:6]

    def to_data_mapping(self):
        the_dict = asdict(self)
        the_dict.pop("alt_header")
        the_dict.pop("header")
        the_dict.pop("team")

        return the_dict


@dataclass_json
@dataclass
class TargetGroup:
    name: str
    targets: List[Target]
    from_headers: bool = False

    @property
    def target_group_hash(self):
        return self.get_hash(self.name.encode("utf-8"))

    def serialize(self):
        if self.from_headers:
            return {
                self.name: sorted(asdict(self)["targets"], key=itemgetter("alt_header"))
            }
        else:
            target_data = asdict(self)["targets"]
            target_data_list = []
            for x in target_data:
                x.pop("alt_header")
                target_data_list.append(x)
            return {self.name: sorted(target_data_list, key=itemgetter("header"))}

    def target_hashes(self) -> List[str]:
        return [x.target_hash for x in self.targets]

    @staticmethod
    def get_hash(hash_input: bytes) -> str:
        # noinspection InsecureHash
        return hashlib.md5(hash_input).hexdigest()[:6]


@dataclass_json
@dataclass
class DisplayConfig:
    config: List[TargetGroup]

    @property
    def hash_to_url(self) -> dict[str, str]:
        ret_dict = {}
        for target_group in self.iterate_primary_only():
            for target in target_group.targets:
                ret_dict[target.target_hash] = target.url
        return ret_dict

    def hash_to_data(self) -> dict[str, dict[str, str | int]]:
        ret_dict = {}
        for target_group in self.iterate_primary_only():
            for target in target_group.targets:
                ret_dict[target.target_hash] = target.to_data_mapping()
        return ret_dict

    @property
    def hash_to_header(self) -> dict[str, str]:
        ret_dict = {}
        for target_group in self.iterate_primary_only():
            for target in target_group.targets:
                ret_dict[target.target_hash] = target.header
        return ret_dict

    def hash_to_tab(self) -> dict[str, List[str]]:
        ret_dict = {}
        for target_group in self.iterate_primary_only():
            for target in target_group.targets:
                if config.SCREENSHOT_HEADER_TABS:
                    ret_dict[target.target_hash] = [
                        target_group.name,
                        self.hash_to_header[target.target_hash],
                    ]
                else:
                    ret_dict[target.target_hash] = target_group.name
        return ret_dict

    def hashes_per_tab(self) -> List[dict[str, List[str]]]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict[target_group.name] = target_group.target_hashes()
        return ret_dict

    @property
    def target_group_to_hash(self) -> dict[str, str]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict[target_group.name] = target_group.target_group_hash
        return ret_dict

    def iterate_primary_only(self) -> TargetGroup:
        for x in self.config:
            if not x.from_headers:
                yield x

    def iterate_all(self) -> TargetGroup:
        for x in self.config:
            yield x

    def display_sources(self) -> dict[str, dict[str, List[str]]]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict.update(target_group.serialize())
        return ret_dict


class DisplayConfigParser(object):

    def __init__(self, config_dict: dict = None, config_location: Path = None):
        self.config = Config()

        self.logger = logging.getLogger(__name__)

        self.config_dict = config_dict
        self.config_location = config_location

    def get_display_config_obj(self) -> DisplayConfig:
        if self.config_dict is None:
            data = self.read_from_file()
        else:
            data = self.config_dict

        target_group_list = []

        for key, value in data.items():
            target_list = []
            for target in value:
                target_list.append(Target(**target))
            target_group_list.append(TargetGroup(name=key, targets=target_list))

        if self.config.SCREENSHOT_HEADER_TABS:
            ret_dict = collections.defaultdict(list)
            for target, urls in data.items():
                for url_entry in urls:
                    target_data = {**url_entry, **{"alt_header": target}}
                    ret_dict[url_entry["header"]].append(Target(**target_data))

            for key, value in ret_dict.items():
                target_group_list.append(
                    TargetGroup(name=key, targets=value, from_headers=True)
                )

        return DisplayConfig(target_group_list)

    def read_from_file(self) -> dict:
        if self.config_location is None:
            if not os.path.exists(self.config.CONFIG_PATH):
                os.mkdir(self.config.CONFIG_PATH)

            try:
                with open(
                    os.path.join(self.config.CONFIG_PATH, self.config.CONFIG_FILE), "r"
                ) as f:
                    config_json = json.loads(f.read())

                return config_json
            except FileNotFoundError:
                with open(
                    os.path.join(self.config.CONFIG_PATH, self.config.CONFIG_FILE), "w"
                ) as f:
                    f.write(json.dumps({"none": [{}]}))

                display_sources = {"none": [{}]}
                return display_sources
        else:
            try:
                with open(self.config_location, "r") as f:
                    config_json = json.loads(f.read())

                return config_json
            except FileNotFoundError:
                self.logger.warning(f"The provided path does not exist!")

    def __repr__(self):
        return f"<< DisplayConfigParser >>"
