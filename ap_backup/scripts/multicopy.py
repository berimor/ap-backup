import argparse

from ap_backup.multicopy import multicopy

__author__ = 'Alexander Pikovsky'


DESCRIPTION = """
Copies the given file or folder to the target folder, whereby the file/folder
name is constructed by appending the current date (and possibly time) to the
file/folder name. If other copies exist in the given target folder, the old
ones are deleted to maintain at most num-copies files/folders.

The command creates a new copy only if at least min_period_days is elapsed since
the last existing copy or there is no existing copies in the target folder.
New copy is always created if min_period_days is 0.
"""


def multicopy_main():

    parser = argparse.ArgumentParser(prog='ap-multicopy', description=DESCRIPTION, add_help=True,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(dest='src_file_or_dir', type=str, metavar='SRC_FILE_OR_DIR',
                        help='the file or directory to copy')

    parser.add_argument(dest='target_dir', type=str, metavar='TARGET_DIR',
                        help='directory where the copies will be stored')

    parser.add_argument('-n', '--num-copies', dest='num_copies', default=5, type=int,
                        help='number of copies to maintain (including the new one); default is 5',
                        metavar='NUM_COPIES')
    parser.add_argument('-d', '--min-period-days', dest='min_period_days', default=0, type=int,
                        help='minimum number of days since last backup; 0 to force copy in any case; default is 0',
                        metavar='MIN_DAYS')
    parser.add_argument('-b', '--target-base-name', dest='target_base_name', default=None,
                        help='beginning of the target file name; if not specified, source file or folder name is used',
                        metavar='NAME')
    parser.add_argument('-T', '--no-time',
                        action='store_false', dest='append_time', default=True,
                        help='if specified, time is not added to the backup name, so at most 1 copy per day can '
                             'be maintained')
    parser.add_argument('-E', '--ignore-errors',
                        action='store_true', dest='ignore_errors', default=False,
                        help='if specified, copy errors are ignored and the list of not copied files is printed; '
                             'otherwise exception occurs on copy errors')

    #parse arguments and call command function
    args = parser.parse_args()

    #run
    multicopy(
        args.src_file_or_dir,
        args.target_dir,
        num_copies=args.num_copies,
        target_base_name=args.target_base_name,
        min_period_days=args.min_period_days,
        append_time=args.append_time,
        ignore_errors=args.ignore_errors)


if __name__ == '__main__':
    multicopy_main()