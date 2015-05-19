import os.path
from datetime import date, datetime
from time import strptime
import glob
import shutil


def multi_copy(src_file_or_folder, target_dir, num_copies, min_period_days=0, target_base_name=None, append_time=True,
               ignore_errors=False, logger=None):
    """
    Copies the given file or folder to the target folder, whereby the file/folder name is constructed 
    by appending the current date (and possibly time) to the file/folder name. If another copies exist 
    in the given target folder, the old ones are deleted to maintain at most num_copies of. The command
    creates a new copy only if at least min_period_days is elapsed since the last existing copy or there
    is no existing copies in the target folder. New backup is always created if min_period_days is 0.
      
         src_file_or_folder    the file or folder to copy
         target_dir          folder where the copies will be stored
         num_copies          number of copies to maintain (including the new one)
         min_period_days      minimum number of days since last backup; 0 to force copy in any case
         target_base_name     beginning of the target file name; if None, source file or folder name is used
         append_time         if True, makes different backups for different times on the same day, adds the
                            time to the target file/folder name
         ignore_errors       if True, the copy errors are ignored and the list of not copied files is printed;
                            if False, exception occurs on copy errors
                            
         logger             logger (prints output to console if not specified)
    """
    
    def logInfo(message):
        if (logger) :
            logger.info(message)
        else :
            print(message)
            
    #print(src_file_or_folder, target_dir, target_base_name, min_period_days, num_copies)
    
    #parse source file/folder name, detect mode ("file" or "folder")
    if os.path.isfile(src_file_or_folder):
        mode = "file"
        src_file_or_folder_name, srcFileExtension = os.path.splitext(os.path.basename(src_file_or_folder))
    elif os.path.isdir(src_file_or_folder):
        mode = "folder"
        src_file_or_folder_name, srcFileExtension = os.path.basename(src_file_or_folder), ""
    else:
        raise Exception("Source file or folder '{0}' does not reference an existing file or folder!"
                        .format(src_file_or_folder))
        
    #check target dir
    if not os.path.isdir(target_dir):
        raise Exception("Target directory '" + target_dir + "' does not exist or is not a directory!")

    #print(src_file_or_folder_name, srcFileExtension)
    
    
    #get current date/time
    currentDate = date.today()
    currentDateTime = datetime.now()
    
    #calc target base name 
    if (target_base_name == None) :
        target_base_name = src_file_or_folder_name;
        
    #construct new file/folder name
    dateTimeStr = currentDateTime.strftime("%Y-%m-%d")
    if (append_time) :
        dateTimeStr = dateTimeStr + "_" + currentDateTime.strftime("%H-%M")
    
    newFileOrFolderName = target_base_name + "_" + dateTimeStr + srcFileExtension
    newFileOrFolderPath = os.path.join(target_dir, newFileOrFolderName)
      
    
    #print(newFileOrFolderName, newFileOrFolderPath)
    
    
    #get the list of all existing backup files or folders
    #sort existing backups in date-reverse order (newer files/folders first)
    existing_backups = glob.glob(os.path.join(target_dir, target_base_name + "_*" + srcFileExtension))
    existing_backups.sort()
    existing_backups.reverse()
    #print(existing_backups)

    #get the last existing backup (if any), parse the date (sets min_period_days = 0 if parse error or no existing backup)
    if len(existing_backups) > 0:
        if mode == "file":
            last_backup_name = os.path.splitext(os.path.basename(existing_backups[0]))[0]
        elif os.path.isdir(src_file_or_folder):
            last_backup_name = os.path.basename(existing_backups[0])
        
        last_backup_date_string = last_backup_name[-10:]
        
        try:
            last_backup_date = date(*strptime(last_backup_date_string, "%Y_%m_%d")[0:3])
        except ValueError:
            #invalid format => set to today, but period to 0 (to force backup)
            last_backup_date = currentDate
            min_period_days = 0
    else:
        last_backup_date = currentDate
        min_period_days = 0
            
    #print last_backup_date_string, last_backup_date, min_period_days, (currentDate - last_backup_date).days
    
    
    #back up the file or folder, if needed
    if (min_period_days == 0 or (currentDate - last_backup_date).days >= min_period_days) :
        if (mode == "file") :
            logInfo("Copying source file to '" + newFileOrFolderPath + "'...")
            if (os.path.isfile(newFileOrFolderPath)) :
                os.remove(newFileOrFolderPath)
            try :
                shutil.copyfile(src_file_or_folder, newFileOrFolderPath)
            except IOError:
                if (ignore_errors) :
                    print("\n\nFollowing file could not be copied:")
                    print(src_file_or_folder)
                else :
                    raise
        else :
            logInfo("Copying source folder to '" + newFileOrFolderPath + "'...")
            if (os.path.isdir(newFileOrFolderPath)) :
                shutil.rmtree(newFileOrFolderPath)
            
            try :
                shutil.copytree(src_file_or_folder, newFileOrFolderPath)
            except shutil.Error as err :
                nonCopiedFiles = err.args[0]
                if (ignore_errors) :
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
    existing_backups = glob.glob(os.path.join(target_dir, target_base_name + "_*" + srcFileExtension))
    existing_backups.sort()
    existing_backups.reverse()
    #print(existing_backups)
        
    #delete out-of-date files/folders (all starting at num_copies)
    for existingBackup in existing_backups[num_copies:]:
        if (mode == "file") :
            os.remove(existingBackup)
        else :
            shutil.rmtree(existingBackup)
    
    #Cleaning up done
    logInfo("Done")

