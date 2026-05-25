import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db


def db_import_from_file(id, path, date_begin, date_end, parse_format = "js"):
    if parse_format == "csv":
        parse_function = solarlog_parse.csv_data
    else:
        parse_function = solarlog_parse.js_data
    pv_data.date_range(path, date_begin, date_end, parse_function,
                       [filter.production], output_db.db_check, id=id)

if __name__ == "__main__":
    id = int(sys.argv[1])
    date_begin = sys.argv[2]
    date_end = sys.argv[3]
    if len(sys.argv) > 3 and sys.argv[4] == "csv":
        parse_format = "csv"
    else:
        parse_format = "js"
    db_import_from_file(id, date_begin, date_end, parse_format)
