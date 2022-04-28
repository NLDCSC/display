from dotenv import load_dotenv

load_dotenv(".env")

import hashlib
import redis
import logging
import json
import os

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import task_prerun, after_setup_task_logger, after_setup_logger
from celery.utils.log import get_task_logger
from flask_socketio import SocketIO

from display.core.screenshot_handler import ScreenShotHandler
from display.helpers.app_logger import AppLogger
from display.webapp.config import Config
from display.core.async_screenshots import AsyncScreenshots


logging.setLoggerClass(AppLogger)

config = Config()

app = Celery(
    "display",
    broker=f"{config.REDIS_URL}{config.REDIS_BROKER_DB}",
    backend=f"{config.REDIS_URL}{config.REDIS_BACKEND_DB}",
    result_extended=True,
    include=["display.celery_app.display_daemon"],
    task_soft_time_limit=36000,
    task_time_limit=48000,
)

socketio = SocketIO(message_queue=config.REDIS_URL)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """
    This function will setup the custom loggers for the workers.

    :param logger: Reference to the default celery logger
    :type logger: logger
    :param args: Positional Arguments
    :type args: list
    :param kwargs: Keyword arguments
    :type kwargs: list
    """
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter("%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s")
        )


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    """
    This function will setup the custom loggers for the tasks.

    :param logger: Reference to the default celery logger
    :type logger: logger
    :param args: Positional Arguments
    :type args: list
    :param kwargs: Keyword arguments
    :type kwargs: list
    """
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter(
                "%(asctime)s - %(task_name)s[%(task_id)s] - %(levelname)-8s - %(message)s"
            )
        )


@task_prerun.connect
def general_task_pre_run_config(task_id, task, *args, **kwargs):

    if not task.ignore_result:

        logger = get_task_logger(__name__)

        task.update_state(state="STARTED")

        logger.info("Task: {}, started!".format(task_id))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Create screenshots every xx seconds
    sender.add_periodic_task(90.0, make_screenshots.s())
    sender.add_periodic_task(30.0, guard_config.s())


@app.task()
def guard_config():
    logger = get_task_logger(__name__)

    logger.info("Starting guard config..")

    try:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "r") as f:
            config_json = json.loads(f.read())

        display_sources = config_json

    except FileNotFoundError:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "w") as f:
            f.write(json.dumps({"none": [{}]}))

        display_sources = {"none": [{}]}

    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    current_hash = hashlib.md5(json.dumps(display_sources).encode()).hexdigest()

    logger.info(f"Current config hash: {current_hash}")

    host, port = config.REDIS_URL.split("//")[1][:-1].split(":")

    with redis.Redis(host=host, port=port, db=7) as conn:
        former_hash = conn.get("config_hash")

        if former_hash is not None:
            former_hash = former_hash.decode("utf-8")

        conn.set("config_hash", current_hash)

    logger.info(f"Current_hash: {current_hash} -- Former_hash: {former_hash}")

    if former_hash != current_hash:
        logger.info("Configs are different, broadcasting client reloads...")
        socketio.emit(
            "config_change", {"data": "reload"}, broadcast=True, namespace="/display"
        )
    else:
        logger.info("Configs match!")

    logger.info("Done with guard config")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def make_screenshots():
    logger = get_task_logger(__name__)

    logger.info("Starting screenshot creation!")

    try:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "r") as f:
            config_json = json.loads(f.read())

        display_sources = config_json

    except FileNotFoundError:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "w") as f:
            f.write(json.dumps({"none": [{}]}))

        display_sources = {"none": [{}]}

    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    logger.info(f"Got urls of {len(display_sources)} sources")

    ss = AsyncScreenshots(display_sources)

    ss.process_async()

    logger.info(f"Finished taking screenshots; processing updates!")

    sh = ScreenShotHandler()
    try:
        for source in display_sources:
            tab_data = sh.get_changed_screenshots_per_tab(tab_name=source)
            socketio.emit(
                "push_all_screenshots",
                {"data": tab_data},
                room=source,
                namespace="/display",
            )
    except Exception as err:
        logger.error(f"Error processing updates.... --> Produced error: {err}")

    logger.info(f"Finished processing updates...")
