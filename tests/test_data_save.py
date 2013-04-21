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

import unittest
import tempfile, shutil, time, os, bz2

from data_save import CsvDataSaver
from parser import DataPoint

class FastRotatingCsvDataSaver(CsvDataSaver):
    FILE_NAME_TEMPLATE = "power.%Y-%m-%d-%H-%M-%S.csv"

class CsvTest(unittest.TestCase):
    def setUp(self):
        self._tempdir = tempfile.mkdtemp()
        print "tempdir:", self._tempdir

    def tearDown(self):
        print "cleaning", self._tempdir
        shutil.rmtree(self._tempdir)

    def _file_name_now(self):
        template = os.path.join(self._tempdir, FastRotatingCsvDataSaver.FILE_NAME_TEMPLATE)
        return time.strftime(template)

    def test_rotation(self):
        saver = FastRotatingCsvDataSaver(self._tempdir)
        point1 = DataPoint(time=int(time.time()), temperature=18.3, power=350)
        first_file_name = self._file_name_now()
        saver.update(point1)
        self.assertTrue(os.path.exists(first_file_name))
        self.assertEqual(os.path.abspath(saver._file.name), first_file_name)
        time.sleep(2)
        point2 = DataPoint(time=int(time.time()), temperature=18.5, power=420)
        second_file_name = self._file_name_now()
        saver.update(point2)
        self.assertTrue(os.path.exists(second_file_name))
        self.assertEqual(os.path.abspath(saver._file.name), second_file_name)

    def test_rotation_bz2(self):
        saver = FastRotatingCsvDataSaver(self._tempdir, compress=True)
        point1 = DataPoint(time=int(time.time()), temperature=18.3, power=350)
        first_file_name = self._file_name_now()
        saver.update(point1)
        self.assertTrue(os.path.exists(first_file_name))
        self.assertEqual(os.path.abspath(saver._file.name), first_file_name)

        time.sleep(2)

        point2 = DataPoint(time=int(time.time()), temperature=18.5, power=420)
        second_file_name = self._file_name_now()
        saver.update(point2)
        self.assertTrue(os.path.exists(second_file_name))
        self.assertFalse(os.path.exists(first_file_name))
        self.assertTrue(os.path.exists(first_file_name + '.bz2'))
        self.assertEqual(os.path.abspath(saver._file.name), second_file_name)

        saver.close()
        self.assertFalse(os.path.exists(second_file_name))
        self.assertTrue(os.path.exists(second_file_name + '.bz2'))


    def test_data(self):
        saver = CsvDataSaver(self._tempdir)
        template_path = os.path.join(self._tempdir, CsvDataSaver.FILE_NAME_TEMPLATE)
        file_path = time.strftime(template_path)

        point1 = DataPoint(time=int(time.time()), temperature=18.3, power=350)
        point2 = DataPoint(time=int(time.time()), temperature=18.5, power=420)
        saver.update(point1)
        saver.update(point2)
        del saver # should trigger a close() and therefore a flush

        save_file = open(file_path, "r")
        data = save_file.read()
        expected = "%s\n%s\n" % (point1.to_csv(), point2.to_csv())
        self.assertEqual(data, expected)

    def test_data_bz2(self):
        saver = CsvDataSaver(self._tempdir, compress=True)
        template_path = os.path.join(self._tempdir, CsvDataSaver.FILE_NAME_TEMPLATE)
        template_path += ".bz2"
        file_path = time.strftime(template_path)

        point1 = DataPoint(time=int(time.time()), temperature=18.3, power=350)
        point2 = DataPoint(time=int(time.time()), temperature=18.5, power=420)
        saver.update(point1)
        saver.update(point2)
        saver.close()

        save_file = bz2.BZ2File(file_path, "r")
        data = save_file.read()
        expected = "%s\n%s\n" % (point1.to_csv(), point2.to_csv())
        self.assertEqual(data, expected)

    def test_resume_bz2(self):
        saver = CsvDataSaver(self._tempdir, compress=True)
        template_path = os.path.join(self._tempdir, CsvDataSaver.FILE_NAME_TEMPLATE)
        template_path += ".bz2"
        file_path = time.strftime(template_path)

        point1 = DataPoint(time=int(time.time()), temperature=18.3, power=350)
        saver.update(point1)
        saver.close()
        del saver

        time.sleep(1)

        point2 = DataPoint(time=int(time.time()), temperature=18.5, power=420)
        saver = CsvDataSaver(self._tempdir, compress=True)
        saver.update(point2)
        saver.close()
        del saver

        save_file = bz2.BZ2File(file_path, "r")
        data = save_file.read()
        expected = "%s\n%s\n" % (point1.to_csv(), point2.to_csv())
        self.assertEqual(data, expected)

if __name__ == '__main__':
    unittest.main()

