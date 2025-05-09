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
        "Each test flushes database state."
        try:
            pass
            print('\n', unittest.TestCase.id(self))
            # self.conn = psycopg2.connect("dbname='margin' user='checker' host='localhost' password='test'")
            # self.cur = self.conn.cursor()
        except:
            print("Cannot connect to the database.")

    def tearDown(self):
        pass
        # self.cur.close()
        # self.conn.close()

    def test_js_date_line(self):
        "No error shall be raised if check is performed on empty tables."
        solarlog_parse.js_data_line('[mi++]="01.03.25 11:25:00|6548;1670;1645;1663|5886;1562;1558"')

        pass
        #
        # self.assertEqual(d.get_newest_error_class(self.cur), None)

    def test_01_basevars(self):
        solarlog_parse.js_basevars("base_vars.js")

    def test_02_date_range_js(self):
        pv_data.date_range("", "2025-03-01", "2025-03-01", solarlog_parse.js_data,
[], output.data_print)

    def test_03_date_range_csv(self):
        pv_data.date_range("", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
[], output.data_print)

    def test_04_csv_filter_pickle(self):
        pv_data.date_range("", "2025-03-01", "2025-03-01", solarlog_parse.csv_data,
[filter.production], output.pickle_write, id=8)

    def test_05_js_filter_js(self):
        pv_data.date_range("", "2025-03-01", "2025-03-01", solarlog_parse.js_data,
[filter.production, filter.good_array], output.js_write, id=8)

    def test_06_db(self):
        pv_data.date_range("", "2025-03-01", "2025-03-01", pv_data.unpickle,
[filter.deduplicate_zeros], output_db.db_check, id=8)  #

"Failfast can be set to True to stop early to preserve DB state. Otherwise set to False."
if __name__ == "__main__":
    unittest.main(failfast = False)
