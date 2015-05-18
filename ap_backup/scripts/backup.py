import sys
import argparse

from ap_backup.config import AppConfig
from ap_backup.reporter import Reporter
from ap_backup.processor import BackupProcessor

__author__ = 'Alexander Pikovsky'


def backup_main():
    parser = argparse.ArgumentParser(prog='ap-backup', description='ap-backup utility.', add_help=False)

    parser.add_argument('-h', '--help', action='store_true', help="prints command help")

    parser.add_argument('-c', '--config', type=str, metavar='FILE',
                        help="config file, default is '/etc/ap-backup/config.yaml'",
                        default='/etc/ap-backup/config.yaml')

    #parse arguments and call command function
    args = parser.parse_args()

    #handle help
    if args.help:
        parser.print_help()
        sys.exit()

    reporter = Reporter(logger_name='summary')
    reporter.info("Starting backup.", separator=True)

    #load config
    reporter.info("Loading application configuration file '{0}'...".format(args.config), separator=True)
    app_config = AppConfig(args.config)
    reporter.info("Application configuration file loaded successfully, {0} backup configuration(s) found."
                        .format(len(app_config.backup_configs)))

    #process backup configs
    try:
        #process backup configs, don't abort if some of them fail
        updated_configs = 0
        up_to_date_configs = 0
        failed_configs = 0
        for backup_config in app_config.backup_configs:
            try:
                backup_processor = BackupProcessor(app_config, backup_config, reporter)
                updated_destinations = backup_processor.process()
                if updated_destinations > 0:
                    updated_configs += 1
                else:
                    up_to_date_configs += 1

            except Exception as ex:
                reporter.critical("Backup {0} failed: {1}".format(backup_config.name, str(ex)), exc_info=True)
                failed_configs += 1

        #complete
        if failed_configs == 0:
            reporter.info("Backup finished: {0} backups updated, {1} skipped (up-to-date)."
                          .format(updated_configs, up_to_date_configs), separator=True)
        else:
            reporter.error("Backup (partially) failed: {0} backups failed, {1} updated, {2} skipped (up-to-date)."
                           .format(failed_configs, updated_configs, up_to_date_configs), separator=True)

    except Exception as ex:
        reporter.critical("Backup failed: {0}".format(str(ex)), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    backup_main()