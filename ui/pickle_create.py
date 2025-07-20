import sys, os, datetime, pickle
import pv_data, config, solarlog_parse, filter, output

def pickle_create(id, date_begin, date_end):
    pv_data.date_range(f"{config.path_base}/{id:02d}",
                       date_begin, date_end,
                       solarlog_parse.js_data, [filter.production], output.pickle_write, id=id)

if __name__ == "__main__":
    pickle_create(int(sys.argv[1]), sys.argv[2], sys.argv[3])
