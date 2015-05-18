from datetime import datetime
from os import path
import os
from croniter import croniter
from shutil import rmtree

from .backup_status import BackupStatus


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
        now = datetime.now()

        self._init_data_folder()
        self._load_last_backup_status()

        destinations_to_update = self._prepare_destinations_to_update(now)
        if not destinations_to_update:
            self.reporter.info("Backup '{0}' skipped: all destinations up-to-date.".format(self.backup_config.name))
            return 0

        self.reporter.info("Preparing folders...")
        self._prepare_folders()

        self.logger.info("Processing objects...")
        self._process_objects()

        #create archive       
        self.logger.info("Creating archive '{0}'...".format(self.last_backup_archive_file))
        self._create_archive()

        #process destinations
        self.logger.info("Copying archive to destinations...")
        self._copy_archive_to_destinations(destinations_to_update)

        self.logger.info("Backup '{0}' complete: {1} destinations updated."
                         .format(self.backup_config.name, len(destinations_to_update)))
        return len(destinations_to_update)

    def _init_data_folder(self):
        self.data_folder = self.backup_config.data_folder
        if not os.path.exists(self.data_folder):
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

    def _prepare_destinations_to_update(self, now):

        #enumerate destinations and decide which must be updated
        destinations_to_update = []
        for destination in self.backup_config.destination_by_name.values():
            if self.is_backup_expired_for_destination(destination, now):
                destinations_to_update.append(destination)

        #if no destinations have to be updated we are complete, otherwise update destination statuses
        if destinations_to_update:
            for destination in destinations_to_update:
                destination_status = self.last_backup_status.get_or_create_destination_status(destination.name)
                destination_status.last_backup_attempt_time = now
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
        backupObjectProcessors = []
        for backupObject in self.backup_config.backupObjects :
            if (isinstance(backupObject, apbackup.config.BackupObjectMySql)):
                backupObjectProcessors.append(BackupObjectMySqlProcessor(backupObject, self))
            elif (isinstance(backupObject, apbackup.config.BackupObjectSvn)):
                backupObjectProcessors.append(BackupObjectSvnProcessor(backupObject, self))
            elif (isinstance(backupObject, apbackup.config.BackupObjectFile)):
                backupObjectProcessors.append(BackupObjectFileProcessor(backupObject, self))
            elif (isinstance(backupObject, apbackup.config.BackupObjectFolder)):
                backupObjectProcessors.append(BackupObjectFolderProcessor(backupObject, self))
            else :
                raise Exception("Unsupported backup object.")

        #process backup objects
        for backupObjectProcessor in backupObjectProcessors :
            backupObjectProcessor.doBackup()

    def _create_archive(self):
        apgeneral.ziputils.zipdir(longPathPrefix + self.last_backup_folder, self.last_backup_archive_file, includeDirInZip=False)

    def _copy_archive_to_destinations(self, destinations_to_update):
        for destination in destinations_to_update:
            #create destination dir if does not exist
            if (not os.path.exists(destination.folder)) :
                os.makedirs(destination.folder, exist_ok=True)

            #multi-copy archive
            apbackup.multicopy.multiCopy(self.last_backup_archive_file, destination.folder,
                numCopies=destination.numCopies, targetBaseName=self.backup_config.name,
                minPeriodDays=0, appendTime=True, ignoreErrors=False, logger=self.logger);

            #update destination status
            destination_status = self.last_backup_status.get(destination.name)
            destination_status.last_successful_backup_time = now
            destination_status.last_backup_result = "Successful"

        #save last backup status
        self._save_last_backup_status()
