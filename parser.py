#!/usr/bin/env python

import time
from bs4 import BeautifulSoup
import serial

import serial_tools

class IteratorLogger(object):
    def __init__(self, iterator, log_file_name):
        self._log_file = file(log_file_name, 'a')
        self._iterator = iterator

    def __iter__(self):
        for item in self._iterator:
            print >> self._log_file, "%s: %s" % (time.strftime("%F %T"), item)
            yield item

class CC128Parser(object):
    def parse_msg(self, xml_data):
        root = BeautifulSoup(xml_data)
        for xml_message in root.find_all('msg'):
            try:
                yield {
                    'time': xml_message.time.text,
                    'power': int(xml_message.ch1.watts.text),
                    'temperature': float(xml_message.tmpr.text)
                }
            except( ValueError, TypeError, AttributeError):
                # badly formatted/empty entry (hist?), we just ignore it
                pass

class CC128LiveParser(CC128Parser):
    def parse_msg(self, xml_data):
        # Time stamp from the CC128 does not have the date and its time may not
        # be accurate. Since we are live, we know that this entry is from
        # "right now", so we can fix the time stamp. Also, we provide it in an
        # unambigous format: seconds since EPOCH.
        time_stamp = int(time.time())
        for entry in CC128Parser.parse_msg(self, xml_data):
            entry['time'] = time_stamp
            yield entry

if __name__ == '__main__':
    import sys
    file_name = None
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    if len(sys.argv) > 2:
        log_file_name = sys.argv[2]
    else:
        log_file_name = None

    if file_name is None or serial_tools.is_serial(file_name):
        data = serial_tools.open_cc128(file_name)
        parser = CC128LiveParser()
    else:
        data = file(file_name, "r")
        parser = CC128Parser();

    if log_file_name is not None:
        data = IteratorLogger(data, log_file_name)

    try:
        for line in data:
            for entry in parser.parse_msg(line):
                print entry
    except KeyboardInterrupt:
        print >> sys.stderr, "\nBye!"
