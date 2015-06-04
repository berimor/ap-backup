'''
Created on 14.06.2012

@author: Alexander Pikovsky
'''
import os
import datetime
import logging.config

import glob


class BackupChecker:
    """Processes the given backup configuration (makes backup)."""
       
    logger = logging.getLogger('backup_checker_protocol')

    backup_config = None
    config = None
    
    def __init__(self, app_config, backup_config, reporter):
        self.app_config = app_config
        self.backup_config = backup_config
        self.reporter = reporter.reporter(logger_name='protocol')

    def check(self) :
        """Checks the given backup configuration (checks whether all backups are up-to-date).
           Returns True if all up-to-date."""
        
        self.reporter.info("Checking backup '{0}'".format(self.backup_config.name))
        return True

        #distinguish by backup type
        if (self.backup_config.backupType == config.backupType_Archive) :
            #Archive backup config
        
            #check destinations
            for destination in self.backup_config.destinations :
                if (not checkRecentFileExists(destination.folder, self.backup_config.name + "*.zip",
                                               destination.scheduleMinutes, self.backup_config, self.logger)) :
                    return False
                                
            self.logger.info("Backup '{0}' checked: {1} destinations up-to-date.".format(self.backup_config.name,
                len(self.backup_config.destinations)))

        elif (self.backup_config.backupType == config.backupType_Checker) :
            #Checker backup config
            
            #check objects
            for checkObject in self.backup_config.backupCheckObjects :
                #create processor
                processor = None
                if (isinstance(checkObject, apbackup.config.BackupCheckObjectRecentFileExists)):
                    processor = BackupCheckObjectRecentFileExistsProcessor(checkObject, self)
                elif (isinstance(checkObject, apbackup.config.BackupCheckObjectCompareFileToSrc)):
                    processor = BackupCheckObjectCompareFileToSrcProcessor(checkObject, self)
                else :
                    raise Exception("Unsupported backup check object.")
            
                #check
                if (not processor.doCheck()) :
                    return False
                
            self.logger.info("Backup '{0}' checked: {1} objects up-to-date.".format(self.backup_config.name,
                len(self.backup_config.backupCheckObjects)))
        
        else :
            raise Exception("Unsupported backup type '{0}' in backup '{1}'".format(self.backupType, self.name))
                  
        return True
    

class BackupCheckObjectProcessor :
    """Base class for backup check object processors."""

    logger = None
    
    backupCheckObject = None # corresponding backup object
    backupChecker = None # parent checker
    
    def __init__(self, backupCheckObject, backupChecker):       
        self.logger = backupChecker.logger
        self.backupCheckObject = backupCheckObject    
        self.backupChecker = backupChecker    

    def doCheck(self):
        raise Exception("This method must be overridden.")       



class BackupCheckObjectRecentFileExistsProcessor(BackupCheckObjectProcessor) :
    """RecentFileExists backup check object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super().__init__(backupCheckObject, backupChecker)
        

    def doCheck(self):
        return checkRecentFileExists(self.backupCheckObject.backup_folder, self.backupCheckObject.backup_file_name_pattern,
            self.backupCheckObject.scheduleMinutes, self.backupChecker.backup_config, self.backupChecker.logger)


class BackupCheckObjectCompareFileToSrcProcessor(BackupCheckObjectProcessor) :
    """CompareFileToSrc backup check object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super().__init__(backupCheckObject, backupChecker)
        

    def doCheck(self):
        logger = self.backupChecker.logger
        
        #get src and backup file info
        backup_file = self.backupCheckObject.backup_file
        if (not os.path.isfile(backup_file)) :
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


def checkRecentFileExists(backup_folder, backup_file_name_pattern, scheduleMinutes, backup_config, logger) :
    """Checks that the given folder contains at least one recent enough file with the given pattern."""
    
    current_time = datetime.datetime.now()

    latestFileTime = None
    backupFilePattern = os.path.join(backup_folder, backup_file_name_pattern)
    existingBackups = glob.glob(backupFilePattern)
    for existingBackup in existingBackups :
        modificationTime = datetime.datetime.fromtimestamp(os.path.getmtime(existingBackup))
        if (not latestFileTime or latestFileTime < modificationTime) :
            latestFileTime = modificationTime

    #check whether up-to-date
    if (not latestFileTime) :
        logger.error("No backup file found for '{0}'".format(backupFilePattern))
        return False       # no backup file found
    
    accuracyDelta = datetime.timedelta(days=backup_config.checker_accuracy_days)
    maxDiff = datetime.timedelta(minutes=scheduleMinutes) + accuracyDelta
    minTime = current_time - maxDiff
    if (minTime > latestFileTime) :
        logger.error("Backup OUT-OF-DATE: last backup for '{0}' found at {1}, but must be at least {2}"
                          .format(backupFilePattern, latestFileTime, minTime))
        return False

    return True