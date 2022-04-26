"""
logger_class.py
================
"""
import logging
import platform
from logging.config import dictConfig

import colors

from display.webapp.config import Config


class HostnameFilter(logging.Filter):
    hostname = platform.node()

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True


class HelperLogger(logging.Logger):
    """
    The HelperLogger is used by the application / gui as their logging class and *extends* the default python
    logger.logging class.
    """

    config = Config()

    logDict = {
        "version": 1,
        "formatters": {
            "sysLogFormatter": {
                "format": "%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s"
            },
            "simpleFormatter": {
                "format": "%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s"
            },
        },
        "handlers": {
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "simpleFormatter",
            }
        },
        "root": {"level": config.LOG_LEVEL, "handlers": ["consoleHandler"]},
    }

    dictConfig(logDict)

    level_map = {
        "debug": "magenta",
        "info": "white",
        "warning": "yellow",
        "error": "red",
        "critical": "red",
    }

    def __init__(self, name, level=logging.NOTSET):

        super().__init__(name, level)

    def debug(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘DEBUG’ and color *MAGENTA.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.debug(“Houston, we have a %s”, “thorny problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=HelperLogger.level_map["debug"])

        return super(HelperLogger, self).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘INFO’ and color *WHITE*.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.info(“Houston, we have a %s”, “interesting problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=HelperLogger.level_map["info"])

        return super(HelperLogger, self).info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘WARNING’ and color *YELLOW*.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.warning(“Houston, we have a %s”, “bit of a problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=HelperLogger.level_map["warning"])

        return super(HelperLogger, self).warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘ERROR’ and color *RED*.

        Store logged message to the database for dashboard alerting.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.error(“Houston, we have a %s”, “major problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=HelperLogger.level_map["error"])

        return super(HelperLogger, self).error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log ‘msg % args’ with severity ‘CRITICAL’ and color *RED*.

        Store logged message to the database for dashboard alerting.

        To pass exception information, use the keyword argument exc_info with a true value, e.g.

        logger.critical(“Houston, we have a %s”, “hell of a problem”, exc_info=1)

        :param msg: Message to log
        :type msg: str
        """

        msg = colors.color("{}".format(msg), fg=HelperLogger.level_map["critical"])

        return super(HelperLogger, self).critical(msg, *args, **kwargs)
