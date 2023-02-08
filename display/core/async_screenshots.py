"""
async_header_collector.py
=========================
"""
import asyncio
import base64
import hashlib
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import aiohttp
from selenium import webdriver
from selenium.common import TimeoutException

from display.external_apis.splash.splash_api import SplashApi
from display.helpers.logger_class import HelperLogger
from display.webapp.config import Config
from display.webapp.helpers.utils.sources import get_screenshot_sources

logging.setLoggerClass(HelperLogger)


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

    def __init__(self, incoming_workload):

        self.config = Config()

        self.logger = logging.getLogger(__name__)

        self.screen_shot_sources = get_screenshot_sources()

        self.map_screenshot_sources = {
            "default": "workload",
            "selenium": "selenium_workload",
        }

        for k, v in self.map_screenshot_sources.items():
            setattr(self, v, [])

        if isinstance(incoming_workload, dict):
            for key, urls in incoming_workload.items():
                if isinstance(urls, list):
                    self.workload.extend(urls)
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

    def process_async(self):
        """
        Method for processing the workload of sites to be screenshotted into files for displaying in the display gui
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.fetch_all(loop))

        self.logger.info(f"Processing splash results: {len(results)}")

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

                        if v[:4] == b"\x89PNG":
                            # picture taken; process

                            # First create a copy of the current file and rename to _old
                            shutil.copyfile(
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}.png"
                                ),
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}_old.png"
                                ),
                            )

                            self.logger.info(f"Setting screenshot picture for {k}")
                            with open(
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}.png"
                                ),
                                "wb",
                            ) as f:
                                f.write(v)

                        else:
                            # set to error pic

                            # First create a copy of the current file and rename to _old
                            shutil.copyfile(
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}.png"
                                ),
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}_old.png"
                                ),
                            )

                            # retrieve bin data
                            with open(
                                os.path.join(
                                    self.current_wd, "../webapp/static/img/error.png"
                                ),
                                "rb",
                            ) as f:
                                data = f.read()

                            self.logger.warning(f"Setting error picture for {k}")
                            with open(
                                os.path.join(
                                    self.config.SCREENSHOT_LOCATION, f"{k}.png"
                                ),
                                "wb",
                            ) as f:
                                f.write(data)
            except Exception as err:
                self.logger.error(f"Error processing {each}, Error produced --> {err}")
                continue

    async def fetch(self, session, entry):
        url_hash = hashlib.md5(entry["url"].encode("utf-8")).hexdigest()[:6]
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

    def get_threaded_screenshots(self, links):
        self.logger.info(f"Starting fetching url's on {len(links)} items")

        with ThreadPoolExecutor() as executor:

            results = list(executor.map(self.selenium_screenshot, links))

        return results

    def selenium_screenshot(self, entry):
        url_hash = hashlib.md5(entry["url"].encode("utf-8")).hexdigest()[:6]
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        options.add_argument("--start-maximized")

        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(entry["timeout"])
        driver.implicitly_wait(entry["wait"])
        try:
            driver.get(entry["url"])
            driver.execute_script("scroll(0, -500);")
            driver.set_window_size(1024, 1024)

            data = driver.get_screenshot_as_base64()
            data = {url_hash: base64.b64decode(data.encode("utf-8"))}
        except TimeoutException:
            data = {url_hash: "ERROR"}
        except Exception as err:
            self.logger.warning(
                f"Error getting {entry['url']} data.... Error observed: {err}"
            )
            data = {url_hash: "ERROR"}
        driver.quit()
        return data

    def __repr__(self):
        return "<< AsyncScreenshots >>"
