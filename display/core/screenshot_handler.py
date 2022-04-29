import hashlib
from collections import defaultdict

from display.webapp.config import Config
from display.webapp.helpers.utils.screenshots import (
    getB64_screenshot,
    get_mod_time,
    get_compare_image,
)
from display.webapp.helpers.utils.sources import get_display_sources


class ScreenShotHandler(object):
    def __init__(self):
        self.config = Config()

        self.display_sources = get_display_sources()

        self.hash_to_tab_mapping = defaultdict()

        self.tab_to_hash_list = defaultdict(list)

        self.hash_to_url_mapping = defaultdict()

        self.set_hash_to_tab_mapping()
        self.set_tab_to_hash_list()
        self.set_hash_to_url_mapping()

    def set_hash_to_tab_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                self.hash_to_tab_mapping[
                    hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                ] = key

        self.hash_to_tab_mapping = dict(self.hash_to_tab_mapping)

    def set_hash_to_url_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                self.hash_to_url_mapping[
                    hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                ] = item["url"]

        self.hash_to_url_mapping = dict(self.hash_to_url_mapping)

    def set_tab_to_hash_list(self):

        for key, value in self.hash_to_tab_mapping.items():
            self.tab_to_hash_list[value].append(key)

        self.tab_to_hash_list = dict(self.tab_to_hash_list)

    def get_tab_by_hash(self, the_hash):

        try:
            return self.hash_to_tab_mapping[the_hash]
        except KeyError:
            return False

    def get_url_by_hash(self, the_hash):

        try:
            return self.hash_to_url_mapping[the_hash]
        except KeyError:
            return False

    def get_hashes_by_tab_name(self, tab_name):

        try:
            return self.tab_to_hash_list[tab_name]
        except KeyError:
            return False

    def get_all_screenshots(self, tab_name):

        ret_data = []

        try:
            screenshot_list = self.get_hashes_by_tab_name(tab_name=tab_name)
            for each in screenshot_list:
                ret_data.append(
                    {
                        "sc_id": each,
                        "sc_src": getB64_screenshot(each),
                        "mod_time": get_mod_time(each),
                        "changed": get_compare_image(each),
                    }
                )
            return ret_data
        except KeyError:
            return ret_data

    def get_changed_screenshots_per_tab(self, tab_name):

        ret_data = []

        try:
            screenshot_list = self.get_hashes_by_tab_name(tab_name=tab_name)
            if screenshot_list is not False:
                for each in screenshot_list:
                    is_changed = get_compare_image(each)
                    if is_changed == "0":
                        ret_data.append(
                            {
                                "sc_id": each,
                                "sc_src": getB64_screenshot(each),
                                "mod_time": get_mod_time(each),
                                "changed": is_changed,
                            }
                        )
                    else:
                        ret_data.append(
                            {
                                "sc_id": each,
                                "mod_time": get_mod_time(each),
                                "changed": is_changed,
                            }
                        )
                return ret_data
        except KeyError:
            return ret_data

    def get_changed_data_from_custom_screenshots(self, the_hash):

        ret_data = []

        is_changed = get_compare_image(the_hash)

        if is_changed == "0":
            ret_data.append(
                {
                    "sc_id": the_hash,
                    "sc_src": getB64_screenshot(the_hash),
                    "mod_time": get_mod_time(the_hash),
                    "changed": is_changed,
                }
            )
        else:
            ret_data.append(
                {
                    "sc_id": the_hash,
                    "mod_time": get_mod_time(the_hash),
                    "changed": is_changed,
                }
            )

        return ret_data

    def __repr__(self):
        return f"<< ScreenShotHandler >>"
