from optparse import OptionParser
import apbackup.multicopy
import sys

usage = """usage: %prog [options] src-file-or-folder target-dir

  src-file-or-folder    the file or folder to copy
  target-dir            folder where the copies will be stored
             
Copies the given file or folder to the target folder, whereby the file/folder 
name is constructed by appending the current date (and possibly time) to the 
file/folder name. If other copies exist in the given target folder, the old 
ones are deleted to maintain at most num-copies files/folders. 

The command creates a new copy only if at least minPeriodDays is elapsed since 
the last existing copy or there is no existing copies in the target folder. 
New copy is always created if minPeriodDays is 0.
""";

parser = OptionParser(usage)
parser.add_option("--num-copies", dest="num_copies", default=5, type="int",
                  help="number of copies to maintain (including the new one); default is 5", 
                  metavar="NUMBER")
parser.add_option("--min-period-days", dest="minPeriodDays", default=0, type="int",
                  help="minimum number of days since last backup; 0 to force copy in any case; default is 0",
                  metavar="NUMBER")
parser.add_option("--target-base-name", dest="targetBaseName", default=None,
                  help="beginning of the target file name; if not specified, source file or folder name is used",
                  metavar="NAME")
parser.add_option("--no-time",
                  action="store_false", dest="appendTime", default=True,
                  help="if specified, time is not added to the backup name, so at most 1 copy per day can be maintained")
parser.add_option("--ignore-errors",
                  action="store_true", dest="ignoreErrors", default=False,
                  help="if specified, the copy errors are ignored and the list of not copied files is printed; otherwise exception occurs on copy errors")

(options, args) = parser.parse_args()

#check parameters
if len(args) != 2 :
    print ("Wrong number of arguments. Use -h option for help.")
    sys.exit(1)

#print empty line
print("")
    
#get parameters
srcFileOrFolder = args[0]
targetDir = args[1]

#run
apbackup.multicopy.multiCopy(srcFileOrFolder, targetDir, 
   numCopies = options.numCopies, 
   targetBaseName = options.targetBaseName, 
   minPeriodDays = options.minPeriodDays, 
   appendTime = options.appendTime,
   ignoreErrors = options.ignoreErrors);
