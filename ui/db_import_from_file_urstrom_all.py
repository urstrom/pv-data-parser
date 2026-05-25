import sys, config
import db_import_from_file, urstrom

def db_import_from_file_urstrom_all(date_begin, date_end):
    for pv_system_id in range(1, urstrom.get_number_systems() + 1):
        parse_function = urstrom.get_parse_function(pv_system_id, date_begin, date_end)
        if parse_function is not None:
            db_import_from_file.db_import_from_file(pv_system_id, f"{config.path_data_raw}{pv_system_id:02}",
                date_begin, date_end, parse_function)

if __name__ == "__main__":
    db_import_from_file_urstrom_all(sys.argv[1], sys.argv[2])
