import collections
import logging
import os
import shutil
from dataclasses import asdict
from typing import List
from urllib.parse import parse_qs

from flask import request
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import delete, select

from . import admin
from ..app.models import TemplateTexts, Tracelog
from ..auth.permissions import admin_required
from ..run import db, config
from ...core.general.constants import msg_cats
from ...core.parsers.display_config_parser import DisplayConfigParser
from ...core.parsers.display_settings_parser import (
    DisplaySettingsParser,
    DisplayTargetSettings,
    DisplaySettings,
    TeamSettings,
)
from ...core.parsers.screenshot_source_config_parser import ScreenshotSourceConfigParser

logging.setLoggerClass(AppLogger)
logger = logging.getLogger(__name__)

settings_parser = DisplaySettingsParser()
display_config_parser = DisplayConfigParser()
screenshot_source_config_parser = ScreenshotSourceConfigParser()


def parse_nested_list(param_string: str = None):
    ret_list = []

    first_split = param_string.split("entry_field")

    for entry in first_split:
        if entry != "":
            logger.info(f"Parsing defacement text entry for: {entry}")
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

    logger.info("Defacement texts saved!")

    return {"msg_cat": msg_cats.OK, "msg": "Defacement texts saved!"}


def get_all_template_texts_obj() -> List[TemplateTexts]:
    logger.info(f"Fetching defacement texts from database...")
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
        logger.error(f"Error occurred while deleting files in {directory_path}")


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
        elif location == "logging":
            db.session.execute(delete(Tracelog).filter())
            db.session.commit()
        elif location == "config_cache":
            settings_parser.invalidate_settings_cache()
            display_config_parser.invalidate_config_file_cache()
            screenshot_source_config_parser.invalidate_config_file_cache()
        else:
            logger.warning(f"{location} is not configured to be cleared!")
            return {
                "msg_cat": msg_cats.NOK,
                "msg": f"{location} is not configured to be cleared!",
            }

        logger.info(f"Cleared location: {location}!")
        return {
            "msg_cat": msg_cats.OK,
            "msg": f"{str(location).title()} cleared!",
        }
    except OSError as err:
        logger.exception(err)
        return {"msg_cat": msg_cats.NOK, "msg": f"{err}"}


@admin.get("/display_settings")
@admin_required
def get_display_settings():
    settings_obj = settings_parser.get_settings_obj()
    # noinspection PyUnresolvedReferences
    return asdict(settings_obj)


def parse_nested_entries(param_string: str = None):
    ret_dict = collections.defaultdict(dict)

    first_split = param_string.split("name_field")
    try:
        for entry in first_split:
            if entry != "":
                logger.info(f"Parsing settings entry for: {entry}")
                parsed_data = parse_qs(f"name_field{entry}")

                if "wait_on_id_field" in parsed_data:
                    wait_on_id = parsed_data["wait_on_id_field"][0]
                else:
                    wait_on_id = ""

                if "stem_field" in parsed_data:
                    stem = parsed_data["stem_field"][0]
                else:
                    stem = None

                ret_dict[parsed_data["name_field"][0]] = {
                    "name": parsed_data["name_field"][0],
                    "zone": parsed_data["zone_field"][0],
                    "wait": int(parsed_data["wait_field"][0]),
                    "timeout": int(parsed_data["timeout_field"][0]),
                    "wait_on_id": wait_on_id,
                    "protocol": parsed_data["protocol_field"][0],
                    "stem": stem,
                    "screenshot_config": parsed_data["source_field"][0],
                }
    except Exception:
        raise

    return dict(ret_dict)


@admin.post("/display_settings")
@admin_required
def post_display_settings():
    data = dict(request.form)

    try:
        entries = parse_nested_entries(data["form-list"])
    except Exception as err:
        logger.exception(err)
        return {"msg_cat": msg_cats.NOK, "msg": f"{err}"}

    logger.info(f"Received {len(entries)} entries...")

    data_target_list = []

    try:
        for entry in entries:
            data_target_list.append(DisplayTargetSettings(**entries[entry]))

        team_settings = TeamSettings(
            display_team_count=int(data["display_team_count"]),
            display_team_start_at=int(data["display_team_start_at"]),
            display_filter_start=int(data["display_filter_start"]),
            display_filter_end=int(data["display_filter_end"]),
            display_gt_start_at=int(data["display_gt_start_at"]),
            display_root_domain=data["display_root_domain"],
        )

        ds = DisplaySettings(targets=data_target_list, team_settings=team_settings)
    except Exception as err:
        logger.exception(err)
        return {
            "msg_cat": msg_cats.NOK,
            "msg": "Error occurred while parsing display settings",
        }

    logger.info("Writing new settings to settings file...")
    try:
        if settings_parser.write_to_settings(ds):
            logger.info("Writing new configs file...")
            if settings_parser.write_to_configs(ds):
                logger.info("Settings saved and new configs created!")
                return {
                    "msg_cat": msg_cats.OK,
                    "msg": "Settings saved and new configs created!",
                }
            else:
                logger.warning("Settings saved, but no new configs created!")
                return {
                    "msg_cat": msg_cats.NOK,
                    "msg": "Settings saved, but no new configs created!",
                }
        else:
            logger.error("Settings could not be saved!")
            return {"msg_cat": msg_cats.NOK, "msg": "Settings could not be saved!"}
    except Exception as err:
        logger.exception(err)
        return {
            "msg_cat": msg_cats.NOK,
            "msg": "Error occurred while saving settings / config",
        }
