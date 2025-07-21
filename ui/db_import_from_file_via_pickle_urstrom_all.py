import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db, db_import_from_pickle,\
    db_import_from_file_via_pickle_urstrom_one

def db_import_from_file_via_pickle_urstrom_all(date_begin, date_end):
    for pv_system_id in range(1, 31):  #NOFIXME
        db_import_from_file_via_pickle_urstrom_one.db_import_from_file_via_pickle_urstrom_one(
            pv_system_id, date_begin, date_end)


if __name__ == "__main__":
    db_import_from_file_via_pickle_urstrom_all(sys.argv[1], sys.argv[2])