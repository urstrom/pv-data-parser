import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db, db_import_from_pickle
import db_import_from_file_via_pickle

def db_import_from_file_via_pickle_urstrom_one(pv_system_id, date_begin, date_end):
    encoding = "utf-8"
    # no Solarlog data at UrStrom
    if pv_system_id == 2 or pv_system_id == 3 or (pv_system_id > 22 and pv_system_id < 31):
        return
    # if pv_system != 14:
    #   return
    parse_format = "js"
    # CSV data
    if pv_system_id == 13 or pv_system_id == 16 or pv_system_id == 17 or pv_system_id == 19 or pv_system_id == 20:
        parse_format = "csv"
    # CSV data, format 1.0, ISO-8859-1
    # HBL if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    db_import_from_file_via_pickle.db_import_from_file_via_pickle(pv_system_id, date_begin, date_end, parse_format)

if __name__ == "__main__":
    db_import_from_file_via_pickle_urstrom_one(int(sys.argv[1]), sys.argv[2], sys.argv[3])