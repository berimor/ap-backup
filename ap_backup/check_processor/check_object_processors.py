from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
import os
from croniter import croniter

from ap_backup.config import CheckObjectRecentFileExists, CheckObjectCompareFileToSrc

from .check_object_processor_manager import check_object_processor_class
from .utils import check_recent_file_exists


class CheckObjectProcessor(object):
    """Base class for check object processors."""
    __metaclass__ = ABCMeta

    def __init__(self, check_object, check_processor):
        self.reporter = check_processor.reporter
        self.backup_config = check_processor.backup_config
        self.check_object = check_object   # corresponding check object
        self.check_processor = check_processor   # parent processor

    @abstractmethod
    def process(self):
        raise Exception("This method must be overridden.")       


@check_object_processor_class(CheckObjectRecentFileExists)
class CheckObjectRecentFileExistsProcessor(CheckObjectProcessor) :
    """RecentFileExists backup check object processor."""
           
    def __init__(self, check_object, check_processor):
        super(CheckObjectRecentFileExistsProcessor, self).__init__(check_object, check_processor)

    def process(self):
        return check_recent_file_exists(self.check_object.backup_folder,
                                        self.check_object.backup_file_name_pattern,
                                        self.check_object.schedule,
                                        self.backup_config.checker_accuracy_days,
                                        self.reporter)


@check_object_processor_class(CheckObjectCompareFileToSrc)
class CheckObjectCompareFileToSrcProcessor(CheckObjectProcessor):
    """CompareFileToSrc backup check object processor."""
           
    def __init__(self, check_object, check_processor):
        super(CheckObjectCompareFileToSrcProcessor, self).__init__(check_object, check_processor)

    def process(self):
        #get src and backup file info
        backup_file = self.check_object.backup_file
        if not os.path.isfile(backup_file):
            self.reporter.error("Backup file '{0}' does not exist.".format(backup_file))
            return False

        src_file = self.check_object.src_file
        if not os.path.isfile(src_file):
            self.reporter.error("Source file '{0}' does not exist.".format(src_file))
            return False

        src_file_time = datetime.fromtimestamp(os.path.getmtime(src_file))
        backup_file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))

        #determine min time due to schedule
        current_time = datetime.now()
        prev_trigger = croniter(self.check_object.schedule, current_time).get_prev(datetime)
        accuracy_delta = timedelta(days=self.backup_config.checker_accuracy_days)
        min_schedule_time = prev_trigger - accuracy_delta

        #determine min time due to source file
        min_src_time = src_file_time

        #min time is the weakest of both
        min_time = min(min_schedule_time, min_src_time)
        if min_time > backup_file_time:
            self.reporter.error("Backup OUT-OF-DATE: backup file '{0}' is at {1}, but must be at least {2}"
                                .format(backup_file, backup_file_time, min_time))
            return False

        return True