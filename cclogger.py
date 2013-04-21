#!/usr/bin/env python

class CCLogger(object):
    def __init__(self, source, parser, savers):
        self._source = source
        self._parser = parser
        self._savers = savers

    def run(self):
        try:
            for line in self._source:
                for data_point in self._parser.parse_msg(line):
                    for saver in self._savers:
                        saver.update(data_point)
        except KeyboardInterrupt:
            print >> sys.stderr, "\nCCLogger stopping operations because of keyboard interrupt"

if __name__ == '__main__':
    import sys, os
    import parser, serial_tools, data_save
    logger = CCLogger(serial_tools.open_cc128(),
                parser.CC128LiveParser(),
                (data_save.RrdDataSaver(sys.argv[1]),
                data_save.CsvDataSaver(sys.argv[2])))
    logger.run()
