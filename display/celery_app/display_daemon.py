import base64
import collections
import hashlib
import json
import logging
import math
import os
import shutil
import time
import uuid
from io import BytesIO

import redis
from celery.result import AsyncResult, allow_join_result
from dotenv import load_dotenv
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv(".env")

from kombu import Queue
from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import task_prerun, after_setup_task_logger, after_setup_logger
from celery.utils.log import get_task_logger
from flask_socketio import SocketIO

from display.core.screenshot_handler import ScreenShotHandler
from display.helpers.app_logger import AppLogger
from display.webapp.config import Config
from display.core.async_screenshots import AsyncScreenshots
from display.webapp.helpers.utils.sources import (
    get_display_sources,
    get_display_source_chunk,
    chunks,
)
from pyvirtualdisplay.smartdisplay import SmartDisplay
from selenium import webdriver

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
    task_default_queue="default",
    task_queues=(Queue("default"), Queue("nodes", routing_key="nodes")),
    result_expires=600,
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
    sender.add_periodic_task(
        float(config.SCREENSHOT_REFRESH), balance_screenshot_workload.s()
    )
    sender.add_periodic_task(30.0, guard_config.s())
    sender.add_periodic_task(1800.0, delete_old_timeline_screenshots.s())


@app.task(
    ignore_result=True,
)
def guard_config():
    logger = get_task_logger(__name__)

    logger.info("Starting guard config..")

    try:

        display_sources = get_display_sources()

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
def balance_screenshot_workload():
    logger = get_task_logger(__name__)

    logger.info("Creating balanced workload!")

    try:
        display_sources = get_display_sources()
    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    # Total size of display sources
    tot_size_ds = len(display_sources)

    # divide total size by total_chunks by config
    total_chunks_needed = math.ceil(tot_size_ds / config.SCREENSHOT_CHUNK_SIZE)

    logger.info(f"Total needed chunks calculated: {total_chunks_needed}")

    # check last run chunk number in redis
    host, port = config.REDIS_URL.split("//")[1][:-1].split(":")

    with redis.Redis(host=host, port=port, db=7) as conn:
        last_run_number = conn.get("last_run_number")

        if last_run_number is not None:

            last_run_number = int(last_run_number.decode("utf-8"))

            if last_run_number < total_chunks_needed:
                conn.set("last_run_number", last_run_number + 1)
            else:
                conn.set("last_run_number", 0)
                last_run_number = 0
        else:
            # never run before, storing 0
            conn.set("last_run_number", 0)
            last_run_number = 0

    logger.info(f"Getting display source with number: {last_run_number}")

    display_sources_chunk = get_display_source_chunk(
        number=last_run_number, chunk_size=total_chunks_needed
    )

    make_screenshots.delay(display_sources_chunk)

    logger.info("Done with distributing workload!")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def make_screenshots(display_sources):
    logger = get_task_logger(__name__)

    logger.info("Starting repeating screenshot creation!")

    logger.info(f"Got urls of {len(display_sources)} sources")

    ss = AsyncScreenshots(display_sources)

    if hasattr(ss, "selenium_workload"):
        if len(ss.selenium_workload) != 0:
            for each in ss.selenium_workload:
                for target, urls in each.items():
                    push_to_nodes.delay(urls)

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
            handle_changes_for_timeline.delay(data=tab_data)
    except Exception as err:
        logger.error(f"Error processing updates.... --> Produced error: {err}")

    logger.info(f"Finished processing updates...")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def push_to_nodes(workload):
    logger = get_task_logger(__name__)

    logger.info("Pushing screenshots to nodes...")

    task_ids = []

    chunked_list = chunks(workload, config.SCREENSHOT_NODES)

    for each in chunked_list:
        res = execute_on_node.apply_async(
            queue="nodes",
            kwargs={"entries": each},
        )
        task_ids.append(res.id)

    logger.info("Done pushing screenshots to nodes!!")

    logger.info(f"Task ids: {task_ids}")

    monitoring_nodes_results.delay(task_ids)


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
)
def monitoring_nodes_results(data):
    logger = get_task_logger(__name__)

    logger.info(f"Starting monitoring task ids: {data}")

    tasks_ready = []
    do_loop = True

    while do_loop:
        for each in data:
            if each not in tasks_ready:
                res = AsyncResult(each, app=app)
                if res.ready():
                    logger.info(
                        f"Task {each} is ready, removing from list and processing data...."
                    )
                    tasks_ready.append(each)
                    try:
                        with allow_join_result():
                            screenshot_list = res.get(timeout=1)

                        ret_screenshot_data = collections.defaultdict(dict)

                        for screenshot_data in screenshot_list:

                            for k, v in screenshot_data.items():
                                url_hash = k
                                if v == "ERROR":
                                    ret_screenshot_data[k] = v
                                else:
                                    if "evidence" in v:
                                        ret_screenshot_data[k][
                                            "evidence"
                                        ] = base64.b64decode(v["evidence"])
                                    if "normal" in v:
                                        ret_screenshot_data[k][
                                            "normal"
                                        ] = base64.b64decode(v["normal"])

                        ss = AsyncScreenshots()
                        ss.process_async(results=[ret_screenshot_data])

                        sh = ScreenShotHandler()

                        if len(screenshot_list) == 1:

                            source = sh.get_tab_by_hash(url_hash)
                            try:
                                tab_data = sh.get_changed_data_from_custom_screenshots(
                                    the_hash=url_hash
                                )
                                socketio.emit(
                                    "push_all_screenshots",
                                    {"data": tab_data},
                                    room=source,
                                    namespace="/display",
                                )
                                handle_changes_for_timeline.delay(
                                    data=tab_data, csc=True
                                )
                            except Exception as err:
                                logger.error(
                                    f"Error processing updates.... --> Produced error: {err}"
                                )

                        else:

                            url_hash = list(ret_screenshot_data.keys())[0]
                            source = sh.get_tab_by_hash(url_hash)

                            try:
                                tab_data = sh.get_changed_screenshots_per_tab(
                                    tab_name=source
                                )
                                socketio.emit(
                                    "push_all_screenshots",
                                    {"data": tab_data},
                                    room=source,
                                    namespace="/display",
                                )
                                handle_changes_for_timeline.delay(data=tab_data)
                            except Exception as err:
                                logger.error(
                                    f"Error processing updates.... --> Produced error: {err}"
                                )

                        resulting_tasks = len(data) - len(tasks_ready)

                        if resulting_tasks == 0:
                            do_loop = False

                        logger.info(
                            f"Processing task {each} ready; still {resulting_tasks} tasks to monitor"
                        )
                    except Exception as err:
                        logger.error(f"Error fetching results: {err}")

    logger.info(f"Done monitoring {len(data)} tasks!!")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
)
def execute_on_node(entries, scroll_percent=0, evidence=True):
    logger = get_task_logger(__name__)
    ret_data = []

    if evidence:

        logger.info("Starting evidence screenshot creation!")

        try:
            logger.info(f"Setting up smartdisplay....")
            with SmartDisplay(visible=False, size=(1137, 853)) as display:

                logger.info(f"Setting up webdriver....")

                with webdriver.Firefox() as driver:

                    for entry in entries:
                        driver.set_page_load_timeout(int(entry["timeout"]))

                        logger.info(
                            f"Driver set to timeout: {entry['timeout']} and implicit wait: {entry['wait']}"
                        )

                        url_hash = hashlib.md5(
                            entry["url"].encode("utf-8")
                        ).hexdigest()[:6]

                        logger.info(f"Working on hash: {url_hash} ({entry['url']})...")

                        try:

                            driver.get(entry["url"])

                            if "wait_on_id" in entry and entry["wait_on_id"] != "":
                                try:
                                    WebDriverWait(driver, int(entry["wait"])).until(
                                        expected_conditions.presence_of_element_located(
                                            (By.ID, entry["wait_on_id"])
                                        )
                                    )
                                    logger.info("Page is ready!")
                                except TimeoutException:
                                    logger.info(
                                        "Loading took too much time....Taking screenshot anyway...."
                                    )
                                    pass

                            time.sleep(1.5)

                            if scroll_percent > 0:
                                driver.execute_script(
                                    "window.scrollTo(0, document.body.scrollHeight*{0:.2f});".format(
                                        scroll_percent
                                    )
                                )

                            with BytesIO() as buffered:
                                img = display.waitgrab(1)
                                img.resize((1024, 768))
                                img.save(buffered, format="PNG")

                                data = base64.b64encode(buffered.getvalue())

                            data_normal = driver.get_screenshot_as_base64()

                            logger.info(f"Got image data (first 25 bytes): {data[:25]}")
                            ret_data.append(
                                {
                                    url_hash: {
                                        "evidence": data.decode("utf-8"),
                                        "normal": data_normal,
                                    }
                                }
                            )

                        except Exception:
                            ret_data.append({url_hash: "ERROR"})

                    logger.info("Done taking screenshots, returning data!")
                    return ret_data

        except Exception as err:
            logger.error(f"Error encountered while taking screenshots: {err}")

    else:

        logger.info("Starting repeating screenshot creation!")

        try:
            logger.info(f"Setting up smartdisplay....")
            with SmartDisplay(visible=False, size=(1137, 853)) as display:

                logger.info(f"Setting up webdriver....")

                with webdriver.Firefox() as driver:

                    for entry in entries:
                        driver.set_page_load_timeout(int(entry["timeout"]))

                        logger.info(
                            f"Driver set to timeout: {entry['timeout']} and implicit wait: {entry['wait']}"
                        )

                        url_hash = hashlib.md5(
                            entry["url"].encode("utf-8")
                        ).hexdigest()[:6]

                        logger.info(f"Working on hash: {url_hash} ({entry['url']})...")

                        try:

                            driver.get(entry["url"])

                            if "wait_on_id" in entry and entry["wait_on_id"] != "":
                                try:
                                    WebDriverWait(driver, int(entry["wait"])).until(
                                        expected_conditions.presence_of_element_located(
                                            (By.ID, entry["wait_on_id"])
                                        )
                                    )
                                    logger.info("Page is ready!")
                                except TimeoutException:
                                    logger.info(
                                        "Loading took too much time....Taking screenshot anyway...."
                                    )
                                    pass

                            time.sleep(1.5)

                            driver.execute_script("scroll(0, -500);")

                            data = driver.get_screenshot_as_base64()

                            logger.info(f"Got image data (first 25 bytes): {data[:25]}")
                            ret_data.append({url_hash: {"normal": data}})

                        except Exception as err:
                            logger.error(f"Encountered error: {err}")
                            ret_data.append({url_hash: "ERROR"})

                    logger.info("Done taking screenshots, returning data!")
                    return ret_data

        except Exception as err:
            logger.error(f"Error encountered while taking screenshots: {err}")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def create_custom_screenshot(data):
    logger = get_task_logger(__name__)

    logger.info(f"Starting custom screenshot creation on {data}!")

    sh = ScreenShotHandler()

    url_data = sh.get_data_by_hash(data["data"])

    display_sources = {sh.get_tab_by_hash(data["data"]): [url_data]}

    logger.info(f"Hash mapped to url: {display_sources}!")

    ss = AsyncScreenshots(display_sources)

    if hasattr(ss, "selenium_workload"):
        if len(ss.selenium_workload) != 0:
            for each in ss.selenium_workload:
                for target, urls in each.items():
                    push_to_nodes.delay(urls)

    if hasattr(ss, "workload"):
        ss.process_async()

        logger.info(f"Finished taking screenshot; processing....")

        try:
            for source in display_sources:
                tab_data = sh.get_changed_data_from_custom_screenshots(
                    the_hash=data["data"]
                )
                socketio.emit(
                    "push_all_screenshots",
                    {"data": tab_data},
                    room=source,
                    namespace="/display",
                )
                handle_changes_for_timeline.delay(data=tab_data, csc=True)
        except Exception as err:
            logger.error(f"Error processing screenshot.... --> Produced error: {err}")

    logger.info(f"Finished processing screenshot...")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def handle_changes_for_timeline(data: list, csc: bool = False):
    logger = get_task_logger(__name__)

    logger.info(f"Starting saving changed screenshots on: {len(data)} data items!")

    for each in data:
        if int(each["changed"]) == 0:
            # changed content; save a copy of the current screenshot
            if not os.path.exists(
                os.path.join(config.TIMELINE_LOCATION, each["sc_id"])
            ):
                logger.info(
                    f"Creating {os.path.join(config.TIMELINE_LOCATION, each['sc_id'])}"
                )
                os.mkdir(os.path.join(config.TIMELINE_LOCATION, each["sc_id"]))

            if csc:
                new_filename = f"csc-{uuid.uuid4()}.png"
            else:
                new_filename = f"{uuid.uuid4()}.png"

            # create a copy of the changed screenshot and copy it to the timeline directory
            shutil.copyfile(
                os.path.join(config.SCREENSHOT_LOCATION, f"{each['sc_id']}.png"),
                os.path.join(config.TIMELINE_LOCATION, each["sc_id"], new_filename),
            )

            evidence_path = os.path.join(
                config.SCREENSHOT_LOCATION, f"{each['sc_id']}_eve.png"
            )
            new_filename = f"eve-{uuid.uuid4()}.png"

            if os.path.exists(evidence_path):
                shutil.copyfile(
                    evidence_path,
                    os.path.join(config.TIMELINE_LOCATION, each["sc_id"], new_filename),
                )


@app.task(
    ignore_result=True,
)
def delete_old_timeline_screenshots():
    logger = get_task_logger(__name__)

    current_time = time.time()
    days_to_delete = config.DAYS_TO_KEEP_TIMELINE_SCREENSHOTS
    directory = config.TIMELINE_LOCATION

    for dir_path, _, filenames in os.walk(directory):
        for f in filenames:
            file_path = os.path.abspath(os.path.join(dir_path, f))
            creation_time = os.path.getmtime(file_path)
            logger.debug("file available: {}".format(file_path))
            if (current_time - creation_time) // (24 * 3600) >= days_to_delete:
                os.unlink(file_path)
                logger.info("{} removed".format(file_path))
            else:
                logger.debug("{} not removed".format(file_path))
