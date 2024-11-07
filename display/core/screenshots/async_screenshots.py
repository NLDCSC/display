"""
async_header_collector.py
=========================
"""

import asyncio
import json
import logging
import os
import shutil
from collections import defaultdict
from pathlib import Path

import aiohttp
from display.external_apis.splash.splash_api import SplashApi
from nldcsc.loggers.app_logger import AppLogger

from display.core.database_log.db_log import DbLog
from display.core.general.constants import tracelog_action, tracelog_result
from display.core.screenshots.screenshot_handler import ScreenShotHandler
from display.webapp.config import Config
from display.webapp.helpers.utils.sources import get_screenshot_sources

logging.setLoggerClass(AppLogger)


class AsyncScreenshots(object):
    """
    The AsyncScreenshots is a class which will take screenshots passing the requests asynchronously to the splash API .
    It is meant for processing a bulk list of dicts and uses the power of async processing to collect the screenshots
    as quick and efficient as possible.

    :param incoming_workload: Dict containing at minimal a key with a value and a list with urls which shall be used to
                              take the screenshots
    :type incoming_workload: dict
    :param user_agent: The user agent to use when retrieving the data
    :type user_agent: str
    """

    def __init__(self, incoming_workload=None):

        self.config = Config()

        self.logger = logging.getLogger(__name__)

        self.screen_shot_sources = get_screenshot_sources()

        self.tab_to_screenshotsource_mapping = defaultdict()
        self.set_tab_to_screenshotsource_mapping()

        self.map_screenshot_sources = {
            "default": "workload",
            "selenium": "selenium_workload",
        }

        if incoming_workload is None:
            incoming_workload = {}

        for k, v in self.map_screenshot_sources.items():
            setattr(self, v, [])

        if isinstance(incoming_workload, dict):
            for key, urls in incoming_workload.items():
                if key in self.tab_to_screenshotsource_mapping:
                    if isinstance(urls, list):
                        getattr(
                            self,
                            self.map_screenshot_sources[
                                self.tab_to_screenshotsource_mapping[key]
                            ],
                        ).append({key: urls})
                    else:
                        raise TypeError(f"Expecting list; got: {type(urls)}")
                else:
                    if isinstance(urls, list):
                        getattr(self, self.map_screenshot_sources["default"]).extend(
                            urls
                        )
                    else:
                        raise TypeError(f"Expecting list; got: {type(urls)}")
        else:
            raise TypeError(f"Expecting dict; got: {type(incoming_workload)}")

        self.user_agent = self.config.USER_AGENT

        self.headers = self.__default_headers

        self.splash_api = SplashApi(
            (self.config.SPLASH_HOST, self.config.SPLASH_PORT),
            protocol="http",
            user_agent=self.config.USER_AGENT,
        )

        self.screenshotHandler = ScreenShotHandler()

        self.current_wd = os.path.dirname(os.path.abspath(__file__))

    @property
    def __default_headers(self):
        """
        Property to return the default headers

        :return: Default headers
        :rtype: dict
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"{self.user_agent}",
        }

    def set_tab_to_screenshotsource_mapping(self):

        for key, value in self.screen_shot_sources.items():
            for item in value:
                self.tab_to_screenshotsource_mapping[item] = key

        self.tab_to_screenshotsource_mapping = dict(
            self.tab_to_screenshotsource_mapping
        )

    def process_async(self, results: list = None, evidence_shot: bool = False):
        """
        Method for processing the workload of sites to be screenshotted into files for displaying in the display gui
        """

        if results is None:
            results = []

            if hasattr(self, "workload"):
                if len(self.workload) != 0:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results.extend(loop.run_until_complete(self.fetch_all(loop)))

        self.logger.info(f"Processing screenshot results: {len(results)}")

        for each in results:
            try:
                if isinstance(each, dict):
                    for k, v in each.items():
                        self.logger.info(f"Processing: {k}")

                        if not os.path.exists(self.config.SCREENSHOT_LOCATION):
                            self.logger.info(
                                f"Creating {self.config.SCREENSHOT_LOCATION}"
                            )
                            os.mkdir(self.config.SCREENSHOT_LOCATION)

                        if not os.path.exists(self.config.TIMELINE_LOCATION):
                            self.logger.info(
                                f"Creating {self.config.TIMELINE_LOCATION}"
                            )
                            os.mkdir(self.config.TIMELINE_LOCATION)

                        if not os.path.exists(
                            os.path.join(self.config.SCREENSHOT_LOCATION, f"{k}.png")
                        ):
                            self.logger.info(
                                f"Creating {os.path.join(self.config.SCREENSHOT_LOCATION, f'{k}.png')}"
                            )
                            Path(
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}.png"
                                )
                            ).touch()

                        if isinstance(v, bytes):
                            if v[:4] == b"\x89PNG":
                                # picture taken; process
                                self.store_normal_picture(k, v)
                                DbLog.insert(
                                    {
                                        "url": self.screenshotHandler.get_url_by_hash(
                                            k
                                        ),
                                        "hash": k,
                                        "action": tracelog_action.SCREENSHOT,
                                        "result": tracelog_result.OK,
                                        "status_code": 200,
                                    }
                                )
                            else:
                                # no picture assume uncatched error for now!
                                self.store_error_picture(k)

                                the_result = json.loads(v)

                                if "error" in the_result:
                                    DbLog.insert(
                                        {
                                            "url": self.screenshotHandler.get_url_by_hash(
                                                k
                                            ),
                                            "hash": k,
                                            "action": tracelog_action.SCREENSHOT,
                                            "result": tracelog_result.NOK,
                                            "status_code": the_result["error"],
                                            "reason": the_result["description"],
                                        }
                                    )
                        elif isinstance(v, str):
                            if v == "ERROR":
                                # set to error pic
                                self.store_error_picture(k)
                        elif isinstance(v, dict):
                            # dict with normal and evidence keys
                            if not evidence_shot:
                                self.store_normal_picture(k, v["normal"])
                                DbLog.insert(
                                    {
                                        "url": self.screenshotHandler.get_url_by_hash(
                                            k
                                        ),
                                        "hash": k,
                                        "action": tracelog_action.SCREENSHOT,
                                        "result": tracelog_result.OK,
                                        "status_code": 200,
                                    }
                                )

                            self.store_evidence_picture(k, v["evidence"])
                            DbLog.insert(
                                {
                                    "url": self.screenshotHandler.get_url_by_hash(k),
                                    "hash": k,
                                    "action": tracelog_action.EVIDENCE,
                                    "result": tracelog_result.OK,
                                    "status_code": 200,
                                }
                            )

                        else:
                            # assume it's an error for now
                            self.store_error_picture(k)
                            DbLog.insert(
                                {
                                    "url": self.screenshotHandler.get_url_by_hash(k),
                                    "hash": k,
                                    "action": tracelog_action.SCREENSHOT,
                                    "result": tracelog_result.NOK,
                                    "status_code": "?",
                                }
                            )

            except Exception as err:
                self.logger.error(f"Error processing {k}, Error produced --> {err}")
                continue

    def store_normal_picture(self, hash, value):

        # First create a copy of the current file and rename to _old
        shutil.copy2(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}.png"),
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}_old.png"),
        )

        self.logger.info(f"Setting screenshot picture for {hash}")
        with open(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}.png"),
            "wb",
        ) as f:
            f.write(value)

        self.minify_current_screenshot(hash=hash)

    def store_evidence_picture(self, hash, value):

        self.logger.info(f"Setting evidence picture for {hash}")
        with open(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}_eve.png"),
            "wb",
        ) as f:
            f.write(value)

    def store_error_picture(self, hash):

        # First create a copy of the current file and rename to _old
        shutil.copy2(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}.png"),
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}_old.png"),
        )

        # retrieve bin data
        with open(
            os.path.join(self.current_wd, "../../webapp/static/img/noScreenShot.png"),
            "rb",
        ) as f:
            data = f.read()

        self.logger.debug(f"Setting error picture for {hash}")
        with open(
            os.path.join(self.config.SCREENSHOT_LOCATION, f"{hash}.png"),
            "wb",
        ) as f:
            f.write(data)

        self.minify_current_screenshot(hash=hash)

    def minify_current_screenshot(self, hash):
        self.screenshotHandler.limit_img_size(hash)

    async def fetch(self, session, entry):
        url_hash = self.screenshotHandler.get_hash(entry["url"].encode("utf-8"))
        try:
            async with session.get(
                self.splash_api.get_render_url(
                    entry["url"], entry["wait"], entry["timeout"]
                )
            ) as response:
                data = await response.content.read()
                return {url_hash: data}
        except Exception as err:
            self.logger.warning(
                f"Error getting {entry['url']} data.... Error observed: {err}"
            )
            DbLog.insert(
                {
                    "url": entry["url"],
                    "hash": url_hash,
                    "action": tracelog_action.SCREENSHOT,
                    "result": tracelog_result.UNK,
                    "reason": err,
                }
            )
            return {url_hash: "ERROR"}

    async def fetch_all(self, loop):
        sem = asyncio.Semaphore(100)
        async with sem:
            async with aiohttp.ClientSession(
                loop=loop,
                headers=self.headers,
                connector=aiohttp.TCPConnector(verify_ssl=False),
                timeout=aiohttp.ClientTimeout(
                    total=30.0, sock_connect=30.0, sock_read=30.0, connect=30.0
                ),
            ) as session:
                results = await asyncio.gather(
                    *[self.fetch(session, entry) for entry in self.workload],
                    return_exceptions=True,
                )
                return results

    def __repr__(self):
        return "<< AsyncScreenshots >>"
