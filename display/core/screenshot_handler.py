import hashlib
import logging
import os
from collections import defaultdict
from io import BytesIO

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

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

        self.logger = logging.getLogger(__name__)

        self.display_sources = get_display_sources(self.config.SCREENSHOT_HEADER_TABS)

        self.hash_to_tab_mapping = defaultdict()

        self.tab_to_hash_list = defaultdict(list)

        self.hash_to_url_mapping = defaultdict()

        self.hash_to_data_mapping = defaultdict()

        if self.config.SCREENSHOT_HEADER_TABS:
            self.hash_to_header_mapping = defaultdict()
            self.set_hash_to_header_mapping()

        self.tabname_to_tabhash = defaultdict()
        self.set_tabname_to_tabhash()

        self.tabhash_to_tabname = defaultdict()
        self.set_tabhash_to_tabname()

        self.set_hash_to_tab_mapping()
        self.set_tab_to_hash_list()
        self.set_hash_to_url_mapping()
        self.set_hash_to_data_mapping()

        self.current_wd = os.path.dirname(os.path.abspath(__file__))

    def set_tabname_to_tabhash(self):

        for each in self.display_sources:
            self.tabname_to_tabhash[each] = hashlib.md5(
                each.encode("utf-8")
            ).hexdigest()[:6]

        self.tabname_to_tabhash = dict(self.tabname_to_tabhash)

    def set_tabhash_to_tabname(self):

        for each in self.display_sources:
            self.tabhash_to_tabname[
                hashlib.md5(each.encode("utf-8")).hexdigest()[:6]
            ] = each

        self.tabhash_to_tabname = dict(self.tabhash_to_tabname)

    def set_hash_to_tab_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                self.hash_to_tab_mapping[
                    hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                ] = key

        if self.config.SCREENSHOT_HEADER_TABS:
            for key, value in self.hash_to_header_mapping.items():
                entry = self.hash_to_tab_mapping[key]
                self.hash_to_tab_mapping[key] = [entry, value]

        self.hash_to_tab_mapping = dict(self.hash_to_tab_mapping)

    def set_hash_to_header_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                if item["header"] == key:
                    self.hash_to_header_mapping[
                        hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                    ] = key

        self.hash_to_header_mapping = dict(self.hash_to_header_mapping)

    def set_hash_to_url_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                self.hash_to_url_mapping[
                    hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                ] = item["url"]

        self.hash_to_url_mapping = dict(self.hash_to_url_mapping)

    def set_hash_to_data_mapping(self):

        for key, value in self.display_sources.items():
            for item in value:
                self.hash_to_data_mapping[
                    hashlib.md5(item["url"].encode("utf-8")).hexdigest()[:6]
                ] = {
                    "url": item["url"],
                    "wait": item["wait"],
                    "timeout": item["timeout"],
                    "wait_on_id": item["wait_on_id"],
                }

        self.hash_to_data_mapping = dict(self.hash_to_data_mapping)

    def set_tab_to_hash_list(self):

        for key, value in self.hash_to_tab_mapping.items():
            if isinstance(value, list):
                for each in value:
                    self.tab_to_hash_list[each].append(key)
            elif isinstance(value, str):
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

    def get_data_by_hash(self, the_hash):

        try:
            return self.hash_to_data_mapping[the_hash]
        except KeyError:
            return False

    def get_hashes_by_tab_name(self, tab_name):

        try:
            return self.tab_to_hash_list[tab_name]
        except KeyError:
            return False

    def get_tabhash_by_tabname(self, tab_name):

        try:
            return self.tabname_to_tabhash[tab_name]
        except KeyError:
            return False

    def get_tabname_by_tabhash(self, the_hash):

        try:
            return self.tabhash_to_tabname[the_hash]
        except KeyError:
            return False

    def get_all_screenshots(self, tab_name):

        ret_data = []

        try:
            screenshot_list = self.get_hashes_by_tab_name(tab_name=tab_name)
            if screenshot_list is not False:
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

    def set_timestamp_to_picture(
        self, filename, filename_is_full_path: bool = False, url_hash: str = None
    ):

        if not filename_is_full_path:
            normal_path = os.path.join(
                self.config.SCREENSHOT_LOCATION, f"{filename}.png"
            )

            evidence_path = os.path.join(
                self.config.SCREENSHOT_LOCATION, f"{filename}_eve.png"
            )

            if os.path.exists(evidence_path):
                photo = Image.open(evidence_path)
            else:
                photo = Image.open(normal_path)

            url_hash = filename
        else:
            photo = Image.open(filename)
            url_hash = url_hash

        # Store image width and height
        w, h = photo.size

        # make the image editable
        drawing = ImageDraw.Draw(photo)
        font = ImageFont.truetype(
            os.path.join(
                self.current_wd, "../webapp/static/fonts/Roboto/Roboto-Black.ttf"
            ),
            30,
        )

        # get text width and height
        text = f"    {self.get_url_by_hash(the_hash=url_hash)} @ {get_mod_time(filename, False, filename_is_full_path)}    "
        text_w, text_h = drawing.textsize(text, font)

        pos = w - text_w, (h - text_h) - 50

        c_text = Image.new("RGB", (text_w, text_h + 10), color="#000")
        drawing = ImageDraw.Draw(c_text)

        drawing.text((0, 0), text, fill="#FFFF00FF", font=font)
        c_text.putalpha(1000)

        photo.paste(c_text, pos, c_text)
        if not filename_is_full_path:
            photo.save(
                os.path.join(self.config.SCREENSHOT_LOCATION, f"{filename}_ts.png")
            )
        else:
            # save to memory and return the buffer
            buffered = BytesIO()
            photo.save(buffered, format="PNG")

            return buffered

    def limit_img_size(
        self, filename: str, target_filesize: int = 100000, tolerance: int = 5
    ):
        """
        Limiting input file to a maximum of approximately (give or take the tolerance) of 100 kb
        """
        self.logger.info(f"Scaling down size for hash: {filename}")
        img = img_orig = Image.open(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{filename}.png")
        )
        aspect = img.size[0] / img.size[1]

        while True:
            with BytesIO() as buffer:
                img.save(buffer, format="PNG")
                data = buffer.getvalue()
            filesize = len(data)
            size_deviation = filesize / target_filesize
            self.logger.info(
                "size: {}; factor: {:.3f}".format(filesize, size_deviation)
            )

            if size_deviation <= (100 + tolerance) / 100:
                self.logger.info(f"Scaling fits; saving minified picture...")
                # filesize fits
                with open(
                    os.path.join(
                        self.config.SCREENSHOT_LOCATION, f"{filename}_min.png"
                    ),
                    "wb",
                ) as f:
                    f.write(data)
                self.logger.info("Scaling done!")
                break
            else:
                # filesize not good enough => adapt width and height
                # use sqrt of deviation since applied both in width and height
                new_width = img.size[0] / size_deviation**0.5
                new_height = new_width / aspect
                # resize from img_orig to not lose quality
                img = img_orig.resize((int(new_width), int(new_height)))

    def __repr__(self):
        return f"<< ScreenShotHandler >>"
