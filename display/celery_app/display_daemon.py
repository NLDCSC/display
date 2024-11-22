from dotenv import load_dotenv

from display.core.parsers.screenshot_source_config_parser import (
    ScreenshotSourceConfigParser,
)

load_dotenv(".env")

import contextlib
import base64
import collections
import json
import logging
import math
import os
import shutil
import time
import uuid

from io import BytesIO
from pathlib import Path
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from kombu import Queue
from celery import Celery
from sqlalchemy import delete
from selenium import webdriver
from celery.result import AsyncResult, allow_join_result
from celery.signals import (
    task_prerun,
    worker_process_init,
    setup_logging,
    task_failure,
    task_postrun,
    task_retry,
    after_task_publish,
    beat_init,
)
from celery.utils.log import get_task_logger
from flask_socketio import SocketIO
from celery.backends.database import SessionManager

from display.core.general.constants import (
    tracelog_action,
    tracelog_result,
    task_result,
)
from display.webapp.app.models import Tracelog
from display.core.screenshots.screenshot_handler import ScreenShotHandler
from display.core.files.dedub_files import DeduplicateFilesInFolder
from display.webapp.config import Config
from display.core.screenshots.async_screenshots import AsyncScreenshots
from display.core.general.utils import chunks
from display.core.parsers.display_config_parser import DisplayConfigParser
from display.core.database_logging.trace_log import TraceLogEntry
from display.core.tasks.task_result import TaskResult
from display.core.redis_utils.redis_utils_class import RedisUtils
from pyvirtualdisplay.smartdisplay import SmartDisplay
from nldcsc.loggers.app_logger import AppLogger
from nldcsc.flask_plugins.flask_redis import FlaskRedis

logging.setLoggerClass(AppLogger)

config = Config()

READINESS_FILE = Path("/tmp/beat_ready")
HEARTBEAT_FILE = Path("/tmp/beat_live")

app = Celery(
    "display",
    broker=f"{config.REDIS_URL}{config.REDIS_BROKER_DB}",
    backend=f"{config.REDIS_URL}{config.REDIS_BACKEND_DB}",
    result_extended=True,
    include=["display.celery_app.display_daemon"],
    task_time_limit=config.CELERY_TASK_TIME_LIMIT,
    task_default_queue="default",
    task_queues=(Queue("default"), Queue("nodes", routing_key="nodes")),
    broker_connection_retry_on_startup=True,
    result_expires=config.CELERY_RESULT_EXPIRES,
)

socketio = SocketIO(message_queue=config.REDIS_URL)
redis_client = FlaskRedis(init_standalone=True).redis_client

display_config_parser = DisplayConfigParser()
screenshot_source_config_parser = ScreenshotSourceConfigParser()

execution_times = {}


@worker_process_init.connect
def worker_proc_init(**kwargs):
    pass


@setup_logging.connect
def setup_logging(logger, *args, **kwargs):
    # Disregard all celery processing on loggers and let the generic loggerClass handle the configuration of the loggers
    pass


@task_prerun.connect
def general_task_pre_run_config(task_id, task, *args, **kwargs):
    logger = get_task_logger(__name__)

    execution_times[task_id] = time.time()

    task.update_state(state="STARTED")

    logger.info("Task: {}, started!".format(task_id))


@task_retry.connect
def general_task_retry_config(request, reason, einfo, *args, **kwargs):
    logger = get_task_logger(__name__)

    logger.warning(f"Task retry initiated reason: {reason}")


