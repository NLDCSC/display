import hashlib
import logging
import os
from io import BytesIO
from typing import List, Any

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from display.core.database_logging.trace_log import TraceLogEntry
from display.core.general.constants import tracelog_action, tracelog_result
from display.core.parsers.display_config_parser import DisplayConfigParser
from display.core.screenshots.utils import (
    get_mod_time,
    get_compare_image,
    get_b64_screenshot,
)
from display.webapp.app.models import DefacementTracker
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)

config = Config

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI, **{"pool_recycle": 299, "pool_timeout": 20}
)

Session = sessionmaker(engine)


class ScreenShotHandler(object):
    def __init__(self):
        self.config = Config()

        self.logger = logging.getLogger(__name__)

        self.display_config_parser = DisplayConfigParser()
        try:
            self.display_config = self.display_config_parser.get_display_config_obj()
            self._hash_to_url_mapping = self.display_config.hash_to_url
            self._hash_to_data_mapping = self.display_config.hash_to_data()
            self._hash_to_header_mapping = self.display_config.hash_to_header
            self._hash_to_tab_mapping = self.display_config.hash_to_tab()
            self._tab_to_hash_list = self.display_config.hashes_per_tab()
            self._tabname_to_tabhash = self.display_config.target_group_to_hash
            self._tabhash_to_tabname = self.display_config.target_hash_to_group
        except Exception as e:
            self.logger.error(e)

        self.current_wd = os.path.dirname(os.path.abspath(__file__))

    @property
    def hash_to_url_mapping(self) -> dict[str, str]:
        return self._hash_to_url_mapping

    @property
    def hash_to_data_mapping(self) -> dict[str, dict[str, str | int]]:
        return self._hash_to_data_mapping

    @property
    def hash_to_header_mapping(self) -> dict[str, str]:
        return self._hash_to_header_mapping

    @property
    def hash_to_tab_mapping(self) -> dict[str, List[str]]:
        return self._hash_to_tab_mapping

    @property
    def tab_to_hash_list(self) -> List[dict[str, List[str]]]:
        return self._tab_to_hash_list

    @property
    def tabname_to_tabhash(self) -> dict[str, str]:
        return self._tabname_to_tabhash

    @property
    def tabhash_to_tabname(self) -> dict[str, str]:
        return self._tabhash_to_tabname

    @staticmethod
    def get_hash(hash_input: bytes) -> str:
        # noinspection InsecureHash
        return hashlib.md5(hash_input).hexdigest()[:8]

    def get_tab_by_hash(self, the_hash: str) -> str:

        try:
            return self.hash_to_tab_mapping[the_hash]
        except KeyError:
            return False

    def get_url_by_hash(self, the_hash: str) -> str:

        try:
            return self.hash_to_url_mapping[the_hash]
        except KeyError:
            return False

    def get_data_by_hash(self, the_hash: str) -> str:

        try:
            return self.hash_to_data_mapping[the_hash]
        except KeyError:
            return False

    def get_hashes_by_tab_name(self, tab_name: str) -> List[str]:

        try:
            return self.tab_to_hash_list[tab_name]
        except KeyError:
            return False

    def get_tabhash_by_tabname(self, tab_name: str) -> str:

        try:
            return self.tabname_to_tabhash[tab_name]
        except KeyError:
            return False

    def get_tabname_by_tabhash(self, tab_name: str) -> str:

        try:
            return self.tabhash_to_tabname[tab_name]
        except KeyError:
            return False

    def get_hash_by_url(self, the_url: str) -> str:

        the_hash = self.get_hash(the_url.encode("utf-8"))

        if the_hash in self.hash_to_url_mapping:
            return the_hash
        else:
            raise ValueError(
                "The requested url hash is not a part of the urls in the configuration!"
            )

    def get_hash_screenshot(self, url_hash: str) -> dict[str, Any]:

        ret_data = {
            "sc_id": url_hash,
            "sc_src": get_b64_screenshot(url_hash),
            "mod_time": get_mod_time(url_hash),
            "changed": get_compare_image(url_hash),
            "defaced": self.is_defaced(picture_hash=url_hash),
        }

        return ret_data

    def get_picture_hash(self, picture_hash: str) -> str:

        picture_hash_location = os.path.join(
            self.config.SCREENSHOT_LOCATION, f"{picture_hash}.png"
        )
        if os.path.exists(picture_hash_location):
            try:
                with open(
                    picture_hash_location,
                    "rb",
                ) as f:
                    # noinspection InsecureHash
                    return hashlib.md5(f.read()).hexdigest()
            except FileNotFoundError:
                return ""
        else:
            return ""

    def is_defaced(self, picture_hash: str) -> int:
        with Session.begin() as session:
            def_data = session.scalar(
                select(DefacementTracker.defaced)
                .filter(
                    DefacementTracker.picture_hash
                    == self.get_picture_hash(picture_hash=picture_hash)
                )
                .order_by(DefacementTracker.created_at.desc())
            )

        if def_data is None:
            def_data = 0

        return f"{def_data}"

    def get_changed_screenshots_per_tab(self, tab_name: str) -> List[dict[str, Any]]:

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
                                "sc_src": get_b64_screenshot(each),
                                "mod_time": get_mod_time(each),
                                "changed": is_changed,
                                "defaced": self.is_defaced(picture_hash=each),
                            }
                        )
                        TraceLogEntry(
                            url=self.get_url_by_hash(each),
                            hash=each,
                            action=tracelog_action.STATE_CHANGE,
                            result=tracelog_result.CHANGED,
                        ).save()
                    else:
                        ret_data.append(
                            {
                                "sc_id": each,
                                "mod_time": get_mod_time(each),
                                "changed": is_changed,
                                "defaced": self.is_defaced(picture_hash=each),
                            }
                        )
                        TraceLogEntry(
                            url=self.get_url_by_hash(each),
                            hash=each,
                            action=tracelog_action.STATE_CHANGE,
                            result=tracelog_result.NOT_CHANGED,
                        ).save()
                return ret_data
        except KeyError:
            return ret_data

    def get_changed_data_from_custom_screenshots(
        self,
        the_hash: str,
        evidence_shot: bool = False,
    ):

        ret_data = []

        is_changed = get_compare_image(the_hash)

        if is_changed == "0":
            ret_data.append(
                {
                    "sc_id": the_hash,
                    "sc_src": get_b64_screenshot(the_hash),
                    "mod_time": get_mod_time(the_hash, evidence_shot=evidence_shot),
                    "changed": is_changed,
                    "defaced": self.is_defaced(picture_hash=the_hash),
                }
            )
        else:
            ret_data.append(
                {
                    "sc_id": the_hash,
                    "mod_time": get_mod_time(the_hash, evidence_shot=evidence_shot),
                    "changed": is_changed,
                    "defaced": self.is_defaced(picture_hash=the_hash),
                }
            )

        return ret_data

    def set_timestamp_to_picture(
        self,
        filename: str,
        filename_is_full_path: bool = False,
        url_hash: str = None,
        send_buffer: bool = False,
    ) -> None | BytesIO:

        if not filename_is_full_path:
            screenshot_root = os.path.realpath(self.config.SCREENSHOT_LOCATION)
            normal_path = os.path.realpath(
                os.path.join(screenshot_root, f"{filename}.png")
            )

            evidence_path = os.path.realpath(
                os.path.join(screenshot_root, f"{filename}_eve.png")
            )

            if (
                os.path.commonpath([screenshot_root, normal_path]) != screenshot_root
                or os.path.commonpath([screenshot_root, evidence_path]) != screenshot_root
            ):
                self.logger.warning("Rejected unsafe screenshot path: %s", filename)
                raise ValueError("Unsafe screenshot path")

            if os.path.exists(evidence_path):
                photo = Image.open(evidence_path)
            else:
                if os.path.exists(normal_path):
                    photo = Image.open(normal_path)
                else:
                    # no picture found; storing error picture
                    with open(
                        os.path.join(
                            self.current_wd, "../../webapp/static/img/noScreenShot.png"
                        ),
                        "rb",
                    ) as f:
                        data = f.read()

                    self.logger.debug(f"Setting error picture for {filename}")
                    with open(normal_path, "wb") as f:
                        f.write(data)

                    photo = Image.open(normal_path)

            url_hash = filename
        else:
            photo = Image.open(filename)
            url_hash = url_hash

        # make the image editable
        drawing = ImageDraw.Draw(photo)
        font = ImageFont.truetype(
            os.path.join(
                self.current_wd, "../../webapp/static/fonts/Roboto/Roboto-Black.ttf"
            ),
            20,
        )

        if not filename_is_full_path:
            if os.path.exists(evidence_path):
                text = (
                    f"    {get_mod_time(filename, False, filename_is_full_path, True)}  -  "
                    f"{self.get_tab_by_hash(the_hash=url_hash)[-1]}    "
                )
            else:
                text = (
                    f"    {self.get_url_by_hash(the_hash=url_hash)} @ "
                    f"{get_mod_time(filename, False, filename_is_full_path, False)}    "
                )
        elif filename_is_full_path:
            if os.path.basename(filename)[:4] == "eve-":
                text = (
                    f"    {get_mod_time(filename, False, filename_is_full_path, True)}  -  "
                    f"{self.get_tab_by_hash(the_hash=url_hash)[-1]}    "
                )
            else:
                text = (
                    f"    {self.get_url_by_hash(the_hash=url_hash)} @ "
                    f"{get_mod_time(filename, False, filename_is_full_path, False)}    "
                )
        else:
            text = (
                f"    {self.get_url_by_hash(the_hash=url_hash)} @ "
                f"{get_mod_time(filename, False, filename_is_full_path, False)}    "
            )

        # get text width and height
        text_w = int(drawing.textlength(text, font))
        text_h = int(font.size)

        pos = 0, 0

        c_text = Image.new("RGB", (text_w, text_h + 10), color="#000")
        drawing = ImageDraw.Draw(c_text)

        drawing.text((0, 0), text, fill="#00CC00", font=font)
        c_text.putalpha(1000)

        photo.paste(c_text, pos, c_text)
        if not filename_is_full_path and not send_buffer:
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
    ) -> None:
        """
        Limiting input file to a maximum of approximately (give or take the tolerance) of 100 kb
        """
        self.logger.debug(f"Scaling down size for hash: {filename}")
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
            self.logger.debug(
                "size: {}; factor: {:.3f}".format(filesize, size_deviation)
            )

            if size_deviation <= (100 + tolerance) / 100:
                self.logger.debug(f"Scaling fits; saving minified picture...")
                # filesize fits
                with open(
                    os.path.join(
                        self.config.SCREENSHOT_LOCATION, f"{filename}_min.png"
                    ),
                    "wb",
                ) as f:
                    f.write(data)
                self.logger.debug("Scaling done!")
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
