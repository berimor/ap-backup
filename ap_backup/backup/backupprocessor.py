'''
Created on 14.06.2012

@author: Alexander Pikovsky
'''
import os
import datetime
import shutil
import subprocess
import logging.config
import sys

import apgeneral.os
import apgeneral.ziputils
import aploggers.loggers
import apbackup.backupstatus
import apbackup.multicopy
import apbackup.config

statusesSubdir = "backup-statuses"
backupsSubdir = "backups"

#This prefix must be added to file paths to allow more than 255 characters in the path
longPathPrefix = "\\\\?\\"

def initLogger() :
    """Initializes backup logger.
       
       Returns the [logger, LOG]."""
    
    packageDir = os.path.dirname(os.path.realpath(__file__))

    logging.config.fileConfig(os.path.join(packageDir, "logging.conf"))
    LOG = aploggers.loggers.LogMessages(packageDir)
    logger = logging.getLogger('summary')
    return [logger, LOG]
    
def runBackup(backupDir) : 
    """Main backup method.
       
       backupDir : directory containing the backup configuration and backups.
    """
    
    [logger, LOG] = initLogger()
    
    #execute main program
    try:
        #read config file
        config = apbackup.config.Config(backupDir)
    
        #complete
        logger.info(LOG.Msg("BackupStarted", backupDir))
    
        #connect network shares
        for rns in config.requiredNetworkShares :
            apgeneral.os.connectNetworkShare(rns.driveName, rns.uncPath)
        
        #process backup configs, don't abort if some of them fail
        updatedConfigs = 0
        upToDateConfigs = 0
        failedConfigs = 0
        for backupConfig in config.backupConfigs :
            try :
                backupProcessor = apbackup.backupprocessor.BackupProcessor(backupConfig, config)
                updatedDestinations = backupProcessor.process()
                if (updatedDestinations > 0) :
                    updatedConfigs += 1 
                else :
                    upToDateConfigs += 1
            
            except Exception as ex:
                logger.critical(LOG.Msg("BackupException", backupConfig.name, str(ex)), exc_info=True)
                failedConfigs += 1
    
        #complete
        if (failedConfigs == 0) :
            logger.info(LOG.Msg("BackupComplete", backupDir, updatedConfigs, upToDateConfigs))
        else :
            logger.error(LOG.Msg("BackupCompleteWithFailures", backupDir, failedConfigs, updatedConfigs, upToDateConfigs))
    
    except Exception as ex:
        logger.critical(LOG.Msg("UnexpectedException", str(ex)), exc_info=True)
        sys.exit(1)
        
    finally:
        #disconnect network shares
        for rns in config.requiredNetworkShares :
            apgeneral.os.disconnectNetworkShare(rns.driveName)



