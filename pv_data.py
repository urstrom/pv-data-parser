import sys, os, datetime, pickle, pathlib
import config
import solarlog_parse, output_db, output, filter

def date_range(path, date_begin, date_end, parse_function, filter_functions, output_function,
               encoding="utf-8", id=1):
    """Arguments:
    path: files with data
    date_begin: date to begin with
    date_end: date to end with"""
    if not os.path.exists (os.path.abspath(path)):
        print(f"Path does not exist: {path}", file = sys.stderr)
        return
    pv_system = solarlog_parse.js_basevars(os.path.join(path, "base_vars.js"), id)
    date_begin = datetime.datetime.strptime(date_begin, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")
    delta = date_end - date_begin
    for day in range(delta.days + 1):
        target_date = (date_begin + datetime.timedelta(days=day)).strftime("%y%m%d")
        # print(type(output_db.db_write), file=sys.stderr)
        data = parse_function(os.path.join(path, f"min{target_date}"), pv_system)
        if data is not None:
            for f in filter_functions:
                data = f(data, pv_system)
            output_function(data, pv_system)

def unpickle(path, pv_system):
    dirname = os.path.dirname(path)
    filename = pathlib.Path(path).stem
    with open(os.path.join(dirname, "p", filename + ".pickle"), "rb") as file:
        return pickle.load(file)

def range_urstrom_one(path, date_begin, date_end, filter_functions, output_function,
               pv_system_id):
    encoding = "utf-8"
    # no Solarlog data at UrStrom
    if pv_system_id == 2 or pv_system_id == 3 or (pv_system_id > 22 and pv_system_id < 31):
        return
    # if pv_system != 14:
    #   return
    parse_function = solarlog_parse.js_data
    # CSV data
    if pv_system_id == 13 or pv_system_id == 16 or pv_system_id == 17 or pv_system_id == 19 or pv_system_id == 20:
        parse_function = solarlog_parse.csv_data
    # CSV data, format 1.0, ISO-8859-1
    # HBL if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    date_range(path, date_begin, date_end, parse_function, filter_functions, output_function,
               encoding, pv_system_id)

def range_urstrom_all(root, date_begin, date_end, filter_functions, output_function):
    for pv_system_id in range(1, 31):  #NOFIXME
        range_urstrom_one(os.path.join(root, "%02d" % pv_system_id), date_begin, date_end, filter_functions, output_function,
               pv_system_id)


if __name__ == "__main__":
    if True:
        range_urstrom_all("/home/hbl/u/comp/hint/fs/web/monitoring/anlagen/",
                          "2024-01-05", "2024-01-06", [filter.production, filter.deduplicate_zeros],
                          output.pickle_write)
    if False:
        date_range("/home/hbl/u/comp/hint/fs/web/monitoring/anlagen/13", "2016-03-01", "2025-04-01", solarlog_parse.csv_data,
                           [filter.production], output.pickle_write, format="csv", id=8)
    if False:
        print("name does not equal main")
        # parse_range_urstrom_one('2021-01-01', '2022-07-10', 'postgresql', 16)
        print(sys.argv[0])
        print(sys.argv[1])
        print(sys.argv[2])
        system_select = 0
        if len(sys.argv) > 3: # select particular system for debugging
           parse_range_urstrom_one(sys.argv[1], sys.argv[2], 'postgresql_check', int(sys.argv[3]))
        else:
            parse_range_urstrom_all(sys.argv[1], sys.argv[2], 'postgresql_check')
            parse.solarlog_parse_database.db_refresh_solarlog_day()
