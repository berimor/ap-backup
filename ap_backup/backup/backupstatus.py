'''
Created on 14.06.2012

@author: Alexander Pikovsky
'''
import os
import configparser
from apgeneral import *
            
                       
class DestinationStatus :
    """Holds a backup status for the given destination."""
    destinationName = None
    lastBackupResult = None
    lastSuccessfulBackupTime = None
    lastBackupAttemptTime = None

    def writeToSection(self, statusFile) :
        values = {}
        if (self.lastBackupResult) :
            values["LastBackupResult"] = self.lastBackupResult
        if (self.lastSuccessfulBackupTime) :                                                  
            values["LastSuccessfulBackupTime"] = helpers.datetimeToIsoString(self.lastSuccessfulBackupTime)
        if (self.lastBackupAttemptTime) : 
            values["LastBackupAttemptTime"] = helpers.datetimeToIsoString(self.lastBackupAttemptTime)
            
        statusFile["DestinationStatus_" + self.destinationName] = values
        
    def __init__(self, destinationName, lastBackupResult, lastSuccessfulBackupTime, lastBackupAttemptTime) :
        self.destinationName = destinationName
        self.lastBackupResult = lastBackupResult
        self.lastSuccessfulBackupTime = lastSuccessfulBackupTime
        self.lastBackupAttemptTime = lastBackupAttemptTime
    
    @classmethod
    def fromSection(cls, configSection) :
        sectionName = configSection.name
        if (not sectionName.startswith("DestinationStatus_")) :
            raise Exception("Invalid backup status section name '{0}'".format(sectionName))
        
        destinationName = sectionName[len("DestinationStatus_"):]
        lastBackupResult = helpers.getOptionalConfigValue(configSection, "LastBackupResult", None) 
        lastSuccessfulBackupTime = helpers.isoStringToDatetime(helpers.getOptionalConfigValue(configSection, "LastSuccessfulBackupTime", None))
        lastBackupAttemptTime = helpers.isoStringToDatetime(helpers.getOptionalConfigValue(configSection, "LastBackupAttemptTime", None))
        return DestinationStatus(destinationName, lastBackupResult, lastSuccessfulBackupTime, lastBackupAttemptTime)


class BackupStatus :
    """Holds backup status (infos for mall destinations)), reads and writes it from/to config file."""
    
    statusDir = None
    backupName = None
    
    #map of lastBackupResult -> DestinationStatus
    DestinationStatuses = None
    
    def getFilePath(self):
        return os.path.join(self.statusDir, self.backupName + ".bstat")
    
    def __init__(self, backupName, statusDir):
        """Loads backup status file if exists, otherwise creates one."""
        
        self.statusDir = statusDir
        self.backupName = backupName
        
        #read config file or create new
        statusFilePath = self.getFilePath()
        statusFile = configparser.ConfigParser()
        if (os.path.exists(statusFilePath)) :
            statusFile.read(statusFilePath)
        else :
            with open(statusFilePath, 'w') as file :
                statusFile.write(file)
        
        #enumerate notification sections
        self.DestinationStatuses = {}
        for sectionName in statusFile :
            if (not sectionName.startswith("DestinationStatus_")) :
                continue
            destinationStatus = DestinationStatus.fromSection(statusFile[sectionName])
            self.DestinationStatuses[destinationStatus.destinationName] = destinationStatus

    def save(self):
        statusFilePath = self.getFilePath()
        statusFile = configparser.ConfigParser()
        
        for destinationName in self.DestinationStatuses :
            self.DestinationStatuses[destinationName].writeToSection(statusFile)
            
        with open(statusFilePath, 'w') as file:
            statusFile.write(file)
        
    def get(self, destinationName) :
        """Gets status for the given destination or creates one (and adds to set) if does not exist."""
        
        if (destinationName in self.DestinationStatuses) :
            return self.DestinationStatuses[destinationName]
        else :
            destinationStatus = DestinationStatus(destinationName, None, None, None)
            self.DestinationStatuses[destinationName] = destinationStatus
            return destinationStatus
