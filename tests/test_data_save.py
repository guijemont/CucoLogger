import unittest
import tempfile, shutil, time, os

from data_save import CsvDataSaver
from parser import DataPoint

class FastRotatingCsvDataSaver(CsvDataSaver):
    FILE_NAME_TEMPLATE = "power.%Y-%m-%d-%H-%M-%S.csv"

class CsvTest(unittest.TestCase):
    def setUp(self):
        self._tempdir = tempfile.mkdtemp()
        print "tempdir:", self._tempdir

    def tearDown(self):
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
        

if __name__ == '__main__':
    unittest.main()

