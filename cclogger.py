#!/usr/bin/env python

import parser, serial_tools, data_save

class CCLoggerConfigException(Exception):
    pass

class CCLogger(object):
    def __init__(self, config):
        if "savers" not in config or len(config['savers']) == 0:
            raise CCLoggerConfigException("no savers in config")

        self._savers = []
        for saver, saver_config in config['savers'].iteritems():
            if saver == "RrdDataSaver":
                constructor = data_save.RrdDataSaver
            elif saver == "CsvDataSaver":
                constructor = data_save.CsvDataSaver
            else:
                raise CCLoggerConfigException("Unknown saver: %s" % saver)
            self._savers.append(constructor(**saver_config))

        self._source = serial_tools.open_cc128()
        self._parser = parser.CC128LiveParser()

    def run(self):
        try:
            for line in self._source:
                for data_point in self._parser.parse_msg(line):
                    for saver in self._savers:
                        saver.update(data_point)
        except KeyboardInterrupt:
            print >> sys.stderr, "\nCCLogger stopping operations because of keyboard interrupt"

        for saver in self._savers:
            saver.close()

if __name__ == '__main__':
    import sys, os, json
    config_file = "./cclogger.conf"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    if not os.path.exists(config_file):
        print >> sys.stderr, "Could not find configuration file in %s, exiting" % config_file
        sys.exit(1)

    print "Loading configuration from %s" % config_file
    config = json.load(open(config_file))

    logger = CCLogger(config)
    logger.run()