class BackupProcessor :
    """Processes the given backup configuration (makes backup)."""
    
    logger = logging.getLogger('protocol')
    
    backupConfig = None
    config = None
    lastBackupStatus = None

    #directory in which last backup files are placed and from where they are then archived
    lastBackupDir = None
    
    #last backup archive file
    lastBackupArchiveFile = None
    
    def __init__(self, backupConfig, config):
        self.config = config
        self.backupConfig = backupConfig
        
        
    def process(self) :
        """Processes the given backup configuration (makes backup).
           Returns the number of updated destinations (0 if nothing updated)."""
        
        self.logger.info("Processing backup '{0}'...".format(self.backupConfig.name))
        currentTime = datetime.datetime.now()

        #read last backup status
        self.loadLastBackupStatus()

        #enumerate destinations and decide which must be updated
        destinationsToUpdate = []
        for destination in self.backupConfig.destinations :
            destinationStatus = self.lastBackupStatus.get(destination.name)
            if (self.isBackupRequiredForDestination(destination, destinationStatus, currentTime)) :            
                destinationsToUpdate.append(destination)
        
        #if no destinations have to be updated we are complete
        if (len(destinationsToUpdate) == 0) :
            self.logger.info("Backup '{0}' skipped: all destinations up-to-date.".format(self.backupConfig.name))
            return 0

        ##update destination statuses
        for destination in destinationsToUpdate :
            destinationStatus = self.lastBackupStatus.get(destination.name)
            destinationStatus.lastBackupAttemptTime = currentTime
            destinationStatus.lastBackupResult = "NotFinished"
            
        self.saveLastBackupStatus()

        self.logger.info("Preparing folders...")
        
        #ensure backup dir exists
        backupDir = os.path.join(self.config.configDir, backupsSubdir, self.backupConfig.name)
        os.makedirs(backupDir, exist_ok=True)
 
        #remove last archive
        self.lastBackupArchiveFile = os.path.join(backupDir, "LastBackup.zip")
        if (os.path.exists(self.lastBackupArchiveFile)) :
            os.remove(self.lastBackupArchiveFile)

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
        self.lastBackupDir = os.path.join(backupDir, "LastBackup")
        if (os.path.exists(self.lastBackupDir)) :
            os.rename(self.lastBackupDir, prevBackupDir)

        #create LastBackup folder
        os.mkdir(self.lastBackupDir)

        self.logger.info("Copying files...")

        #create backup object processors
        backupObjectProcessors = []
        for backupObject in self.backupConfig.backupObjects :
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
        self.logger.info("Creating archive '{0}'...".format(self.lastBackupArchiveFile))
        apgeneral.ziputils.zipdir(longPathPrefix + self.lastBackupDir, self.lastBackupArchiveFile, includeDirInZip=False)
            
        #process destinations
        self.logger.info("Copying archive to destinations...")
        
        for destination in destinationsToUpdate :
            #create destination dir if does not exist
            if (not os.path.exists(destination.folder)) :
                os.makedirs(destination.folder, exist_ok=True)
            
            #multi-copy archive
            apbackup.multicopy.multiCopy(self.lastBackupArchiveFile, destination.folder,
                numCopies=destination.numCopies, targetBaseName=self.backupConfig.name,
                minPeriodDays=0, appendTime=True, ignoreErrors=False, logger=self.logger);

            #update destination status
            destinationStatus = self.lastBackupStatus.get(destination.name)
            destinationStatus.lastSuccessfulBackupTime = currentTime
            destinationStatus.lastBackupResult = "Successful"

        #save last backup status
        self.saveLastBackupStatus()
    
        self.logger.info("Backup '{0}' complete: {1} destinations updated.".
               format(self.backupConfig.name, len(destinationsToUpdate)))
        return len(destinationsToUpdate)
    
    def loadLastBackupStatus(self) :
        """Reads last backup status to self.lastBackupStatus."""
        
        #ensure statuses dir exists
        statusDir = os.path.join(self.config.configDir, statusesSubdir)
        os.makedirs(statusDir, exist_ok=True)

        #read last backup status file file
        self.lastBackupStatus = apbackup.backupstatus.BackupStatus(self.backupConfig.name, statusDir)

    def saveLastBackupStatus(self) :
        """Saves last backup status from self.lastBackupStatus."""
        self.lastBackupStatus.save()

    def isBackupRequiredForDestination(self, destination, destinationStatus, currentTime) :
        """Determines whether update is required for the given destination."""
        if (not destinationStatus.lastSuccessfulBackupTime) :
            return True    #no backup done yet
        
        timeDiff = currentTime - destinationStatus.lastSuccessfulBackupTime
        return (timeDiff > datetime.timedelta(minutes=destination.scheduleMinutes))
    

class BackupObjectProcessor :
    """Base class for backup object processors."""

    logger = None
    
    backupObject = None # corresponding backup object
    backupProcessor = None # parent processor
    
    def __init__(self, backupCheckObject, backupChecker):       
        self.logger = backupChecker.logger
        self.backupObject = backupCheckObject    
        self.backupProcessor = backupChecker    

    def doBackup(self):
        raise Exception("This method must be overridden.")       



