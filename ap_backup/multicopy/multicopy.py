import os.path
from datetime import date, datetime
from time import strptime
import glob
import shutil

def multiCopy(srcFileOrFolder, targetDir, numCopies, minPeriodDays = 0, targetBaseName = None, appendTime = True,
              ignoreErrors = False, logger = None) :
    """
    Copies the given file or folder to the target folder, whereby the file/folder name is constructed 
    by appending the current date (and possibly time) to the file/folder name. If another copies exist 
    in the given target folder, the old ones are deleted to maintain at most num_copies of. The command
    creates a new copy only if at least minPeriodDays is elapsed since the last existing copy or there 
    is no existing copies in the target folder. New backup is always created if minPeriodDays is 0.
      
         srcFileOrFolder    the file or folder to copy
         targetDir          folder where the copies will be stored
         num_copies          number of copies to maintain (including the new one)
         minPeriodDays      minimum number of days since last backup; 0 to force copy in any case
         targetBaseName     beginning of the target file name; if None, source file or folder name is used
         appendTime         if True, makes different backups for different times on the same day, adds the 
                            time to the target file/folder name
         ignoreErrors       if True, the copy errors are ignored and the list of not copied files is printed;
                            if False, exception occurs on copy errors
                            
         logger             logger (prints output to console if not specified)
    """
    
    def logInfo(message):
        if (logger) :
            logger.info(message)
        else :
            print(message)
            
    #print(srcFileOrFolder, targetDir, targetBaseName, minPeriodDays, num_copies)
    
    #parse source file/folder name, detect mode ("file" or "folder")
    mode = "none"
    if (os.path.isfile(srcFileOrFolder)) :
        mode = "file"
        srcFileOrFolderName, srcFileExtension = os.path.splitext(os.path.basename(srcFileOrFolder))
    elif (os.path.isdir(srcFileOrFolder)) :
        mode = "folder"
        srcFileOrFolderName, srcFileExtension = os.path.basename(srcFileOrFolder), ""
    else :
        raise Exception("Source file or folder '" + srcFileOrFolder + "' does not reference an existing file or folder!")
        
    #check target dir
    if (not os.path.isdir(targetDir)) :
        raise Exception("Target directory '" + targetDir + "' does not exist or is not a directory!")

    #print(srcFileOrFolderName, srcFileExtension)
    
    
    #get current date/time
    currentDate = date.today()
    currentDateTime = datetime.now()
    
    #calc target base name 
    if (targetBaseName == None) :
        targetBaseName = srcFileOrFolderName;
        
    #construct new file/folder name
    dateTimeStr = currentDateTime.strftime("%Y-%m-%d")
    if (appendTime) :
        dateTimeStr = dateTimeStr + "_" + currentDateTime.strftime("%H-%M")
    
    newFileOrFolderName = targetBaseName + "_" + dateTimeStr + srcFileExtension
    newFileOrFolderPath = os.path.join(targetDir, newFileOrFolderName)
      
    
    #print(newFileOrFolderName, newFileOrFolderPath)
    
    
    #get the list of all existing backup files or folders
    #sort existing backups in date-reverse order (newer files/folders first)
    existingBackups = glob.glob(os.path.join(targetDir, targetBaseName + "_*" + srcFileExtension))
    existingBackups.sort()
    existingBackups.reverse()
    #print(existingBackups)
    
    
    #get the last existing backup (if any), parse the date (sets minPeriodDays = 0 if parse error or no existing backup)
    if (len(existingBackups) > 0) :
        if (mode == "file") :
            lastBackupName = os.path.splitext(os.path.basename(existingBackups[0]))[0]
        elif (os.path.isdir(srcFileOrFolder)) :
            lastBackupName = os.path.basename(existingBackups[0])
        
        lastBackupDateString = lastBackupName[-10:]
        
        try:
            lastBackupDate = date(*strptime(lastBackupDateString, "%Y_%m_%d")[0:3])
        except ValueError:
            #invalid format => set to today, but period to 0 (to force backup)
            lastBackupDate = currentDate
            minPeriodDays = 0
    else :
        lastBackupDate = currentDate
        minPeriodDays = 0
            
    #print lastBackupDateString, lastBackupDate, minPeriodDays, (currentDate - lastBackupDate).days
    
    
    #back up the file or folder, if needed
    if (minPeriodDays == 0 or (currentDate - lastBackupDate).days >= minPeriodDays) :
        if (mode == "file") :
            logInfo("Copying source file to '" + newFileOrFolderPath + "'...")
            if (os.path.isfile(newFileOrFolderPath)) :
                os.remove(newFileOrFolderPath)
            try :
                shutil.copyfile(srcFileOrFolder, newFileOrFolderPath)
            except IOError:
                if (ignoreErrors) :
                    print("\n\nFollowing file could not be copied:")
                    print(srcFileOrFolder)
                else :
                    raise
        else :
            logInfo("Copying source folder to '" + newFileOrFolderPath + "'...")
            if (os.path.isdir(newFileOrFolderPath)) :
                shutil.rmtree(newFileOrFolderPath)
            
            try :
                shutil.copytree(srcFileOrFolder, newFileOrFolderPath)
            except shutil.Error as err :
                nonCopiedFiles = err.args[0]
                if (ignoreErrors) :
                    print ("\n\nFollowing", len(nonCopiedFiles), "files could not be copied:")
                    for nonCopiedFile in nonCopiedFiles :
                        nonCopiedFileSrc = nonCopiedFile[0]
                        print("    " + nonCopiedFileSrc)
                else :
                    raise
            
        logInfo("Done")
    else :
        logInfo("Skiping backup because the last existing backup is new enough.")
    
    #cleaning up existing backups
    logInfo("Cleaning up existing copies...")
    
    #again get the list of all existing backup files or folders (now includes the new backup)
    #sort existing backups in date-reverse order (newer files/folders first)
    existingBackups = glob.glob(os.path.join(targetDir, targetBaseName + "_*" + srcFileExtension))
    existingBackups.sort()
    existingBackups.reverse()
    #print(existingBackups)
        
    #delete out-of-date files/folders (all starting at num_copies)
    for existingBackup in existingBackups[numCopies:]: 
        if (mode == "file") :
            os.remove(existingBackup)
        else :
            shutil.rmtree(existingBackup)
    
    #Cleaning up done
    logInfo("Done")

