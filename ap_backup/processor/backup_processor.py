import os
import datetime
import logging.config

from .backup_status import BackupStatus


class BackupProcessor(object):
    """Processes the given backup configuration (makes backup)."""
    
    logger = logging.getLogger('protocol')

    def __init__(self, config, backup_config, reporter):
        self.config = config
        self.backup_config = backup_config
        self.reporter = reporter

        self.last_backup_status = None

        #directory in which last backup files are placed and from where they are then archived
        self.last_backup_dir = None

        #last backup archive file
        self.last_backup_archive_file = None

    def process(self):
        """Processes the given backup configuration (makes backup).
           Returns the number of updated destinations (0 if nothing updated)."""
        
        self.logger.info("Processing backup '{0}'...".format(self.backup_config.name), separator=True)
        current_time = datetime.datetime.now()

        return 1

        #read last backup status
        self.loadLastBackupStatus()

        #enumerate destinations and decide which must be updated
        destinationsToUpdate = []
        for destination in self.backup_config.destinations :
            destination_status = self.last_backup_status.get(destination.name)
            if (self.isBackupRequiredForDestination(destination, destination_status, current_time)) :
                destinationsToUpdate.append(destination)
        
        #if no destinations have to be updated we are complete
        if (len(destinationsToUpdate) == 0) :
            self.logger.info("Backup '{0}' skipped: all destinations up-to-date.".format(self.backup_config.name))
            return 0

        ##update destination statuses
        for destination in destinationsToUpdate :
            destination_status = self.last_backup_status.get(destination.name)
            destination_status.last_backup_attempt_time = current_time
            destination_status.last_backup_result = "NotFinished"
            
        self.saveLastBackupStatus()

        self.logger.info("Preparing folders...")
        
        #ensure backup dir exists
        backupDir = os.path.join(self.config.configDir, backupsSubdir, self.backup_config.name)
        os.makedirs(backupDir, exist_ok=True)
 
        #remove last archive
        self.last_backup_archive_file = os.path.join(backupDir, "LastBackup.zip")
        if (os.path.exists(self.last_backup_archive_file)) :
            os.remove(self.last_backup_archive_file)

        #remove PrevBackup folder, we do this by first renaming it 
        #(workaround for the following code to always be able to rename to prevBackupDir)
        prevBackupDir = os.path.join(backupDir, "PrevBackup")
        if (os.path.exists(prevBackupDir)) :
            tempDir = os.path.join(backupDir, "Temp")
            if (os.path.exists(tempDir)) :
                apgeneral.os.rmtreeWithReadonly(longPathPrefix + tempDir)
            os.rename(prevBackupDir, tempDir)
            apgeneral.os.rmtreeWithReadonly(longPathPrefix + tempDir)
            
        #rename LastBackup folder to PrevBackup
        self.last_backup_dir = os.path.join(backupDir, "LastBackup")
        if (os.path.exists(self.last_backup_dir)) :
            os.rename(self.last_backup_dir, prevBackupDir)

        #create LastBackup folder
        os.mkdir(self.last_backup_dir)

        self.logger.info("Copying files...")

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

        #create archive       
        self.logger.info("Creating archive '{0}'...".format(self.last_backup_archive_file))
        apgeneral.ziputils.zipdir(longPathPrefix + self.last_backup_dir, self.last_backup_archive_file, includeDirInZip=False)
            
        #process destinations
        self.logger.info("Copying archive to destinations...")
        
        for destination in destinationsToUpdate :
            #create destination dir if does not exist
            if (not os.path.exists(destination.folder)) :
                os.makedirs(destination.folder, exist_ok=True)
            
            #multi-copy archive
            apbackup.multicopy.multiCopy(self.last_backup_archive_file, destination.folder,
                numCopies=destination.numCopies, targetBaseName=self.backup_config.name,
                minPeriodDays=0, appendTime=True, ignoreErrors=False, logger=self.logger);

            #update destination status
            destination_status = self.last_backup_status.get(destination.name)
            destination_status.last_successful_backup_time = current_time
            destination_status.last_backup_result = "Successful"

        #save last backup status
        self.saveLastBackupStatus()
    
        self.logger.info("Backup '{0}' complete: {1} destinations updated.".
               format(self.backup_config.name, len(destinationsToUpdate)))
        return len(destinationsToUpdate)
    
    def loadLastBackupStatus(self) :
        """Reads last backup status to self.last_backup_status."""
        
        #ensure statuses dir exists
        status_dir = os.path.join(self.config.configDir, statusesSubdir)
        os.makedirs(status_dir, exist_ok=True)

        #read last backup status file file
        self.last_backup_status = BackupStatus(self.backup_config.name, status_dir)

    def saveLastBackupStatus(self) :
        """Saves last backup status from self.last_backup_status."""
        self.last_backup_status.save()

    def isBackupRequiredForDestination(self, destination, destination_status, current_time) :
        """Determines whether update is required for the given destination."""
        if (not destination_status.last_successful_backup_time) :
            return True    #no backup done yet
        
        timeDiff = current_time - destination_status.last_successful_backup_time
        return (timeDiff > datetime.timedelta(minutes=destination.scheduleMinutes))
