from abc import ABCMeta, abstractmethod
import os
import datetime

from ap_backup.config import CheckObjectRecentFileExists, CheckObjectCompareFileToSrc

from .check_object_processor_manager import check_object_processor_class
from .utils import check_recent_file_exists


class CheckObjectProcessor(object):
    """Base class for check object processors."""
    __metaclass__ = ABCMeta

    def __init__(self, check_object, check_processor):
        self.reporter = check_processor.reporter
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
        return check_recent_file_exists(self.backupCheckObject.backup_folder, self.backupCheckObject.backup_file_name_pattern,
            self.backupCheckObject.scheduleMinutes, self.backupChecker.backup_config, self.backupChecker.logger)


@check_object_processor_class(CheckObjectCompareFileToSrc)
class CheckObjectCompareFileToSrcProcessor(CheckObjectProcessor) :
    """CompareFileToSrc backup check object processor."""
           
    def __init__(self, check_object, check_processor):
        super(CheckObjectRecentFileExistsProcessor, self).__init__(check_object, check_processor)

    def process(self):
        logger = self.backupChecker.logger
        
        #get src and backup file info
        backup_file = self.backupCheckObject.backup_file
        if not os.path.isfile(backup_file):
            raise Exception("Backup file '" + backup_file + "' does not exist!")

        src_file = self.backupCheckObject.src_file
        if (not os.path.isfile(src_file)) :
            raise Exception("Source file '" + src_file + "' does not exist!")

        backupFileTime = datetime.datetime.fromtimestamp(os.path.getmtime(backup_file))
        srcFileTime = datetime.datetime.fromtimestamp(os.path.getmtime(src_file))
        accuracyDelta = datetime.timedelta(days=self.backupChecker.backup_config.checker_accuracy_days)
        
        #determine min time due to schedule
        current_time = datetime.datetime.now()
        maxScheduleDiff = datetime.timedelta(minutes=self.backupCheckObject.scheduleMinutes) + accuracyDelta
        minScheduleTime = current_time - maxScheduleDiff

        #determine min time due to source file
        minSrcTime = srcFileTime
        
        #min time is the weakest of both
        minTime = min(minScheduleTime, minSrcTime)
        
        if (minTime > backupFileTime) :
            logger.error("Backup OUT-OF-DATE: backup file '{0}' is at {1}, but must be at least {2}"
                .format(backup_file, backupFileTime, minTime))
            return False

        return True