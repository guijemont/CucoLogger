#!/usr/bin/env python
# Copyright 2013 Guillaume Emont <guij@emont.org>
#
# This file is part of CucoLogger
#
# CucoLogger is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import parser, serial_tools, data_save

class CucoLoggerConfigException(Exception):
    pass

class CucoLogger(object):
    def __init__(self, config):
        if "savers" not in config or len(config['savers']) == 0:
            raise CucoLoggerConfigException("no savers in config")

        self._savers = []
        for saver, saver_config in config['savers'].iteritems():
            if saver == "RrdDataSaver":
                constructor = data_save.RrdDataSaver
            elif saver == "CsvDataSaver":
                constructor = data_save.CsvDataSaver
            elif saver == "ThermostatSaver":
                constructor = data_save.ThermostatSaver
            else:
                raise CucoLoggerConfigException("Unknown saver: %s" % saver)
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
            print >> sys.stderr, "\nCucoLogger stopping operations because of keyboard interrupt"

        for saver in self._savers:
            saver.close()

if __name__ == '__main__':
    import sys, os, json
    config_file = "./cucologger.conf"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    if not os.path.exists(config_file):
        print >> sys.stderr, "Could not find configuration file in %s, exiting" % config_file
        sys.exit(1)

    print "Loading configuration from %s" % config_file
    config = json.load(open(config_file))

    logger = CucoLogger(config)
    logger.run()
