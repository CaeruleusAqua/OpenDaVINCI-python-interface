class Logger:
    def __init__(self):
        pass

    DEFAULT = 0
    GREEN = 1
    YELLOW = 2

    @staticmethod
    def logInfo(line, color=GREEN):
        if color == Logger.YELLOW:
            print "\033[1;33;40m" + line + "\033[0;37;39m"
        if color == Logger.GREEN:
            print "\033[1;33;92m" + line + "\033[0;37;39m"
        if color == Logger.DEFAULT:
            print line

    @staticmethod
    def logWarn(line):
        print "\033[1;33;40mWarning! " + line + "\033[0;37;39m"

    @staticmethod
    def logError(line):
        print "\033[1;33;91mERROR! " + line + "\033[0;37;39m"

    @staticmethod
    def lineHappen(line, line_nr, color=DEFAULT):
        if color is Logger.DEFAULT:
            print "Happens in line %s: %s" % (line_nr + 1, line.replace("\r", "").replace("\n", ""))