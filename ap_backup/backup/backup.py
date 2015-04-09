import sys
import argparse

from ap_backup.config import AppConfig
from ap_backup.reporter import Reporter

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

    reporter = Reporter()

    #load config
    reporter.print_line("Loading configuration file '{0}'...".format(args.config), True)
    config = AppConfig(args.config)
    reporter.print_line("Configuration file loaded successfully, {0} backup configuration(s) found."
                        .format(len(config.backup_configs)))

    #run backup processor



if __name__ == "__main__":
    backup_main()