import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db, db_import_from_pickle,\
    db_import_from_pickle, urstrom

def db_import_from_pickle_urstrom_all(date_begin, date_end):
    for pv_system_id in range(1, urstrom.get_number_systems() + 1):
        parse_function = urstrom.get_parse_function(pv_system_id, date_begin, date_end)
        db_import_from_pickle.db_import_from_pickle(pv_system_id, date_begin, date_end, parse_function)

if __name__ == "__main__":
    db_import_from_pickle_urstrom_all(sys.argv[1], sys.argv[2])
