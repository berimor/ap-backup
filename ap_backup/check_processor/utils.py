
__author__ = 'Alexander Pikovsky'


def check_recent_file_exists(backup_folder, backup_file_name_pattern, scheduleMinutes, backup_config, logger) :
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