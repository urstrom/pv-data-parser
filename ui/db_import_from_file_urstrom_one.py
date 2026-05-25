import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db, db_import_from_file
import db_import_from_file_via_pickle

def db_import_from_file_urstrom_one(pv_system_id, date_begin, date_end):
    encoding = "utf-8"
    # no Solarlog data at UrStrom
    if pv_system_id in [2,3,23,24,25,26,28,29,30]:
        return
    parse_format = "js"
    # CSV data
    if pv_system_id in (13, 14, 16, 17, 18, 19, 20, 21, 22, 31):
        parse_format = "csv"
    # CSV data, format 1.0, ISO-8859-1
    # HBL if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    db_import_from_file.db_import_from_file(pv_system_id, date_begin, date_end, parse_format)

if __name__ == "__main__":
    db_import_from_file_urstrom_one(int(sys.argv[1]), sys.argv[2], sys.argv[3])
