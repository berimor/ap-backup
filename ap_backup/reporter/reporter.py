__author__ = 'Alexander Pikovsky'


class Reporter(object):

    def print_line(self, line, separator=False):
        if separator:
            print ""
        print line
