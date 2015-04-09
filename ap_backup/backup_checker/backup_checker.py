import sys
import argparse

__author__ = 'Alexander Pikovsky'


def backup_checker_main():
    parser = argparse.ArgumentParser(prog='ap-backup-checker', description='ap-backup-checker utility.', add_help=False)

    parser.add_argument('-h', '--help', action='store_true', help="prints command help")

    #parse arguments and call command function
    args = parser.parse_args()

    #handle help
    if args.help:
        parser.print_help()
        sys.exit()

    def print_line(line, separator=False):
        if separator:
            print ""
        print line


if __name__ == "__main__":
    backup_checker_main()