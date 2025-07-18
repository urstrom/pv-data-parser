import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output

define pickle_create(id, date_begin, date_end): 
    pv_data.date_range(f"{config.path_base}/{id:02d}", date_begin, date_end, solarlog_parse.js_data, [filter.production], output.pickle_write, id=id)

pickle_create(id, date_begin, date_end)
