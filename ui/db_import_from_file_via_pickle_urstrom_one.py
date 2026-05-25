import sys, urstrom
import db_import_from_file_via_pickle

def db_import_from_file_via_pickle_urstrom_one(pv_system_id, date_begin, date_end):
    parse_function = urstrom.get_parse_function(pv_system_id, date_begin, date_end)
    db_import_from_file_via_pickle.db_import_from_file_via_pickle(pv_system_id, date_begin, date_end, parse_function)

if __name__ == "__main__":
    db_import_from_file_via_pickle_urstrom_one(int(sys.argv[1]), sys.argv[2], sys.argv[3])
