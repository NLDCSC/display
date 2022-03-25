"""
app_logger.py
=============
"""
import logging
import os
from logging.handlers import RotatingFileHandler, SysLogHandler

from display.helpers.logger_class import HelperLogger, HostnameFilter


class AppLogger(HelperLogger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s"
        )

        if not os.path.exists(self.config.LOG_FILE_PATH):
            os.makedirs(self.config.LOG_FILE_PATH)

        crf = RotatingFileHandler(
            filename=os.path.join(self.config.LOG_FILE_PATH, self.config.LOG_FILE_NAME),
            maxBytes=100000000,
            backupCount=5,
        )
        crf.setLevel(logging.DEBUG)
        crf.setFormatter(formatter)
        self.addHandler(crf)

        formatter = logging.Formatter(
            "%(asctime)s [%(hostname)s] - %(name)-8s - %(levelname)-8s - %(message)s"
        )

        if self.config.SYSLOG_ENABLE:
            syslog = SysLogHandler(
                address=(self.config.SYSLOG_SERVER, int(self.config.SYSLOG_PORT)),
                facility=SysLogHandler.LOG_LOCAL0,
            )

            syslog.setLevel(logging.DEBUG)
            syslog.addFilter(HostnameFilter())
            syslog.setFormatter(formatter)
            self.addHandler(syslog)
