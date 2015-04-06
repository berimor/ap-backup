'''
Created on 14.06.2012

@author: Alexander Pikovsky
'''
import os
import datetime
import logging.config
import sys

import apgeneral.os
import aploggers.loggers
import apbackup.config
import glob
from apbackup import config

def runChecker(backupCheckerDir) : 
    """Main backup method.
       
       backupCheckerDir : directory containing the backup checker configuration.
    """

    packageDir = os.path.dirname(os.path.realpath(__file__))
    
    logging.config.fileConfig(os.path.join(packageDir, "logging.conf"))
    LOG = aploggers.loggers.LogMessages(packageDir)
    logger = logging.getLogger('backup_checker_summary')
          
    #execute main program
    try:
        #read config file
        config = apbackup.config.Config(backupCheckerDir)
    
        #complete
        logger.info(LOG.Msg("BackupCheckerStarted", backupCheckerDir))
    
        #connect network shares
        for rns in config.requiredNetworkShares :
            apgeneral.os.connectNetworkShare(rns.driveName, rns.uncPath)
        
        #process backup configs, don't abort if some of them fail
        upToDateConfigs = 0
        failedConfigs = 0
        for backupConfig in config.backupConfigs :
            try :
                backupChecker = BackupChecker(backupConfig, config)
                upToDate = backupChecker.check()
                if (upToDate) :
                    upToDateConfigs += 1 
                else :
                    failedConfigs += 1
            
            except Exception as ex:
                logger.critical(LOG.Msg("BackupCheckerException", backupConfig.name, str(ex)), exc_info=True)
                failedConfigs += 1
    
        #complete
        if (failedConfigs == 0) :
            logger.info(LOG.Msg("BackupCheckerComplete", backupCheckerDir, upToDateConfigs))
        else :
            logger.error(LOG.Msg("BackupCheckerCompleteWithFailures", backupCheckerDir, failedConfigs, upToDateConfigs))
    
    except Exception as ex:
        logger.critical(LOG.Msg("UnexpectedException", str(ex)), exc_info=True)
        sys.exit(1)
        
    finally:
        #disconnect network shares
        for rns in config.requiredNetworkShares :
            apgeneral.os.disconnectNetworkShare(rns.driveName)




class BackupChecker :
    """Processes the given backup configuration (makes backup)."""
       
    logger = logging.getLogger('backup_checker_protocol')

    backupConfig = None
    config = None
    
    def __init__(self, backupConfig, config):
        self.config = config
        self.backupConfig = backupConfig
        
        
    def check(self) :
        """Checks the given backup configuration (checks whether all backups are up-to-date).
           Returns True if all up-to-date."""
        
        self.logger.info("Checking backup '{0}'...".format(self.backupConfig.name))

        #distinguish by backup type
        if (self.backupConfig.backupType == config.backupType_Archive) : 
            #Archive backup config
        
            #check destinations
            for destination in self.backupConfig.destinations :
                if (not checkRecentFileExists(destination.folder, self.backupConfig.name + "*.zip", 
                                               destination.scheduleMinutes, self.backupConfig, self.logger)) :
                    return False
                                
            self.logger.info("Backup '{0}' checked: {1} destinations up-to-date.".format(self.backupConfig.name,
                len(self.backupConfig.destinations)))

        elif (self.backupConfig.backupType == config.backupType_Checker) : 
            #Checker backup config
            
            #check objects
            for checkObject in self.backupConfig.backupCheckObjects :
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
                
            self.logger.info("Backup '{0}' checked: {1} objects up-to-date.".format(self.backupConfig.name,
                len(self.backupConfig.backupCheckObjects)))
        
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
        return checkRecentFileExists(self.backupCheckObject.backupFolder, self.backupCheckObject.backupFileNamePattern, 
            self.backupCheckObject.scheduleMinutes, self.backupChecker.backupConfig, self.backupChecker.logger)


class BackupCheckObjectCompareFileToSrcProcessor(BackupCheckObjectProcessor) :
    """CompareFileToSrc backup check object processor."""
           
    def __init__(self, backupCheckObject, backupChecker):       
        super().__init__(backupCheckObject, backupChecker)
        

    def doCheck(self):
        logger = self.backupChecker.logger
        
        #get src and backup file info
        backupFile = self.backupCheckObject.backupFile
        if (not os.path.isfile(backupFile)) :
            raise Exception("Backup file '" + backupFile + "' does not exist!")

        srcFile = self.backupCheckObject.srcFile
        if (not os.path.isfile(srcFile)) :
            raise Exception("Source file '" + srcFile + "' does not exist!")

        backupFileTime = datetime.datetime.fromtimestamp(os.path.getmtime(backupFile))
        srcFileTime = datetime.datetime.fromtimestamp(os.path.getmtime(srcFile))
        accuracyDelta = datetime.timedelta(days=self.backupChecker.backupConfig.checker_accuracy_days)
        
        #determine min time due to schedule
        currentTime = datetime.datetime.now()
        maxScheduleDiff = datetime.timedelta(minutes=self.backupCheckObject.scheduleMinutes) + accuracyDelta
        minScheduleTime = currentTime - maxScheduleDiff

        #determine min time due to source file
        minSrcTime = srcFileTime
        
        #min time is the weakest of both
        minTime = min(minScheduleTime, minSrcTime)
        
        if (minTime > backupFileTime) :
            logger.error("Backup OUT-OF-DATE: backup file '{0}' is at {1}, but must be at least {2}"
                .format(backupFile, backupFileTime, minTime))
            return False

        return True


def checkRecentFileExists(backupFolder, backupFileNamePattern, scheduleMinutes, backupConfig, logger) :
    """Checks that the given folder contains at least one recent enough file with the given pattern."""
    
    currentTime = datetime.datetime.now()

    latestFileTime = None
    backupFilePattern = os.path.join(backupFolder, backupFileNamePattern)
    existingBackups = glob.glob(backupFilePattern)
    for existingBackup in existingBackups :
        modificationTime = datetime.datetime.fromtimestamp(os.path.getmtime(existingBackup))
        if (not latestFileTime or latestFileTime < modificationTime) :
            latestFileTime = modificationTime

    #check whether up-to-date
    if (not latestFileTime) :
        logger.error("No backup file found for '{0}'".format(backupFilePattern))
        return False       # no backup file found
    
    accuracyDelta = datetime.timedelta(days=backupConfig.checker_accuracy_days)
    maxDiff = datetime.timedelta(minutes=scheduleMinutes) + accuracyDelta
    minTime = currentTime - maxDiff
    if (minTime > latestFileTime) :
        logger.error("Backup OUT-OF-DATE: last backup for '{0}' found at {1}, but must be at least {2}"
                          .format(backupFilePattern, latestFileTime, minTime))
        return False

    return True