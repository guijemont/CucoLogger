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

class CC128FileParser(object):
    class ParseError(Exception):
        pass

    def __init__(self, xml_file, log_file_name=None):
        if log_file_name is not None:
            self._file = IteratorLogger(xml_file, log_file_name)
        else:
            self._file = xml_file

    def __iter__(self):
        # This makes the assumption that there is a <msg> entry per line.
        for xml_data in self._file:
            for entry in self._parse_msg(xml_data):
                yield entry

    def _parse_msg(self, xml_data):
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

class CC128LiveParser(CC128FileParser):
    def __init__(self, serial_port=None, **kwargs):
        connection = serial_tools.open_cc128(serial_port)
        CC128FileParser.__init__(self, connection, **kwargs)

    def __iter__(self):
        # when parsing live, we might  want to stop with a KeyboardInterrupt
        try:
            for entry in CC128FileParser.__iter__(self):
                yield entry
        except KeyboardInterrupt:
            print >> sys.stderr, "\nLive parsing got interrupted, returning"

    def _parse_msg(self, xml_data):
        # Time stamp from the CC128 does not have the date and its time may not
        # be accurate. Since we are live, we know that this entry is from
        # "right now", so we can fix the time stamp.
        time_stamp = time.strftime("%F %T")
        for entry in CC128FileParser._parse_msg(self, xml_data):
            entry['time'] = time_stamp
            yield entry

def CC128Parser(file_name, **kwargs):
    if file_name is None or serial_tools.is_serial(file_name):
        return CC128LiveParser(file_name, **kwargs)
    else:
        return CC128FileParser(file(file_name), **kwargs)

if __name__ == '__main__':
    import sys
    file_name = None
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    if len(sys.argv) > 2:
        log_file_name = sys.argv[2]
    else:
        log_file_name = None
    for entry in CC128Parser(file_name, log_file_name=log_file_name):
        print entry
