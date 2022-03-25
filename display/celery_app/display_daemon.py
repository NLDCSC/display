from dotenv import load_dotenv

load_dotenv(".env")

import logging
import json
import os

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import task_prerun, after_setup_task_logger, after_setup_logger
from celery.utils.log import get_task_logger

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


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """
    This function will setup the custom loggers for the certexmon workers.

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
    This function will setup the custom loggers for the certexmon tasks.

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
    # Create screenshots every 60 seconds
    sender.add_periodic_task(60.0, make_screenshots.s())


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
            f.write(json.dumps([{}]))

        display_sources = [{}]

    logger.info(f"Got display_sources: {display_sources}")

    ss = AsyncScreenshots(display_sources)

    ss.process_async()
