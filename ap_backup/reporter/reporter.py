from logging.config import fileConfig
from logging import getLogger
from os import path

__author__ = 'Alexander Pikovsky'


class Reporter(object):

    def __init__(self, parent_reporter=None, logger_name='root'):
        if not parent_reporter:
            self._init_logger()

        self.logger_name = logger_name
        self.logger = getLogger(logger_name)

    def _init_logger(self):
        """Initializes backup logger."""
        package_dir = path.abspath(path.join(path.dirname(__file__), '..'))
        config_file = path.join(package_dir, "logging.conf")

        print("")
        print("Loading logging configuration file '{0}'...".format(config_file))
        fileConfig(config_file)
        print("Logging configuration file loaded successfully.")

    def reporter(self, logger_name=None):
        return Reporter(self, logger_name=logger_name if logger_name else self.logger_name)

    def debug(self, msg, separator=False):
        if separator:
            self.logger.debug("")
        self.logger.debug(msg)

    def info(self, line, separator=False):
        if separator:
            self.logger.info("")
        self.logger.info(line)

    def error(self, msg, exc_info=False, separator=False):
        if separator:
            self.logger.info("")
        self.logger.error(msg, exc_info=exc_info)

    def critical(self, msg, exc_info=False, separator=False):
        if separator:
            self.logger.info("")
        self.logger.critical(msg, exc_info=exc_info)