@task_postrun.connect
def general_task_post_run_config(task_id, task, retval, state, *args, **kwargs):
    logger = get_task_logger(__name__)

    try:
        cost = time.time() - execution_times.pop(task_id)
    except KeyError:
        cost = -1

    logger.info(
        f"Task post run cost: {cost}, State: {state}, Task: {task}, RetVal: {retval}"
    )

    task.request.update(task_execution_time=cost)

    if "task_slug" in task.request.kwargs:
        task_slug = task.request.kwargs["task_slug"]
    else:
        task_slug = task.name

    if not task.ignore_result:
        if isinstance(retval, Exception) or retval is None:
            logger.info(f"Completed {task.name} [{task_id}]")

            task.backend.client.set(
                f"runresult_{task_slug}",
                config.CELERY_TASK_FAILED_ERROR_CODE,
                ex=86400,
            )
            task.backend.client.hincrby(f"counter_{task_slug}", "failed", 1)

            insert_time = int(time.time())
            task.backend.client.zadd(
                f"sortresults_{task_slug}", {f"{task_slug}_{task_id}": insert_time}
            )
            task.backend.client.hset(
                f"{task_slug}_{task_id}",
                mapping={
                    "state": "FAILURE",
                    "status": config.CELERY_TASK_FAILED_ERROR_CODE,
                    "cost": cost,
                    "messages": json.dumps(
                        [
                            {"data": f"{type(retval)}"},
                        ]
                    ),
                    "errors": json.dumps([]),
                    "inserted": insert_time,
                    "task_id": task_id,
                },
            )
            task.backend.client.expire(
                name=f"{task_slug}_{task_id}",
                time=config.CELERY_KEEP_TASK_RESULT * 60 * 60 * 24,
            )
        elif isinstance(retval, TaskResult):
            task.backend.client.set(f"runresult_{task_slug}", retval.status, ex=86400)
            if retval.status == task_result.SUCCESS:
                task.backend.client.hincrby(f"counter_{task_slug}", "success", 1)
                logger.info(f"Completed {task.name} [{task_id}]")
            else:
                task.backend.client.hincrby(f"counter_{task_slug}", "failed", 1)
                logger.warning(
                    f"Completed {task.name} [{task_id}]; execution failed..."
                )

            insert_time = int(time.time())
            task.backend.client.zadd(
                f"sortresults_{task_slug}", {f"{task_slug}_{task_id}": insert_time}
            )
            task.backend.client.hset(
                f"{task_slug}_{task_id}",
                mapping={
                    "state": state,
                    "status": retval.status,
                    "cost": cost,
                    "messages": json.dumps(retval.messages),
                    "errors": json.dumps(retval.errors),
                    "inserted": insert_time,
                    "task_id": task_id,
                },
            )
            task.backend.client.expire(
                name=f"{task_slug}_{task_id}",
                time=config.CELERY_KEEP_TASK_RESULT * 60 * 60 * 24,
            )

        else:
            task.backend.client.set(
                f"runresult_{task_slug}", retval["status"], ex=86400
            )
            task.backend.client.hincrby(f"counter_{task_slug}", "success", 1)

            insert_time = int(time.time())
            task.backend.client.zadd(
                f"sortresults_{task_slug}", {f"{task_slug}_{task_id}": insert_time}
            )
            task.backend.client.hset(
                f"{task_slug}_{task_id}",
                mapping={
                    "state": state,
                    "status": retval["status"],
                    "cost": cost,
                    "messages": json.dumps(retval),
                    "errors": json.dumps([]),
                    "inserted": insert_time,
                    "task_id": task_id,
                },
            )
            task.backend.client.expire(
                name=f"{task_slug}_{task_id}",
                time=config.CELERY_KEEP_TASK_RESULT * 60 * 60 * 24,
            )

    logger.info("Task execution completed!")


@task_failure.connect
def general_task_failure_config(task_id, exception, traceback, einfo, *args, **kwargs):
    logger = get_task_logger(__name__)

    logger.exception(exception)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Create screenshots every xx seconds
    sender.add_periodic_task(
        float(config.SCREENSHOT_REFRESH), balance_screenshot_workload.s()
    )
    sender.add_periodic_task(30.0, guard_config.s())
    sender.add_periodic_task(30.0, ping.s())
    sender.add_periodic_task(60.0, delete_duplicate_timeline_entries.s())
    sender.add_periodic_task(60.0, store_node_status.s())
    sender.add_periodic_task(1800.0, delete_old_timeline_screenshots.s())
    sender.add_periodic_task(1800.0, delete_old_log_entries.s())


