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

from display.core.cache.display_cache import cache
from display.core.general.data_class_validations import Validations
from display.core.general.utils import exclude_optional_dict, chunks
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config()


@dataclass_json
@dataclass
class Target(Validations):
    url: str
    header: str
    wait: int = config.SCREENSHOT_DEFAULT_WAIT
    timeout: int = config.SCREENSHOT_DEFAULT_TIMEOUT
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
        return hashlib.md5(hash_input).hexdigest()[:8]

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
        return hashlib.md5(hash_input).hexdigest()[:8]


@dataclass_json
@dataclass
class DisplayConfig:
    target_groups: List[TargetGroup]

    @property
    def target_count(self) -> int:
        return len([x for x in self.target_groups if not x.from_headers])

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

    def hashes_per_tab(self) -> dict[str, List[str]]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict[target_group.name] = target_group.target_hashes()
        return ret_dict

    def hashes_per_header_tab(self) -> dict[str, List[str]]:
        ret_dict = {}
        for target_group in self.iterate_from_headers_only():
            ret_dict[target_group.name] = target_group.target_hashes()
        return ret_dict

    @property
    def target_group_to_hash(self) -> dict[str, str]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict[target_group.name] = target_group.target_group_hash
        return ret_dict

    @property
    def target_hash_to_group(self) -> dict[str, str]:
        ret_dict = {}
        for key, val in self.target_group_to_hash.items():
            ret_dict[val] = key
        return ret_dict

    def iterate_primary_only(self) -> TargetGroup:
        for x in self.target_groups:
            if not x.from_headers:
                yield x

    def iterate_from_headers_only(self) -> TargetGroup:
        for x in self.target_groups:
            if x.from_headers:
                yield x

    def iterate_all(self) -> TargetGroup:
        for x in self.target_groups:
            yield x

    @property
    def config_hash(self):
        # noinspection InsecureHash
        return hashlib.md5(json.dumps(self.display_sources()).encode()).hexdigest()

    def display_sources(self) -> dict[str, dict[str, List[str]]]:
        ret_dict = {}
        for target_group in self.iterate_all():
            ret_dict.update(target_group.serialize())
        return ret_dict

    def get_display_source_chunk(self, number=0, chunk_size=1):
        ds = self.display_sources()

        try:
            if config.SCREENSHOT_HEADER_TABS:
                chunk_list = list(
                    chunks(
                        [
                            x
                            for x in ds.keys()
                            if not x[:2].lower() in config.DISPLAY_FILTER_FROM_CHUNKS
                        ],
                        chunk_size,
                    )
                )
            else:
                chunk_list = list(
                    chunks(
                        [
                            x
                            for x in ds.keys()
                            if x[:2].lower() in config.DISPLAY_FILTER_FROM_CHUNKS
                        ],
                        chunk_size,
                    )
                )
        except ZeroDivisionError:
            return {}

        ret_data = {}

        if number >= len(chunk_list):
            number = len(chunk_list) - 1

        for each in chunk_list[number]:
            ret_data[each] = ds[each]

        return ret_data


@cache.cache(ttl=config.CACHE_DEFAULT_TIMEOUT)
def get_display_config_file(
    config_location: Path = None,
) -> dict[str, List[dict[str, str | int]]]:
    return get_direct_display_config_file(config_location=config_location)


def get_direct_display_config_file(
    config_location: Path = None,
) -> dict[str, List[dict[str, str | int]]]:
    if config_location is None:
        if not os.path.exists(config.DISPLAY_CONFIG_PATH):
            os.mkdir(config.DISPLAY_CONFIG_PATH)

        try:
            with open(
                os.path.join(config.DISPLAY_CONFIG_PATH, config.DISPLAY_CONFIG_FILE),
                "r",
            ) as f:
                config_json = json.loads(f.read())

            return config_json
        except FileNotFoundError:
            with open(
                os.path.join(config.DISPLAY_CONFIG_PATH, config.DISPLAY_CONFIG_FILE),
                "w",
            ) as f:
                f.write(json.dumps({}))

            display_sources = {}
            return display_sources
    else:
        try:
            with open(config_location, "r") as f:
                config_json = json.loads(f.read())

            return config_json
        except FileNotFoundError:
            raise


class DisplayConfigParser(object):

    def __init__(self, config_dict: dict = None, config_location: Path = None):
        self.logger = logging.getLogger(__name__)

        self.config_dict = config_dict
        self.config_location = config_location

    def get_display_config_obj(self, force: bool = False) -> DisplayConfig:
        if self.config_dict is None:
            try:
                if force:
                    data = get_direct_display_config_file(
                        config_location=self.config_location
                    )
                else:
                    data = get_display_config_file(config_location=self.config_location)
            except FileNotFoundError:
                self.logger.warning(f"The provided config location does not exist!")
                raise
        else:
            data = self.config_dict

        target_group_list = []

        for key, value in data.items():
            target_list = []
            for target in value:
                target_list.append(Target(**target))
            target_group_list.append(
                TargetGroup(
                    name=key, targets=sorted(target_list, key=lambda x: x.header)
                )
            )

        if config.SCREENSHOT_HEADER_TABS:
            ret_dict = collections.defaultdict(list)
            for target, urls in data.items():
                for url_entry in urls:
                    target_data = {**url_entry, **{"alt_header": target}}
                    ret_dict[url_entry["header"]].append(Target(**target_data))

            for key, value in ret_dict.items():
                target_group_list.append(
                    TargetGroup(
                        name=key,
                        targets=sorted(value, key=lambda x: x.header),
                        from_headers=True,
                    )
                )

        return DisplayConfig(sorted(target_group_list, key=lambda x: x.name))

    @staticmethod
    def invalidate_config_file_cache() -> None:
        get_display_config_file.invalidate()

    def __repr__(self):
        return f"<< DisplayConfigParser >>"