class BackupObjectMySqlProcessor(BackupObjectProcessor) :
    """MySql backup object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super(BackupObjectMySqlProcessor, self).__init__(backupCheckObject, backupChecker)
        

    def doBackup(self):
        targetFolder = os.path.join(self.backupProcessor.lastBackupDir, self.backupObject.targetSubfolder)
        os.makedirs(targetFolder, exist_ok=True)
        
        targetFilePath = os.path.join(targetFolder, self.backupObject.target_file_name)
        args = ["mysqldump", "--lock-tables"]
        args += ["--opt", "--skip-extended-insert"] #disable extended (bulk) inserts
        args += ["--user={0}".format(self.backupObject.user)]
        args += ["--password={0}".format(self.backupObject.password)]
        if (self.backupObject.port) :
            args.append("--port={0}".format(self.backupObject.port))
            
        args.append("{0}".format(self.backupObject.database))

        try :
            self.logger.info("Backing up MySql database '{0}'...".format(self.backupObject.database))
            with open(targetFilePath, "w") as targetFile:
                subprocess.check_call(args, stdout=targetFile)
            self.logger.info("Database backup complete.")
            
        except subprocess.CalledProcessError as ex :
            raise Exception("MySQL backup for database '{0}' failed with exit code {1}.".format(
                self.backupObject.database, ex.returncode))



class BackupObjectSvnProcessor(BackupObjectProcessor) :
    """Subversion repository backup object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super(BackupObjectSvnProcessor, self).__init__(backupCheckObject, backupChecker)

    def doBackup(self):
        targetFolder = os.path.join(self.backupProcessor.lastBackupDir, self.backupObject.targetSubfolder)
        os.makedirs(targetFolder, exist_ok=True)
        
        args = ["svnadmin", "hotcopy",
                "{0}".format(self.backupObject.repository_folder),
                "{0}".format(targetFolder)]

        try :
            self.logger.info("Backing up Subversion repository '{0}'...".format(self.backupObject.repository_folder))
            subprocess.check_call(args)
            self.logger.info("Subversion repository backup complete.")
            
        except subprocess.CalledProcessError as ex :
            raise Exception("Subversion backup for repository folder '{0}' failed with exit code {1}.".format(
                self.backupObject.repository_folder, ex.returncode))



class BackupObjectFileProcessor(BackupObjectProcessor) :
    """File backup object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super(BackupObjectFileProcessor, self).__init__(backupCheckObject, backupChecker)

    def doBackup(self):
        targetFolder = os.path.join(self.backupProcessor.lastBackupDir, self.backupObject.targetSubfolder)
        os.makedirs(longPathPrefix + targetFolder, exist_ok=True)

        src_file = self.backupObject.src_file_path
        if (not os.path.isfile(longPathPrefix + src_file)) :
            raise Exception("Source file '" + src_file + "' does not exist!")

        target_file_name = self.backupObject.target_file_name
        if (not target_file_name) :
            target_file_name = os.path.basename(src_file)
               
        self.logger.info("Copying file '{0}' to '{1}'...".format(src_file, target_file_name))
        newFile = os.path.join(targetFolder, target_file_name)
        shutil.copyfile(longPathPrefix + src_file, longPathPrefix + newFile)
        self.logger.info("Done")
        


class BackupObjectFolderProcessor(BackupObjectProcessor) :
    """Folder backup object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super(BackupObjectFolderProcessor, self).__init__(backupCheckObject, backupChecker)

    def doBackup(self):
        targetFolder = os.path.join(self.backupProcessor.lastBackupDir, self.backupObject.targetSubfolder)

        srcFolder = self.backupObject.src_folder_path
        if (not os.path.isdir(longPathPrefix + srcFolder)) :
            raise Exception("Source folder '" + srcFolder + "' does not exist!")
              
        self.logger.info("Copying folder '{0}'...".format(srcFolder))
        shutil.copytree(longPathPrefix + srcFolder, longPathPrefix + targetFolder)
        self.logger.info("Done")