@beat_init.connect
def startup_tasks(sender, **kwargs):
    """
    Tasks that should be run when beat starts, if two task share the same index they are chained.
        1. Ping that the daemon is alive is nice to have.
        2. Fire guard_config.
    """
    logger = get_task_logger(__name__)

    logger.info("Running startup tasks")
    logger.info(f"sending task {ping.delay()} (ping)")
    logger.info(f"sending task {guard_config.delay()} (guard_config)")
    # touching file is needed as a check possibility
    READINESS_FILE.touch()


@after_task_publish.connect()
def task_published(**_):
    # touching file is needed as a heartbeat check possibility
    HEARTBEAT_FILE.touch()


@contextlib.contextmanager
def get_db_session():
    session_logger = logging.getLogger(__name__)

    session_manager = SessionManager()
    engine, Session = session_manager.create_session(config.SQLALCHEMY_DATABASE_URI)
    session = Session()

    try:
        yield session
    except Exception as err:
        session_logger.warning(f"Error inserting data into database: {err}")
        session_logger.exception(err)
        session.rollback()
    finally:
        session.close()


@app.task(
    ignore_result=True,
)
def ping() -> None:
    """
    This function just writes a ping entry into the database logging.
    """
    logger = get_task_logger(__name__)

    logger.info("Still alive!")


