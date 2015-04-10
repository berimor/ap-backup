import os
import datetime
import shutil
import subprocess
import logging.config
import sys

import apgeneral.os
import apgeneral.ziputils
import apbackup.backupstatus
import apbackup.multicopy

statusesSubdir = "backup-statuses"
backupsSubdir = "backups"

#This prefix must be added to file paths to allow more than 255 characters in the path
longPathPrefix = "\\\\?\\"


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
        targetFolder = os.path.join(self.backupProcessor.last_backup_dir, self.backupObject.targetSubfolder)
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
        targetFolder = os.path.join(self.backupProcessor.last_backup_dir, self.backupObject.targetSubfolder)
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
        targetFolder = os.path.join(self.backupProcessor.last_backup_dir, self.backupObject.targetSubfolder)
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
        targetFolder = os.path.join(self.backupProcessor.last_backup_dir, self.backupObject.targetSubfolder)

        srcFolder = self.backupObject.src_folder_path
        if (not os.path.isdir(longPathPrefix + srcFolder)) :
            raise Exception("Source folder '" + srcFolder + "' does not exist!")
              
        self.logger.info("Copying folder '{0}'...".format(srcFolder))
        shutil.copytree(longPathPrefix + srcFolder, longPathPrefix + targetFolder)
        self.logger.info("Done")
