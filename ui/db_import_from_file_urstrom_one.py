import sys, urstrom
import pv_data, config, solarlog_parse, filter, output, output_db, db_import_from_file

def db_import_from_file_urstrom_one(pv_system_id, date_begin, date_end):
    parse_function = urstrom.get_parse_function(pv_system_id, date_begin, date_end)
    db_import_from_file.db_import_from_file(pv_system_id, f"{config.path_data_raw}{pv_system_id:02}", date_begin, date_end, parse_function)

if __name__ == "__main__":
    db_import_from_file_urstrom_one(int(sys.argv[1]), sys.argv[2], sys.argv[3])
