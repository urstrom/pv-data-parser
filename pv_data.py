import sys, os, datetime, pickle, pathlib
import config
import solarlog_parse, output_db, output, filter

def date_range(path, date_begin, date_end, parse_function, filter_functions, output_function,
               format="csv", encoding="utf-8", id=1):
    """Arguments:
    path: files with data
    date_begin: date to begin with
    date_end: date to end with"""
    pv_system = solarlog_parse.js_basevars(os.path.join(path, "base_vars.js"), id)
    date_begin = datetime.datetime.strptime(date_begin, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")
    delta = date_end - date_begin
    for day in range(delta.days + 1):
        target_date = (date_begin + datetime.timedelta(days=day)).strftime("%y%m%d")
        # print(type(output_db.db_write), file=sys.stderr)
        data = parse_function(os.path.join(path, f"min{target_date}.{format}"), pv_system)
        if data is not None:
            for f in filter_functions:
                data = f(data, pv_system)
            output_function(data, pv_system)

def unpickle(path, pv_system):
    dirname = os.path.dirname(path)
    filename = pathlib.Path(path).stem
    with open(os.path.join(dirname, "p", filename + ".pickle"), "rb") as file:
        return pickle.load(file)

def range_urstrom_one(date_begin, date_end, target, pv_system_id):
    encoding = "utf-8"
    # no Solarlog data at UrStrom
    if pv_system_id == 2 or pv_system_id == 3:
        return
    # if pv_system != 14:
    #   return
    file_type = "js"
    # CSV data
    if pv_system_id == 13 or pv_system_id == 16 or pv_system_id == 17 or pv_system_id == 18 or pv_system_id == 19 or pv_system_id == 20:
        file_type = "csv"
    # CSV data, format 1.0, ISO-8859-1
    # HBL if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    system_short = ("%02d" % pv_system_id)
    system_long = ("10%02d" % pv_system_id)
    print(f"\n\nSystem {system_long}", file=sys.stderr)
    sys.stderr.flush()
    date_range(system_short, date_begin, date_end,  file_type,
                            encoding, target)

def range_urstrom_all(date_begin, date_end, target):
    for pv_system in range(1, 21):  #NOFIXME
        parse_range_urstrom_one(date_begin, date_end, target, pv_system)


if __name__ == "__main__":
    if True:
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
