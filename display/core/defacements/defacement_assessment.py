import collections
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, List, Optional

import cv2
import nltk
import pytesseract
from dataclasses_json import config as json_config
from dataclasses_json import dataclass_json
from nldcsc.loggers.app_logger import AppLogger

from display.core.general.data_class_validations import Validations
from display.core.general.utils import exclude_optional_dict
from display.webapp.config import Config

logging.setLoggerClass(AppLogger)


@dataclass_json
@dataclass
class ImageAssessmentResult(Validations):
    template_text: str
    count: int
    corrected_count: float


@dataclass_json
@dataclass
class ImageAssessment(Validations):
    filename: str
    data_length: int
    results: Optional[List[ImageAssessmentResult]] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


defacement_assessment_text = collections.namedtuple(
    "defacement_assessment_text",
    [
        "NO_TEXT",
        "FULL_MATCH",
        "CORRECTED_COUNT",
        "MULTI_MATCH",
        "NO_DEFACEMENT",
        "NO_TEXT_NO_DEFACEMENT",
        "NO_ASSESSMENT",
        "TEMPLATE_AS_DEFACED",
        "TEMPLATE_NOT_DEFACED",
    ],
)(
    "No text found in screenshot; assuming defacement!",
    "Defacement text found in screenshot (full match)",
    "Defacement text found in screenshot (corrected count match)",
    "Multiple Defacement texts found in screenshot (data_length mod count match)",
    "No defacement detected!",
    "No text found in screenshot; assuming NO defacement!",
    "Picture source could not be assessed!!",
    "Picture comes back as template, assume defaced!",
    "Picture comes back as template, assume NOT defaced!",
)


class DefacementAssessment(object):
    def __init__(self, template_texts: List[str]):
        self.logger = logging.getLogger(__name__)
        self.config = Config()

        self.reg_ex = re.compile(r"\d{4}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}z-bt\d{2}")
        self.reg_domain = re.compile(r"\w+(?:\.\w+){1,4}")

        self.template_texts = template_texts

    @staticmethod
    def remove_non_ascii(text):
        text = re.sub(r"[^\x00-\x7F]", "", text)
        text = re.sub(r"[^\w\s]", "", text)

        return text

    def extract_text_from_image(self, image_path: Path) -> str:
        try:
            image = cv2.imread(image_path.as_posix())
            text = pytesseract.image_to_string(image, "eng")

            data = re.sub(self.reg_domain, "", text)

            data = data.strip().replace("\n", "").lower().replace(" ", "")

            data = re.sub(self.reg_ex, "", data)

            data = self.remove_non_ascii(data)

            return data
        except TypeError:
            raise
        except Exception as e:
            self.logger.error(e)

    def assess_defacement(self, assess_image_obj: ImageAssessment) -> Tuple[bool, str]:

        if assess_image_obj.data_length == 0:
            self.logger.debug(defacement_assessment_text.NO_TEXT)
            if self.config.DISPLAY_ASSUME_NO_TEXT_DEFACED:
                return True, defacement_assessment_text.NO_TEXT
            else:
                return False, defacement_assessment_text.NO_TEXT_NO_DEFACEMENT

        for result in assess_image_obj.results:
            # check for full match
            if result.count == 0:
                self.logger.debug(
                    f"{defacement_assessment_text.FULL_MATCH}: {result.template_text}"
                )
                return True, defacement_assessment_text.FULL_MATCH

            # check for partial match
            if result.corrected_count <= 0.35 or result.count <= 25:
                self.logger.debug(
                    f"{defacement_assessment_text.CORRECTED_COUNT}: {result.template_text}"
                )
                return True, defacement_assessment_text.CORRECTED_COUNT

            if (assess_image_obj.data_length % result.count) == 0:
                self.logger.debug(
                    f"{defacement_assessment_text.MULTI_MATCH}: {result.template_text}"
                )
                return True, defacement_assessment_text.MULTI_MATCH

        return False, defacement_assessment_text.NO_DEFACEMENT

    def assess_image(self, image_path: Path) -> Tuple[bool, str]:
        try:
            data = self.extract_text_from_image(image_path=image_path)
            if data == "noscreenshotavailable":
                # this is the template when no screenshot is available, check settings and determine result
                if self.config.DISPLAY_ASSUME_TEMPLATE_AS_DEFACED:
                    return True, defacement_assessment_text.TEMPLATE_AS_DEFACED
                else:
                    return False, defacement_assessment_text.TEMPLATE_NOT_DEFACED
        except TypeError:
            return False, defacement_assessment_text.NO_ASSESSMENT

        ret_obj = ImageAssessment(
            filename=image_path, data_length=len(data), results=[]
        )

        for template_text in self.template_texts:
            stripped_template_text = self.remove_non_ascii(
                template_text.lower().replace(" ", "")
            )

            count = nltk.edit_distance(stripped_template_text, data)
            self.logger.debug(
                f"File: {image_path} Result: {count} -> "
                f"Corrected: {count / len(stripped_template_text)} -> "
                f"Data length: {len(data)}"
            )

            ret_obj.results.append(
                ImageAssessmentResult(
                    template_text=template_text,
                    count=count,
                    corrected_count=count / len(stripped_template_text),
                )
            )

        result, reason = self.assess_defacement(ret_obj)

        self.logger.info(
            f"Filename: {image_path}, is_defaced: {result}, reason: {reason}"
        )

        return result, reason

    def __repr__(self):
        return f"<< DefacementAssessment >>"