@app.task(
    ignore_result=True,
)
def guard_config():
    logger = get_task_logger(__name__)

    logger.info("Starting guard config..")

    try:
        current_display_config = display_config_parser.get_display_config_obj(
            force=True
        )
    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    logger.info(f"Current config hash: {current_display_config.config_hash}")

    former_hash = RedisUtils.decode_redis_output(redis_client.get("config_hash"))

    redis_client.set("config_hash", current_display_config.config_hash)

    logger.info(
        f"Current_hash: {current_display_config.config_hash} -- Former_hash: {former_hash}"
    )

    if former_hash != current_display_config.config_hash:
        logger.info("Configs are different, broadcasting client reloads...")
        # invalidating cache
        display_config_parser.invalidate_config_file_cache()
        socketio.emit("config_change", {"data": "reload"}, namespace="/display")
        logger.info("Broadcast send!")
    else:
        logger.info("Configs match!")

    logger.info("Getting screenshot source config hash")

    try:
        current_source_config = (
            screenshot_source_config_parser.get_screenshot_source_config_obj(force=True)
        )
    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    logger.info(
        f"Current screenshot source config hash: {current_source_config.config_hash}"
    )

    former_hash = RedisUtils.decode_redis_output(
        redis_client.get("screenshot_config_hash")
    )

    redis_client.set("screenshot_config_hash", current_source_config.config_hash)

    logger.info(
        f"Current_hash: {current_source_config.config_hash} -- Former_hash: {former_hash}"
    )

    if former_hash != current_display_config.config_hash:
        logger.info("Configs are different; invalidating cache")
        screenshot_source_config_parser.invalidate_config_file_cache()
        logger.info("Cache invalidated!")
    else:
        logger.info("Screenshot source configs match!")

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
        display_config = display_config_parser.get_display_config_obj()
        display_sources = display_config.display_sources()
    except Exception as err:
        logger.error(f"Unhandled error --> {err}")
        return

    # Total size of display sources
    tot_size_ds = len(display_sources)

    # divide total size by total_chunks by config
    total_chunks_needed = math.ceil(tot_size_ds / config.SCREENSHOT_CHUNK_SIZE)

    logger.info(f"Total needed chunks calculated: {total_chunks_needed}")

    last_run_number = RedisUtils.decode_redis_output(
        redis_client.get("last_run_number")
    )

    if last_run_number is not None:

        if last_run_number < total_chunks_needed:
            redis_client.set("last_run_number", last_run_number + 1)
        else:
            # Reset last_run_number to 0 and set 1 for the next run to prevent 0 from running twice
            redis_client.set("last_run_number", 1)
            last_run_number = 0
    else:
        # never run before, storing 0
        redis_client.set("last_run_number", 0)
        last_run_number = 0

    logger.info(f"Getting display source with number: {last_run_number}")

    display_sources_chunk = display_config.get_display_source_chunk(
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

    if hasattr(ss, "workload"):
        if len(ss.workload) != 0:
            ss.process_async()

            logger.info(f"Finished taking screenshots; processing updates!")

            sh = ScreenShotHandler()

            try:
                for source in display_sources:
                    tab_data = sh.get_changed_screenshots_per_tab(tab_name=source)
                    socketio.emit(
                        "push_all_screenshots",
                        {
                            "data": tab_data,
                            "tab_hash": sh.get_tabhash_by_tabname(source),
                        },
                        to=source,
                        namespace="/display",
                    )

                    for changed_pic in tab_data:
                        changed_sources = sh.get_tab_by_hash(changed_pic["sc_id"])
                        for changed_source in changed_sources:
                            if changed_source != source:
                                socketio.emit(
                                    "push_all_screenshots",
                                    {
                                        "data": tab_data,
                                        "tab_hash": sh.get_tabhash_by_tabname(
                                            changed_source
                                        ),
                                    },
                                    to=changed_source,
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
def push_to_nodes(workload, evidence_shot=False, update_timestamp=False):
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

    monitoring_nodes_results.delay(task_ids, evidence_shot, update_timestamp)


@app.task()
def monitoring_nodes_results(data, evidence_shot=False, update_timestamp=False):
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

                        if screenshot_list is not None:
                            for screenshot_data in screenshot_list:
                                for k, v in screenshot_data.items():
                                    url_hash = k
                                    if v == "ERROR":
                                        ret_screenshot_data[k] = v
                                    else:
                                        if "evidence" in v:
                                            ret_screenshot_data[k]["evidence"] = (
                                                base64.b64decode(v["evidence"])
                                            )
                                        if "normal" in v:
                                            ret_screenshot_data[k]["normal"] = (
                                                base64.b64decode(v["normal"])
                                            )

                            ss = AsyncScreenshots()
                            ss.process_async(
                                results=[ret_screenshot_data],
                                evidence_shot=evidence_shot,
                            )

                        sh = ScreenShotHandler()

                        if len(screenshot_list) == 1:

                            if not evidence_shot or update_timestamp:
                                sources = sh.get_tab_by_hash(url_hash)
                                try:
                                    tab_data = (
                                        sh.get_changed_data_from_custom_screenshots(
                                            the_hash=url_hash,
                                            evidence_shot=evidence_shot,
                                        )
                                    )
                                    for source in sources:
                                        socketio.emit(
                                            "push_all_screenshots",
                                            {
                                                "data": tab_data,
                                                "tab_hash": sh.get_tabhash_by_tabname(
                                                    source
                                                ),
                                            },
                                            to=source,
                                            namespace="/display",
                                        )
                                    handle_changes_for_timeline.delay(data=tab_data)
                                except Exception as err:
                                    logger.error(
                                        f"Error processing updates.... --> Produced error: {err}"
                                    )

                        else:

                            if not evidence_shot:
                                url_hash = list(ret_screenshot_data.keys())[0]

                                sources = sh.get_tab_by_hash(url_hash)

                                all_tab_data = []

                                for source in sources:
                                    try:
                                        tab_data = sh.get_changed_screenshots_per_tab(
                                            tab_name=source
                                        )
                                        all_tab_data.extend(tab_data)
                                        socketio.emit(
                                            "push_all_screenshots",
                                            {
                                                "data": tab_data,
                                                "tab_hash": sh.get_tabhash_by_tabname(
                                                    source
                                                ),
                                            },
                                            to=source,
                                            namespace="/display",
                                        )
                                    except Exception as err:
                                        logger.error(
                                            f"Error processing updates on source {source}.... --> Produced error: {err}"
                                        )
                                # make changes unique to prevent multiple screenshot copies of the same picture
                                unique_all_tab_data = list(
                                    {x["sc_id"]: x for x in all_tab_data}.values()
                                )
                                handle_changes_for_timeline.delay(
                                    data=unique_all_tab_data
                                )

                        resulting_tasks = len(data) - len(tasks_ready)

                        if resulting_tasks == 0:
                            do_loop = False

                        logger.info(
                            f"Processing task {each} ready; still {resulting_tasks} tasks to monitor"
                        )
                    except Exception as err:
                        logger.error(f"Error fetching results: {err}")
                        continue

    logger.info(f"Done monitoring {len(data)} tasks!!")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
)
def execute_on_node(entries, scroll_percent=0):
    logger = get_task_logger(__name__)
    ret_data = []

    logger.info("Starting evidence / screenshot creation!")

    try:
        logger.info(f"Setting up smartdisplay....")
        with SmartDisplay(visible=False, size=(1138, 854)) as display:

            logger.info(f"Setting up webdriver....")

            with webdriver.Firefox() as driver:

                for entry in entries:
                    driver.set_page_load_timeout(int(entry["timeout"]))

                    logger.info(
                        f"Driver set to timeout: {entry['timeout']} and implicit wait: {entry['wait']}"
                    )

                    url_hash = ScreenShotHandler.get_hash(entry["url"].encode("utf-8"))

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


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def create_custom_evidence(data: dict):
    logger = get_task_logger(__name__)

    logger.info(f"Starting custom evidence creation on {data}!")

    sh = ScreenShotHandler()

    url_data = [sh.get_data_by_hash(data["data"])]

    TraceLogEntry(
        url=sh.get_url_by_hash(data["data"]),
        user="DAEMON",
        hash=data["data"],
        action=tracelog_action.OD_EVIDENCE,
        result=tracelog_result.REQUESTED,
        reason="User requested to create a custom evidence shot",
    ).save()

    push_to_nodes.delay(url_data, evidence_shot=True, update_timestamp=True)

    logger.info(f"Finished processing custom evidence shot...")


@app.task(
    autoretry_for=(ConnectionResetError,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=60,
    retry_jitter=False,
    ignore_result=True,
)
def create_custom_screenshot(data: dict):
    logger = get_task_logger(__name__)

    logger.info(f"Starting custom screenshot creation on {data}!")

    sh = ScreenShotHandler()

    url_data = sh.get_data_by_hash(data["data"])

    display_sources = {sh.get_tab_by_hash(data["data"])[0]: [url_data]}

    TraceLogEntry(
        url=sh.get_url_by_hash(data["data"]),
        user="DAEMON",
        hash=data["data"],
        action=tracelog_action.OD_SCREENSHOT,
        result=tracelog_result.REQUESTED,
        reason="User requested to create a custom screenshot",
    ).save()

    logger.info(f"Hash mapped to url: {display_sources}!")

    ss = AsyncScreenshots(display_sources)

    if hasattr(ss, "selenium_workload"):
        if len(ss.selenium_workload) != 0:
            for each in ss.selenium_workload:
                for target, urls in each.items():
                    push_to_nodes.delay(urls)

    if hasattr(ss, "workload"):
        if len(ss.workload) != 0:
            ss.process_async()

            logger.info(f"Finished taking screenshot; processing....")

            try:
                for source in display_sources:
                    tab_data = sh.get_changed_data_from_custom_screenshots(
                        the_hash=data["data"]
                    )
                    socketio.emit(
                        "push_all_screenshots",
                        {
                            "data": tab_data,
                            "tab_hash": sh.get_tabhash_by_tabname(source),
                        },
                        to=source,
                        namespace="/display",
                    )
                    handle_changes_for_timeline.delay(data=tab_data, csc=True)
            except Exception as err:
                logger.error(
                    f"Error processing screenshot.... --> Produced error: {err}"
                )

    logger.info(f"Finished processing custom screenshot...")


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

    sh = ScreenShotHandler()

    evidence_workload = []

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

            # Create evidence of changed screenshot, if not already taken by display nodes....
            url_data = sh.get_data_by_hash(the_hash=each["sc_id"])

            target = sh.get_tab_by_hash(the_hash=each["sc_id"])[0]
            ss = AsyncScreenshots()

            # check if this url is part of the selenium workload, if it isn't append to the evidence workload!
            if config.SCREENSHOT_EVIDENCE_ENABLED:
                try:
                    if target not in ss.screen_shot_sources["selenium"]:
                        evidence_workload.append(url_data)
                except KeyError:
                    # selenium key is not there; so it's safe to add to the evidence workload
                    evidence_workload.append(url_data)

            if csc:
                new_filename = f"csc-{uuid.uuid4()}.png"
            else:
                new_filename = f"{uuid.uuid4()}.png"

            # create a copy of the changed screenshot and copy it to the timeline directory
            shutil.copy2(
                os.path.join(config.SCREENSHOT_LOCATION, f"{each['sc_id']}.png"),
                os.path.join(config.TIMELINE_LOCATION, each["sc_id"], new_filename),
            )

            evidence_path = os.path.join(
                config.SCREENSHOT_LOCATION, f"{each['sc_id']}_eve.png"
            )
            evidence_filename = f"eve-{uuid.uuid4()}.png"

            if os.path.exists(evidence_path):
                shutil.copy2(
                    evidence_path,
                    os.path.join(
                        config.TIMELINE_LOCATION, each["sc_id"], evidence_filename
                    ),
                )

            TraceLogEntry(
                url=sh.get_url_by_hash(each["sc_id"]),
                user="DAEMON",
                hash=each["sc_id"],
                action=tracelog_action.TIMELINE,
                result=tracelog_result.OK,
                reason="Previous state screenshots moved to timeline!",
            ).save()

    if len(evidence_workload) != 0:
        logger.info(
            f"Received evidence workload; count {len(evidence_workload)}, pushing load to nodes..."
        )
        push_to_nodes.delay(evidence_workload, evidence_shot=True)


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


@app.task(
    ignore_result=True,
)
def delete_duplicate_timeline_entries():
    logger = get_task_logger(__name__)

    logger.info("Starting timeline folders deduplication...")

    ddf = DeduplicateFilesInFolder()

    ddf.execute()

    logger.info("Done with deduplication of timeline folders")


@app.task(
    ignore_result=True,
)
def delete_old_log_entries():
    logger = get_task_logger(__name__)

    logger.info("Starting check for removing old log lines from the database")

    with get_db_session() as db:
        # calculate delta in seconds;
        time_delta = config.LOG_PURGE_TIME * 60

        all_logs = db.execute(
            delete(Tracelog).filter(
                Tracelog.timestamp <= (int(time.time()) - time_delta)
            )
        ).rowcount
        db.commit()

        logger.info(f"Deleted {all_logs} log lines!")

    logger.info("Done checking old log lines!")


@app.task(
    ignore_result=True,
)
def store_node_status():
    logger = get_task_logger(__name__)

    logger.info("Storing node status...")

    status_dict = collections.defaultdict(dict)

    inspect_handle = app.control.inspect()

    pinged = inspect_handle.ping()

    for each in pinged:
        if pinged[each] == {"ok": "pong"}:
            status_dict[each]["status"] = "OK"
        else:
            status_dict[each]["status"] = "NOK"

    active = inspect_handle.active()

    for each in active:
        status_dict[each]["active"] = len(active[each])

    stats = inspect_handle.stats()

    for each in stats:
        status_dict[each]["task_count"] = sum(list(stats[each]["total"].values()))
        status_dict[each]["uptime"] = stats[each]["uptime"]
        status_dict[each]["nswap"] = stats[each]["rusage"]["nswap"]

    store_dict = {"timestamp": int(time.time()), "data": dict(status_dict)}

    redis_client.set("node_status", json.dumps(store_dict))

    logger.info("Done storing node status")
