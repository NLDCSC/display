import logging
import os
import shutil
from typing import List
from urllib.parse import parse_qs

from flask import request
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import delete, select

from . import admin
from ..app.models import TemplateTexts
from ..auth.permissions import admin_required
from ..run import db, config
from ...core.general.constants import msg_cats

logging.setLoggerClass(AppLogger)
logger = logging.getLogger(__name__)


def parse_nested_list(param_string: str = None):
    ret_list = []

    first_split = param_string.split("entry_field")

    for entry in first_split:
        if entry != "":
            parsed_data = parse_qs(f"entry_field{entry}")

            ret_list.extend(parsed_data["entry_field"])

    return ret_list


@admin.post("/defacement_texts")
@admin_required
def post_defacement_texts():
    data = dict(request.form)

    entries = parse_nested_list(data["form-list"])

    db.session.execute(delete(TemplateTexts).filter())
    db.session.commit()

    for entry in entries:
        new_entry = TemplateTexts(text=entry)
        db.session.add(new_entry)

    db.session.commit()

    return {"msg_cat": msg_cats.OK, "msg": "Defacement texts saved!"}


def get_all_template_texts_obj() -> List[TemplateTexts]:
    all_texts = db.session.scalars(select(TemplateTexts)).all()
    return all_texts


@admin.get("/defacement_texts")
@admin_required
def get_defacement_texts():
    return [x.text for x in get_all_template_texts_obj()]


def clear_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                shutil.rmtree(file_path)
        logger.info(f"All files deleted successfully in {directory_path}")
    except OSError:
        logger.info(f"Error occurred while deleting files in {directory_path}")


@admin.get("/clear/<location>")
@admin_required
def get_clear_location(location):
    try:
        if location == "screenshots":
            clear_directory(config.SCREENSHOT_LOCATION)
        elif location == "defacements":
            db.session.execute(delete(TemplateTexts).filter())
            db.session.commit()
        elif location == "timeline":
            clear_directory(config.TIMELINE_LOCATION)
        else:
            return {
                "msg_cat": msg_cats.NOK,
                "msg": f"{location} is not configured to be cleared!",
            }

        return {"msg_cat": msg_cats.OK, "msg": "Directory / DB cleared!"}
    except OSError as err:
        return {"msg_cat": msg_cats.NOK, "msg": f"{err}"}
