import logging.config

from ap_backup.config.backup_config import BackupConfig

from .check_object_processor_manager import check_object_processor_manager
from .utils import check_recent_file_exists

# Import all work object processor classes, this will register them in backup_object_processor_manager
# noinspection PyUnresolvedReferences
from .check_object_processors import \
    CheckObjectProcessor, \
    CheckObjectRecentFileExistsProcessor, \
    CheckObjectCompareFileToSrcProcessor


class CheckProcessor:
    """Processes the given backup configuration (makes backup)."""
       
    logger = logging.getLogger('backup_checker_protocol')

    backup_config = None
    config = None
    
    def __init__(self, app_config, backup_config, reporter):
        self.app_config = app_config
        self.backup_config = backup_config
        self.reporter = reporter.reporter(logger_name='protocol')

    def check(self):
        """Checks the given backup configuration (checks whether all backups are up-to-date).
           Returns True if all up-to-date."""
        
        self.reporter.info("Checking backup '{0}'".format(self.backup_config.name))

        if self.backup_config.backup_type == BackupConfig.BACKUP_TYPE_ARCHIVE:
            return self.check_archive_config()
        elif self.backup_config.backup_type == BackupConfig.BACKUP_TYPE_CHECKER:
            return self.check_checker_config()
        else:
            raise Exception("Unsupported backup type '{0}' in backup '{1}'"
                            .format(self.backup_config.backup_type, self.backup_config.name))
                  
        return True

    def check_archive_config(self):
        for destination in self.backup_config.destination_by_name.values():
            if (not check_recent_file_exists(destination.folder, self.backup_config.name + "*.zip",
                                             destination.scheduleMinutes, self.backup_config, self.reporter)):
                return False

        self.reporter.info("Backup '{0}' checked: {1} destinations up-to-date."
                           .format(self.backup_config.name, len(self.backup_config.destination_by_name)))

    def check_checker_config(self):
        for check_object in self.backup_config.backup_objects:
            object_processor = check_object_processor_manager.create_processor(check_object, self)
            if not object_processor:
                raise Exception("Unsupported check object type '{0}'.".format(type(check_object).__name__))

            #check
            if not object_processor.process():
                return False

        self.reporter.info("Backup '{0}' checked: {1} objects up-to-date."
                           .format(self.backup_config.name, len(self.backup_config.backup_objects)))
