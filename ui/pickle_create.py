import sys, os, datetime, pickle
import pv_data, config, solarlog_parse, filter, output

def pickle_create(id, date_begin, date_end):
    pv_data.date_range(f"{config.path_base}/{id:02d}",
                       date_begin, date_end,
                       solarlog_parse.js_data, [filter.production], output.pickle_write, id=id)

pickle_create(17, "2024-01-01", "2024-01-03")
