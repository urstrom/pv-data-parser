import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, output_db

def pickle_create(id, date_begin, date_end, parse_function):
    pv_data.date_range(f"{config.path_base}/{id:02d}", date_begin, date_end, parse_function, [filter.production], output.pickle_write, id=id)

def db_import_from_pickle(id, date_begin, date_end):
   pv_data.date_range(f"{config.path_base}/{id:02}", date_begin, date_end, pv_data.unpickle, [filter.production, filter.deduplicate_zeros], output_db.db_check, id=id)

id = int(sys.argv[1])
date_begin = sys.argv[2]
date_end = sys.argv[3]

pickle_create(id, date_begin, date_end, solarlog_parse.js_data)
db_import_from_pickle(id, date_begin, date_end)
