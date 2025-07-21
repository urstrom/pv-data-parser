import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db

def pickle_create(id, date_begin, date_end, parse_function):
    pv_data.date_range(f"{config.path_base}/{id:02d}", date_begin, date_end, parse_function, [filter.production], output.pickle_write, id=id)

def db_import_from_pickle(id, date_begin, date_end):
   pv_data.date_range(f"{config.path_base}/{id:02}", date_begin, date_end, pv_data.unpickle, [filter.production, filter.deduplicate_zeros], output_db.db_check, id=id)

def db_import_from_file_via_pickle(id, date_begin, date_end, parse_format = "js"):
    if parse_format == "csv":
        parse_function = solarlog_parse.csv_data
    else:
        parse_function = solarlog_parse.js_data
    pickle_create(int(id), date_begin, date_end, parse_function)
    db_import_from_pickle(int(id), date_begin, date_end)

if __name__ == "__main__":
    id = int(sys.argv[1])
    date_begin = sys.argv[2]
    date_end = sys.argv[3]
    if len(sys.argv) > 3 and sys.argv[4] == "csv":
        parse_format = "csv"
    else:
        parse_format = "js"
    db_import_from_file_via_pickle(id, date_begin, date_end, parse_format)
