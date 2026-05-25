#!/usr/bin/python3

"""Test cases and derived requirements.
."""


# import psycopg2 # standard Python to PostgreSQL interface
import unittest # standard Python unit testing framework
import pv_data, solarlog_parse, filter, output, output_db

class TestPvData(unittest.TestCase):

    conn = None
    cur = None


    def __init__(self, *args, **kwargs):
        super(TestPvData, self).__init__(*args, **kwargs)

    def setUp(self):
        """Each test flushes database state."""
        try:
            pass
            print('\n', unittest.TestCase.id(self))
            # self.conn = psycopg2.connect("dbname='xxx' user='xxx' host='localhost' password='test'")
            # self.cur = self.conn.cursor()
        except:
            print("Cannot connect to the database.")

    def tearDown(self):
        pass
        # self.cur.close()
        # self.conn.close()

    def test_00_js_date_line(self):
        """No error shall be raised if check is performed on empty tables."""
        solarlog_parse.js_data_line('[mi++]="01.03.25 11:25:00|6548;1670;1645;1663|5886;1562;1558"')

    def test_01_basevars(self):
        solarlog_parse.js_basevars("test/base_vars.js")

# Data parsing

    def test_02_date_range_js(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.js_data,
[], output.data_print, id=8)

    def test_03_date_range_csv(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
[], output.data_print, id=8)

# Pickle

    def test_04_csv_filter_pickle(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
[filter.production], output.pickle_write, id=8)

# Time filter test (filter for deletion of duplicated values)

    def test_04_time_filter(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
                    [filter.production, filter.time_filter], output.data_print, id=8)

# Output: Javascript

    def test_05_js_filter_js(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.js_data,
[filter.production, filter.good_array], output.js_write, id=8)

# Output: Pickle to DB

    def test_06_db_from_pickle(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", pv_data.unpickle,
[filter.production, filter.deduplicate_zeros], output_db.db_check, id=8)  #

# Output: CSV to DB

    def test_07_db_from_csv(self):
        pv_data.date_range("test", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
[filter.production, filter.deduplicate_zeros], output_db.db_check, id=8)  #


"Failfast can be set to True to stop early to preserve DB state. Otherwise set to False."
if __name__ == "__main__":
    unittest.main(failfast = True)
