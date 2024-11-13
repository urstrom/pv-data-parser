import sys
import datetime
import config
import parse.solarlog_parse

def parse_range_urstrom_one(date_begin, date_end, target, pv_system):
    encoding = "utf-8"
    # no Solarlog data at UrStrom
    if pv_system == 2 or pv_system == 3:
        return
    # if pv_system != 14:
    #   return
    file_type = "js"
    # CSV data
    if pv_system == 13 or pv_system == 16 or pv_system == 17 or pv_system == 18 or pv_system == 19 or pv_system == 20:
        file_type = "csv"
    # CSV data, format 1.0, ISO-8859-1
    # HBL if pv_system == 16 or pv_system == 17:
    #    encoding = "iso-8859-1"
    system_short = ("%02d" % pv_system)
    system_long = ("10%02d" % pv_system)
    print(f"\n\nSystem {system_long}", file=sys.stderr)
    sys.stderr.flush()
    parse.solarlog_parse.parse_file_time_range(system_short, date_begin, date_end,  file_type,
                            encoding, target)

def parse_range_urstrom_all(date_begin, date_end, target):
    for pv_system in range(1, 21):  #NOFIXME
        parse_range_urstrom_one(date_begin, date_end, target, pv_system)

def parse_range_urstrom_all(date_begin, date_end, target):
    for pv_system in range(1, 21):  #NOFIXME
        parse_range_urstrom_one(date_begin, date_end, target, pv_system)


if __name__ == "__main__":
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
