import re, config, solarlog_parse_library, sys, os
# regood = re.compile("var\\s+(Datum|Uhrzeit|Pac|aPdc|PacArr|PdcArr)\\s*=")
regood = re.compile("var\\s+(Datum|Uhrzeit|Pac)\\s*=")

def solarlog_parse_filter_day_cur(system_id):
    # def js_production_5min(system_id, day, data_root_system, file_type, encoding, pv_system):
    pv_system = solarlog_parse_library.parse_basevars_file(f"{config.path_data_raw}/{system_id}")
    filter.js_production_5min(system_id, "min_day", f"{config.path_data_raw}/{system_id}", 'js', 'utf-8', pv_system)
    filter.js_production_5min(system_id, "days", f"{config.path_data_raw}/{system_id}", 'js', 'utf-8', pv_system)

def solarlog_parse_filter_min_cur(system_id):
    data_root_system = f"{config.path_data_raw}/{system_id}"
    pv_system = solarlog_parse_library.parse_basevars_file(data_root_system)
    path_in = f"{data_root_system}/min_cur.js"
    path_out = f"{config.path_data_raw}/{system_id}w/min_cur.js"

    if os.path.isfile(path_in):
        print(f"parsing file {path_in}\n", file=sys.stderr)
        input_file = open(path_in, "r")
        output_file = open(path_out, "w")
        lines = input_file.readlines()
        for line in lines:
            if regood.search(line):
                print(line, file=output_file, end="")
        input_file.close()
        print(f"closing output file {path_out}")
        output_file.close()



if __name__ == "__main__":
    for i in [1,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]:
        solarlog_parse_filter_day_cur("%02d" % i)
        solarlog_parse_filter_min_cur("%02d" % i)
