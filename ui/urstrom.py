import solarlog_parse

def get_number_systems():
    return 31

def get_parse_function(pv_system_id, date_begin, date_end):
    # encoding = "utf-8"
    # CSV data, format 1.0, ISO-8859-1
    # HBL previously: if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    # no Solarlog data at UrStrom
    if pv_system_id in (2, 3, 23, 24, 25, 26, 28, 29, 30):
        parse_function = None
    elif pv_system_id in (13, 14, 16, 17, 18, 19, 20, 21, 22, 31):
        parse_function = solarlog_parse.csv_data
    else:
        parse_function = solarlog_parse.js_data

    return parse_function