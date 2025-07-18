import sys, os, datetime, pickle, pathlib
import pv_data, filter, output_db, config, pickle

def db_import_from_pickle(id, date_begin, date_end):
   pv_data.date_range(f"{config.path_base}/{id:02}", date_begin, date_end, pv_data.unpickle, [filter.production, filter.deduplicate_zeros], output_db.db_check, id=id)

db_import_from_pickle(1, date_begin, date_end)
