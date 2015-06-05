from datetime import datetime, timedelta
import glob
import os
from croniter import croniter

__author__ = 'Alexander Pikovsky'


def check_recent_file_exists(backup_folder, backup_file_name_pattern, schedule, accuracy_days, reporter) :
    """Checks that the given folder contains at least one recent enough file with the given pattern."""

    current_time = datetime.now()

    latest_file_time = None
    backup_file_pattern = os.path.join(backup_folder, backup_file_name_pattern)
    existing_backups = glob.glob(backup_file_pattern)
    for existingBackup in existing_backups :
        modification_time = datetime.fromtimestamp(os.path.getmtime(existingBackup))
        if not latest_file_time or latest_file_time < modification_time:
            latest_file_time = modification_time

    #check whether up-to-date
    if not latest_file_time:
        reporter.error("No backup file found for '{0}'".format(backup_file_pattern))
        return False       # no backup file found

    prev_trigger = croniter(schedule, current_time).get_prev(datetime)
    accuracy_delta = timedelta(days=accuracy_days)
    min_time = prev_trigger - accuracy_delta
    if min_time > latest_file_time:
        reporter.error("Backup OUT-OF-DATE: last backup for '{0}' found at {1}, but must be at least {2}"
                       .format(backup_file_pattern, latest_file_time, min_time))
        return False

    return True