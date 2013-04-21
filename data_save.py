import os, sys, time, bz2

import rrdtool

from parser import DataPoint

class DataSaver(object):
    def update(self, data_point):
        raise NotImplementedError()

    def close(self):
        pass


class RrdDataSaver(DataSaver):
    POWER_FILE = 'power.rrd'
    TEMPERATURE_FILE = 'temperature.rrd'

    SAMPLING_RESOLUTION = 6 # in seconds

    TEMPERATURE_DS = "DS:temperature:GAUGE:%d:-50:70" % SAMPLING_RESOLUTION
    TEMPERATURE_RRAS = (
            # keep everything for 24 hours (86400 seconds)
            "RRA:AVERAGE:0.5:1:%d" % (86400/SAMPLING_RESOLUTION),
            # keep one per 10 minutes for the week (one sample per 600 seconds,
            # 6 samples per hour)
            "RRA:AVERAGE:0.5:%d:%d" % (600/SAMPLING_RESOLUTION, 6*24*7),
            # keep one per hour for the last 10 years (one sample per 3600 seconds, 24
            # samples per day)
            "RRA:AVERAGE:0.5:%d:%d" % (3600/SAMPLING_RESOLUTION, 24*366*10)
            )

    POWER_DS = "DS:power:GAUGE:%d:0:U" % SAMPLING_RESOLUTION
    POWER_RRAS = (
            # keep everything for 90 days
            "RRA:AVERAGE:0.5:1:%d" % ((90 * 86400)/SAMPLING_RESOLUTION),
            # keep average per 10 minutes (6 per hour) for the last 10 years
            "RRA:AVERAGE:0.5:%d:%d" % (600/SAMPLING_RESOLUTION, 6*24*366*10)
            )

    def __init__(self, directory):
        self._dir = os.path.abspath(directory)
        self._power_file = os.path.join(self._dir, self.POWER_FILE)
        self._temperature_file = os.path.join(self._dir, self.TEMPERATURE_FILE)

        have_power_file = os.path.exists(self._power_file)
        have_temperature_file = os.path.exists(self._temperature_file)

        if not (have_power_file or have_temperature_file):
            self._created = False
        else:
            assert(have_power_file and have_temperature_file)
            self._created = True

    def _create_rrd_files(self, start_time):
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)
        assert(os.path.isdir(self._dir))

        print "Creating rrd files in", self._dir

        rrdtool.create(self._temperature_file,
                "--start", str(start_time),
                "--step", str(self.SAMPLING_RESOLUTION),
                "--no-overwrite",
                self.TEMPERATURE_DS,
                *self.TEMPERATURE_RRAS
                )
        rrdtool.create(self._power_file,
                "--start", str(start_time),
                "--step", str(self.SAMPLING_RESOLUTION),
                "--no-overwrite",
                self.POWER_DS,
                *self.POWER_RRAS
                )
    def update(self, data_point):
        # FIXME: use cache daemon (or have shell script for that?)
        assert(isinstance(data_point.time, int))

        if not self._created:
            self._create_rrd_files(data_point.time - 10)
            self._created = True

        rrdtool.update(self._temperature_file,
                "%d:%.1f" % (data_point.time, data_point.temperature))

        rrdtool.update(self._power_file,
                "%d:%d" % (data_point.time, data_point.power))

class CsvDataSaver(DataSaver):
    FILE_NAME_TEMPLATE = "power.%Y-%m-%d.csv"
    def __init__(self, directory, compress=False):
        self._directory = os.path.abspath(directory)
        self._file = None
        self._file_path = None
        self._compress = compress

        if not os.path.isdir(directory):
            os.makedirs(directory)

    def _make_file_path(self):
        file_path_template = os.path.join(self._directory, self.FILE_NAME_TEMPLATE)
        return time.strftime(file_path_template)

    def _should_rotate(self):
        return self._file_path != self._make_file_path()

    def _compress_file(self, path):
        compressed_path = path + '.bz2'
        print >> sys.stderr, "Compressing %s to %s" % (path, compressed_path)
        CHUNK_SIZE = 1024*1024
        original = open(path)
        destination = bz2.BZ2File(compressed_path, "w")
        while True:
            data = original.read(CHUNK_SIZE)
            if not data:
                break
            destination.write(data)
        original.close()
        destination.close()
        os.remove(path)

    def _uncompress_file(self, source, target):
        print >> sys.stderr, "Decompressing %s to %s" % (source, target)
        CHUNK_SIZE = 1024*1024
        original = bz2.BZ2File(source, "r")
        destination = open(target, "a")
        while True:
            data = original.read(CHUNK_SIZE)
            if not data:
                break
            destination.write(data)
        original.close()
        destination.close()
        os.remove(source)

    def _rotate(self):
        self.close()
        self._file_path = self._make_file_path()
        if os.path.exists (self._file_path + '.bz2'):
            self._uncompress_file(self._file_path + '.bz2', self._file_path)
        print >> sys.stderr, "Rotating: now outputting to file %s" % self._file_path
        self._file = open(self._file_path, "a")

    def close(self):
        if self._file:
            self._file.close()
            if self._compress:
                self._compress_file(self._file_path)
        self._file = None
        self._file_path = None

    def update(self, data_point):
        if self._should_rotate():
            self._rotate()
        print >> self._file, data_point.to_csv()

    def __delete__(self):
        self.close()

if __name__ == '__main__':
    import sys
    import parser, serial_tools
    saver = RrdDataSaver(sys.argv[1])
    if len(sys.argv) > 2: # CSV file as parameter
        source = file(sys.argv[2], "r")
        _parser = parser.CSVParser()
    else: # live data
        source = serial_tools.open_cc128()
        _parser = parser.CC128LiveParser()

    try:
        for line in source:
            for data_point in _parser.parse_msg(line):
                saver.update(data_point)
    except KeyboardInterrupt:
        print >> sys.stderr, "\nBye!"
        saver.close()
