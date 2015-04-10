from logging.config import fileConfig
from logging import getLogger
from os import path

__author__ = 'Alexander Pikovsky'


class Reporter(object):

    def __init__(self):
        self._init_logger()

    def _init_logger(self):
        """Initializes backup logger."""
        package_dir = path.abspath(path.join(path.dirname(__file__), '..'))
        config_file = path.join(package_dir, "logging.conf")

        print("")
        print("Loading logging configuration file '{0}'...".format(config_file))
        fileConfig(config_file)
        print("Logging configuration file loaded successfully.")

        self.summary_logger = getLogger('summary')

    def debug(self, msg, separator=False):
        if separator:
            self.summary_logger.debug("")
        self.summary_logger.debug(msg)

    def info(self, line, separator=False):
        if separator:
            self.summary_logger.info("")
        self.summary_logger.info(line)

    def error(self, msg, exc_info=False, separator=False):
        if separator:
            self.summary_logger.info("")
        self.summary_logger.error(msg, exc_info=exc_info)

    def critical(self, msg, exc_info=False, separator=False):
        if separator:
            self.summary_logger.info("")
        self.summary_logger.critical(msg, exc_info=exc_info)

