from datetime import datetime
from os import path
import os
import shutil
from croniter import croniter
from shutil import rmtree

from ap_backup.multicopy import multicopy

from .backup_status import BackupStatus
from .backup_object_processor_manager import backup_object_processor_manager

# Import all work object processor classes, this will register them in backup_object_processor_manager
# noinspection PyUnresolvedReferences
from .backup_object_processors import \
    BackupObjectProcessor, \
    BackupObjectFileProcessor, \
    BackupObjectFolderProcessor, \
    BackupObjectMySqlProcessor, \
    BackupObjectSvnProcessor


class BackupProcessor(object):
    """Processes the given backup configuration (makes backup)."""
    
    def __init__(self, app_config, backup_config, reporter):
        self.app_config = app_config
        self.backup_config = backup_config
        self.reporter = reporter.reporter(logger_name='protocol')

        self.data_folder = None
        self.last_backup_status = None

        #directory in which last backup files are placed and from where they are then archived
        self.last_backup_folder = None

        #last backup archive file
        self.last_backup_archive_file = None

    def process(self):
        """Processes the given backup configuration (makes backup).
           Returns the number of updated destinations (0 if nothing updated)."""
        
        self.reporter.info("Processing backup '{0}'...".format(self.backup_config.name), separator=True)
        backup_time = datetime.now()

        self._init_data_folder()
        self._load_last_backup_status()

        destinations_to_update = self._prepare_destinations_to_update(backup_time)
        if not destinations_to_update:
            self.reporter.info("Backup '{0}' skipped: all destinations up-to-date.".format(self.backup_config.name))
            return 0

        self.reporter.info("Preparing folders...")
        self._prepare_folders()

        self.reporter.info("Processing objects...")
        self._process_objects()

        #create archive       
        self.reporter.info("Creating archive '{0}'...".format(self.last_backup_archive_file))
        self._create_archive()

        #process destinations
        self.reporter.info("Copying archive to destinations...")
        self._copy_archive_to_destinations(destinations_to_update, backup_time)

        self.reporter.info("Backup '{0}' complete: {1} destinations updated."
                           .format(self.backup_config.name, len(destinations_to_update)))
        return len(destinations_to_update)

    def _init_data_folder(self):
        self.data_folder = self.backup_config.data_folder
        if not path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    def _load_last_backup_status(self):
        """Reads last backup status to self.last_backup_status."""
        status_dir = self.data_folder
        self.last_backup_status = BackupStatus(self.backup_config.name, status_dir)

    def _save_last_backup_status(self):
        """Saves last backup status from self.last_backup_status."""
        self.last_backup_status.save()

    def is_backup_expired_for_destination(self, destination, now):
        """Determines whether update is required for the given destination."""
        destination_status = self.last_backup_status.get_or_create_destination_status(destination.name)
        if not destination_status.last_successful_backup_time:
            return True    # no backup done yet
        
        prev_trigger = croniter(destination.schedule, now).get_prev(datetime)
        return prev_trigger > destination_status.last_successful_backup_time

    def _prepare_destinations_to_update(self, backup_time):

        #enumerate destinations and decide which must be updated
        destinations_to_update = []
        for destination in self.backup_config.destination_by_name.values():
            if self.is_backup_expired_for_destination(destination, backup_time):
                destinations_to_update.append(destination)

        #if no destinations have to be updated we are complete, otherwise update destination statuses
        if destinations_to_update:
            for destination in destinations_to_update:
                destination_status = self.last_backup_status.get_or_create_destination_status(destination.name)
                destination_status.last_backup_attempt_time = backup_time
                destination_status.last_backup_result = "not_finished"

            self._save_last_backup_status()

        return destinations_to_update

    def _prepare_folders(self):
        #remove last archive
        self.last_backup_archive_file = os.path.join(self.data_folder, "last_backup.zip")
        if path.exists(self.last_backup_archive_file):
            os.remove(self.last_backup_archive_file)

        #remove prev_backup folder, we do this by first renaming it
        #(workaround for the following code to always be able to rename to prevBackupDir)
        prev_backup_folder = os.path.join(self.data_folder, "prev_backup")
        if path.exists(prev_backup_folder):
            rmtree(prev_backup_folder)

        #rename last_backup folder to prev_backup
        self.last_backup_folder = os.path.join(self.data_folder, "last_backup")
        if path.exists(self.last_backup_folder):
            os.rename(self.last_backup_folder, prev_backup_folder)

        #create last_backup folder
        os.mkdir(self.last_backup_folder)

    def _process_objects(self):

        #create backup object processors
        for backup_object in self.backup_config.backup_objects:
            object_processor = backup_object_processor_manager.create_processor(backup_object, self)
            if not object_processor:
                raise Exception("Unsupported backup object type '{0}'.".format(type(backup_object).__name__))

            object_processor.process()

    def _create_archive(self):
        archive_base_name, archive_ext = os.path.splitext(self.last_backup_archive_file)
        archive_format = archive_ext[1:]
        shutil.make_archive(archive_base_name, archive_format, self.last_backup_folder)

    def _copy_archive_to_destinations(self, destinations_to_update, backup_time):
        for destination in destinations_to_update:
            #create destination dir if does not exist
            if not path.exists(destination.folder):
                os.makedirs(destination.folder)

            #multi-copy archive
            multicopy(self.last_backup_archive_file, destination.folder,
                      num_copies=destination.num_copies, target_base_name=self.backup_config.name,
                      min_period_days=0, append_time=True, ignore_errors=False, reporter=self.reporter)

            #update destination status
            destination_status = self.last_backup_status.get_or_create_destination_status(destination.name)
            destination_status.last_successful_backup_time = backup_time
            destination_status.last_backup_result = "succeded"

        #save last backup status
        self._save_last_backup_status()
