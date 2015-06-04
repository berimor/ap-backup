import sys
import argparse

from ap_backup import AppConfig
from ap_backup.backup_checker import BackupChecker
from ap_backup.reporter import Reporter

__author__ = 'Alexander Pikovsky'


def backup_checker_main():
    parser = argparse.ArgumentParser(prog='ap-backup-checker', description='ap-backup-checker utility.', add_help=False)

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
    reporter.info("Checking backups...", separator=True)

    #load config
    reporter.info("Loading application configuration file '{0}'...".format(args.config), separator=True)
    app_config = AppConfig(args.config)
    reporter.info("Application configuration file loaded successfully, {0} backup configuration(s) found.\n"
                        .format(len(app_config.backup_configs)))

    try:
        #process backup configs, don't abort if some of them fail
        up_to_date_configs = 0
        failed_configs = 0
        for backup_config in app_config.backup_configs:
            try:
                checker = BackupChecker(app_config, backup_config, reporter)
                up_to_date = checker.check()
                if up_to_date:
                    up_to_date_configs += 1
                else:
                    failed_configs += 1

            except Exception as ex:
                reporter.critical("Backup checker failed for backup '{0}': {1}"
                                  .format(backup_config.name, str(ex)), exc_info=True)
                failed_configs += 1

        #complete
        if failed_configs == 0:
            reporter.info("Backup checker finished for configuration '{0}': {1} backup(s) up-to-date."
                          .format(args.config, up_to_date_configs), separator=True)
            sys.exit(0)
        else:
            reporter.error("Backup checker FAILED for configuration '{0}': {1} backup(s) failed, {2} up-to-date."
                           .format(args.config, failed_configs, up_to_date_configs), separator=True)
            sys.exit(1)

    except Exception as ex:
        reporter.critical("Backup checker failed: {0}".format(str(ex)), exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    backup_checker_main()