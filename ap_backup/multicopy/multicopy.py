import os.path
from datetime import date, datetime
from time import strptime
import glob
import shutil


def multicopy(src_file_or_dir, target_dir, num_copies, min_period_days=0, target_base_name=None, append_time=True,
               ignore_errors=False, reporter=None):
    """
    Copies the given file or folder to the target folder, whereby the file/folder name is constructed 
    by appending the current date (and possibly time) to the file/folder name. If another copies exist 
    in the given target folder, the old ones are deleted to maintain at most num_copies of. The command
    creates a new copy only if at least min_period_days is elapsed since the last existing copy or there
    is no existing copies in the target folder. New backup is always created if min_period_days is 0.
      
    :param src_file_or_dir: the file or folder to copy
    :param target_dir: folder where the copies will be stored
    :param num_copies: number of copies to maintain (including the new one)
    :param min_period_days: minimum number of days since last backup; 0 to force copy in any case
    :param target_base_name: beginning of the target file name; if None, source file or folder name is used
    :param append_time: if True, makes different backups for different times on the same day, adds the
                        time to the target file/folder name
    :param ignore_errors: if True, the copy errors are ignored and the list of not copied files is printed;
                          if False, exception occurs on copy errors
                            
    :param reporter: reporter (prints output to console if not specified)
    """
    
    def log_info(message):
        if reporter:
            reporter.info(message)
        else:
            print(message)
            
    #print(src_file_or_dir, target_dir, target_base_name, min_period_days, num_copies)
    
    #parse source file/folder name, detect mode ("file" or "folder")
    MODE_FILE = "file"
    MODE_DIR = "dir"
    if os.path.isfile(src_file_or_dir):
        mode = MODE_FILE
        src_file_or_dir_name, src_file_extension = os.path.splitext(os.path.basename(src_file_or_dir))
    elif os.path.isdir(src_file_or_dir):
        mode = MODE_DIR
        src_file_or_dir_name, src_file_extension = os.path.basename(src_file_or_dir), ""
    else:
        raise Exception("Source path '{0}' does not reference an existing file or directory!"
                        .format(src_file_or_dir))
        
    #check target dir
    if not os.path.isdir(target_dir):
        raise Exception("Target directory '" + target_dir + "' does not exist or is not a directory!")

    #print(src_file_or_dir_name, src_file_extension)

    #get current date/time
    current_date = date.today()
    current_date_time = datetime.now()
    
    #calc target base name 
    if target_base_name is None:
        target_base_name = src_file_or_dir_name;
        
    #construct new file/folder name
    date_time_str = current_date_time.strftime("%Y-%m-%d")
    if append_time:
        date_time_str = date_time_str + "_" + current_date_time.strftime("%H-%M")
    
    new_file_or_dir_name = target_base_name + "_" + date_time_str + src_file_extension
    new_file_or_dir_path = os.path.join(target_dir, new_file_or_dir_name)

    #print(new_file_or_dir_name, new_file_or_dir_path)
    
    #get the list of all existing backup files or folders
    #sort existing backups in date-reverse order (newer files/folders first)
    existing_backups = glob.glob(os.path.join(target_dir, target_base_name + "_*" + src_file_extension))
    existing_backups.sort()
    existing_backups.reverse()
    #print(existing_backups)

    #get the last existing backup (if any), parse date (sets min_period_days = 0 if parse error or no existing backup)
    if len(existing_backups) > 0:
        if mode == MODE_FILE:
            last_backup_name = os.path.splitext(os.path.basename(existing_backups[0]))[0]
        elif os.path.isdir(src_file_or_dir):
            last_backup_name = os.path.basename(existing_backups[0])
        
        last_backup_date_string = last_backup_name[-10:]
        
        try:
            last_backup_date = date(*strptime(last_backup_date_string, "%Y_%m_%d")[0:3])
        except ValueError:
            #invalid format => set to today, but period to 0 (to force backup)
            last_backup_date = current_date
            min_period_days = 0
    else:
        last_backup_date = current_date
        min_period_days = 0
            
    #print last_backup_date_string, last_backup_date, min_period_days, (current_date - last_backup_date).days

    #back up the file or folder, if needed
    if min_period_days == 0 or (current_date - last_backup_date).days >= min_period_days:
        if mode == MODE_FILE:
            log_info("Copying '{0}' to '{1}'...".format(src_file_or_dir, new_file_or_dir_path))
            if os.path.isfile(new_file_or_dir_path):
                os.remove(new_file_or_dir_path)
            try:
                shutil.copyfile(src_file_or_dir, new_file_or_dir_path)
            except IOError:
                if ignore_errors:
                    log_info("\n\nFollowing file could not be copied: '{0}'.".format(src_file_or_dir))
                else:
                    raise
        else:
            log_info("Copying source folder to '" + new_file_or_dir_path + "'...")
            if os.path.isdir(new_file_or_dir_path):
                shutil.rmtree(new_file_or_dir_path)
            
            try:
                shutil.copytree(src_file_or_dir, new_file_or_dir_path)
            except shutil.Error as err :
                non_copied_files = err.args[0]
                if ignore_errors:
                    log_info ("\n\nFollowing", len(non_copied_files), "files could not be copied:")
                    for non_copied_file in non_copied_files:
                        non_copied_file_src = non_copied_file[0]
                        log_info("    " + non_copied_file_src)
                else:
                    raise
            
        log_info("Done")
    else:
        log_info("Skiping backup because the last existing backup is new enough.")
    
    #cleaning up existing backups
    log_info("Cleaning up existing copies...")
    
    #again get the list of all existing backup files or folders (now includes the new backup)
    #sort existing backups in date-reverse order (newer files/folders first)
    existing_backups = glob.glob(os.path.join(target_dir, target_base_name + "_*" + src_file_extension))
    existing_backups.sort()
    existing_backups.reverse()
    #print(existing_backups)
        
    #delete out-of-date files/folders (all starting at num_copies)
    for existingBackup in existing_backups[num_copies:]:
        if mode == MODE_FILE:
            os.remove(existingBackup)
        else:
            shutil.rmtree(existingBackup)
    
    #Cleaning up done
    log_info("Done")
