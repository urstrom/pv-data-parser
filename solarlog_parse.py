#!/usr/bin/python3

import re, datetime, sys, os, pytz, csv, output_db, pickle

# Parse solarlog min*.js files
# ' https://www.photonensammler.de/wiki/doku.php?id=solarlog_datenformat'

# date_range(path,date_begin, date_end, parse_function, output_function)
# csv_data(path, pv_system, output_function)
# csv_data_line(pv_system)
# js_basevars(path)
# js_data(path, pv_system)
# js_data_line(line)

# pv_system
## row_length: length of CSV row
## inverters: list of inverters
### name, is_production, size, nr_trackers, type
## has_temperature

# handover format
## header: ['version', 'path', 'line1', 'line2', 'inverter_offsets', 'tracker_offsets']
## list of timestamps and inverter dictionaries, each inverter dictionary has 'ac', 'dc', 'sum', 'voltage', 'temperature'

def date_range(path, date_begin, date_end, parse_function, filter_functions, output_function, format="csv", encoding="utf-8", id=1):
    import config
    pv_system = js_basevars(os.path.join(path, "base_vars.js"), id)
    date_begin = datetime.datetime.strptime(date_begin, "%Y-%m-%d")
    date_end = datetime.datetime.strptime(date_end, "%Y-%m-%d")
    delta = date_end - date_begin
    for day in range(delta.days + 1):
        target_date = (date_begin + datetime.timedelta(days=day)).strftime("%y%m%d")
        print(type(output_db.db_write), file=sys.stderr)
        data = parse_function(os.path.join(path, f"min{target_date}.{format}"), pv_system)
        for f in filter_functions:
            data = f(data, pv_system)
        output_function(data, pv_system)

def unpickle(path, pv_system):
    with open(path + ".pickle", "rb") as file:
        return pickle.load(file)

def csv_data(path, pv_system, encoding='utf-8'):
    """Parses an entire CSV min file."""

    tracker_offsets = []
    inverter_offsets = []
    row_counter = 0
    solarlog_csv_version = '0'

    result = []
    header = {'path': path} # first row of header

    if os.path.isfile(path):
        print("csv_data: parsing " + path, file=sys.stderr)
        with open(path, newline='', encoding=encoding) as f:
            reader = csv.reader(f, delimiter=';', quotechar='\"')
            for row in reader:
                if row_counter == 0:
                    # is header row
                    print(row, file=sys.stderr)
                    if row[0][0:15] == '#SDS CSV V1.0.0':
                        solarlog_csv_version = '1.0.0'
                        header['version'] = 'csv1.0.0'
                        header['line1'] = row
                    # old Solar-Log CSV version has header in 1st row
                    else:
                        header['version'] = 'csv'
                        header['line1'] = row
                        print("Old CSV without version", file=sys.stderr)
                        field_counter = 0
                        for l in row:
                            # if l[0:3] == 'Pac':  # German or English
                            if l == 'Pac':  # German or English
                                inverter_offsets.append(field_counter)
                                print(f"adding inverter Pac {field_counter}", file=sys.stderr)
                                tracker_offsets.append([])
                            if l[0:3] == 'Pdc':  # tracker DC
                                tracker_offsets[-1].append(field_counter)
                            field_counter += 1
                        header['inverter_offsets'] = inverter_offsets
                        header['tracker_offsets'] = tracker_offsets
                        result.append(header)
                    row_counter += 1
                elif row_counter == 1 and solarlog_csv_version == '1.0.0':
                    # version 1.0.0 of Solar-Log CSV has header in 2nd row
                    print(row, file=sys.stderr)
                    pv_system['row_length'] = len(row)
                    header['line2'] = row
                    # 1st pass: identify trackers with DC devices attached #FIXME, may be obsolete
                    pdc_fields = {}  # AC devices connected to DC trackers
                    for l in row:
                        if l[1:8] == '-CH_PDC':
                            pdc_fields[l[0:1]] = 1
                    # 2nd pass; identify inverters
                    field_counter = 0  # keep track of field offsets
                    # mapping of inverter numbers to possibly lower count (if some "inverters") are something else
                    inverter_numbers = {}
                    inverter_counter = 0
                    for l in row:
                        if l[0:1] in pdc_fields or True: #FIXME
                            if l[1:10] == '-CH_PAC-0':
                                print(f"adding inverter {l[0:10]} {field_counter} ", file=sys.stderr, end='')
                                inverter_offsets.append(field_counter)
                                tracker_offsets.append([])
                                inverter_numbers[l[0:1]] = inverter_counter
                                inverter_counter += 1
                        field_counter += 1
                    # 3rd pass: identify trackers
                    field_counter = 0
                    for l in row:
                        if l[0:1] in pdc_fields:
                            if l[1:9] == '-CH_PDC-':
                                # print(f"adding tracker {l[0:10]} {field_counter}", file=sys.stderr)
                                # print(f"field counter{field_counter}, tracker_offsets{tracker_offsets}, ", file=sys.stderr)
                                tracker_offsets[inverter_numbers[l[0:1]]].append(field_counter)
                        field_counter += 1

                    row_counter += 1
                    print("Inverter offsets: ", inverter_offsets, file=sys.stderr)
                    print("Tracker offsets: ", tracker_offsets, file=sys.stderr)
                    header['inverter_offsets'] = inverter_offsets
                    header['tracker_offsets'] = tracker_offsets
                    result.append(header)
                    # result.append(["csv", inverter_offsets, tracker_offsets])
                    if inverter_offsets == [] or tracker_offsets == []:
                        print(f"Parse error {pv_system['path']}: Invalid offsets, file=sys.stderr", file=sys.stderr)
                        return []
                else:  # is data row
                    csv_data = csv_data_line(row, inverter_offsets, tracker_offsets, pv_system)
                    if csv_data != []: # case where an error has occurred in csv_data_line
                        result.append(csv_data)
        return result


def csv_data_line(parts, inverter_offsets, tracker_offsets, pv_system):
    """Parses a line of CSV min file."""
    """Returns a list of dictionaries for each inverter"""
    if len(parts) == 0:
        print(f"Parse error parse_min_line_csv {pv_system['path']} (too little parts): ")
        return
    timestamp = pytz.timezone('Europe/Brussels').localize(
        datetime.datetime.strptime(parts[0] + " " + parts[1], "%d.%m.%y %H:%M:%S"))
    result = [timestamp]

    for counter_inv in range(0, len(inverter_offsets)):
        'inv_type == 0 ==> is inverter, not counter'
        inverter = {}
        # AC value for entire inverter
        try:
            if good_value(parts[inverter_offsets[counter_inv]], str(parts)):
                inverter['ac'] = int(parts[inverter_offsets[counter_inv]])
            else:
                print(f"Parse error parse_min_line_csv {pv_system['path']} {timestamp}: appending "
                    f"{counter_inv}", file=sys.stderr)
                return []

        except ValueError:
            print(f"Parse error parse_min_line_csv {pv_system['path']} {timestamp} Exception: "
                  f"INV {str(counter_inv)} of (total) {str(len(inverter_offsets))} "
                  f"position {inverter_offsets[counter_inv]} "
                  f"parts {str(parts)}"
                  f"result {str(result)} ",
                  file=sys.stderr)
            return []

        if len(tracker_offsets[counter_inv]) != pv_system['inverters'][counter_inv]['nr_trackers']:
            print(f"Parse error parse_min_line_csv {pv_system['path']} {timestamp}: tracker offsets {len(tracker_offsets[counter_inv])} != pv_trackers_no "
                  f"{pv_system['pv_inverters'][counter_inv]['nr_trackers']}", file=sys.stderr)
            return []

        inverter['dc'] = []
        for i in range(0, len(tracker_offsets[counter_inv])):
            if good_value(parts[tracker_offsets[counter_inv][i]], str(parts)):
                inverter['dc'].append(int(parts[tracker_offsets[counter_inv][i]]))
            else:
                print(f"Parse error parse_min_line_csv {pv_system['path']} {timestamp}: bad value", file=sys.stderr)
                return []
        result.append(inverter)
    return result


def js_basevars(path, id=1):
    """Parses solarlog basevars file."""

    re_js_array = re.compile(r"^(.*?)\s*=\s*new\s+Array\((.*)\)\s*$")
    re_is_temp = re.compile(r"^var\s+isTemp\s*=\s*true\s*$")
    re_js_array_name = re.compile(r"^([^\[]*)\s*(.*)$")
    re_js_array_index = re.compile(r"^\[(\d+)]\s*(.*)$")
    re_js_array_value = re.compile(r"^(\"([^\"]*)\"|([^),]+))[,)]?(.*)")

    def parse_js_array(line):
        """Parses javascript array as string, return a python array.
        Args:
            line: line containing javascript array, e.g. "WRInfo[0][7] = (1, 2, 1, 2)"
        Returns:
            Tuple with (1) variable name, (2) list of indices, (3) list of fields.
            For the example the return value is ("WRInfo", [0,7], [1,2,1,2])
        """
        m = re_js_array.match(line) # r"^(.*?)\s*=\s*new\s+Array\((.*)\)\s*$"
        (lhs, rhs) = (m.group(1), m.group(2))
        m = re_js_array_name.match(lhs) # r"^([^\[]*)\s*(.*)$"
        tuple = (m.group(1), [], [])
        brackets = m.group(2)
        while re_js_array_index.search(brackets):
            # create list of indices
            m = re_js_array_index.match(brackets) #"^\[(\d+)]\s*(.*)$"
            tuple[1].append(m.group(1))
            brackets = m.group(2)
        while re_js_array_value.search(rhs): # r"^(\"([^\"]*)\"|([^),]+))[,)]?(.*)"
            # create list of values
            m = re_js_array_value.match(rhs)
            tuple[2].append(m.group(2) if m.group(2) is not None else m.group(3))
            rhs = m.group(4)
        return tuple

    if os.path.isfile(path):

        # WRInfo[0]=new Array("SUN2000-30KTL-M","0",30600,1,"WR 3",4,null,null,30000,null,232,0,1,1000,null)
        # WRInfo[0][6]=new Array("URD Str 37 SO","URD Str 38 NW","URD Str 39 SO","URD Str 40 NW")
        # WRInfo[0][7]=new Array(1,2,1,2)
        # WRInfo[0][9]=new Array(7650,7650,7650,7650)
        # WRInfo[0][16]=1
        # WRInfo[0][17]=1

        with open(path, encoding='utf8') as basevars_file:
            pv_system = {'inverters': [], 'has_temperature': 0, 'path': path, 'id': id }
            for line in basevars_file:
                # assumption is that WRInfo follow after each other in sequential order
                line = line.strip()
                if re_js_array.match(line):
                    (varname, idx_list, values) = parse_js_array(line)
                    # line for inverter general info, only one index
                    # WRInfo[0] = new Array("SUN2000-30KTL-M", "0", 30600, 1, "WR 3", 4, null, null, 30000, null, 232, 0, 1, 1000, null)
                    if varname == 'WRInfo' and len(idx_list) == 1:
                        if values[4] in ["Batterie", "Zähler", "Varta Speicher", "Netzzähler", "PRO380-Mod CT"] or \
                            values[11] != "0":  # field 11 is documented in https://web.archive.org/web/20150417231430/http://photonensammler.homedns.org/wiki/doku.php?id=solarlog_datenformat
                            inverter_is_production = 0
                        else:
                            inverter_is_production = 1
                        pv_system['inverters'].append({'name': values[0], 'is_production': inverter_is_production,
                            'size': int(values[2]), 'nr_trackers': int(values[5]), 'type': int(values[11])})
                    # line for trackers
                    # e.g. WRInfo[1][9]=new Array(18423,18423)
                    if  varname == 'WRInfo' and len(idx_list) == 2 and idx_list[1] == "9":
                        pv_system['inverters'][-1]['trackers'] = list(map(int, values))
                if re_is_temp.search(line): #r"^var\s+isTemp\s*=\s*true\s*$"
                    pv_system['has_temperature'] = 1
            print(pv_system, file=sys.stderr)
            return pv_system
    else:
        print("Error: File path not found: %s" % path, file=sys.stderr)
    # pv_system.max_tracker_data = 3


def js_data(path, pv_system, encoding='utf-8'):
    """Parses an entire javascript min file.
    Returns: list of timestamp and dictionaries, where each dictionary represents an inverter"""
    re_min = re.compile(r"^m\[mi\+\+]=\"(.*)\"\s*$")
    result = [{'version': 'js', 'path': path}]
    if os.path.isfile(path):
        print(f"parsing (js_data) minfile {path}\n", file=sys.stderr)
        with open(path, "rb") as min_file:
            for line in min_file.readlines():
                try:
                    line = line.decode(encoding)
                except ValueError:
                    print(f"Parse error {pv_system['id']} {path}: no match " + encoding, file=sys.stderr)
                    continue
                if re_min.search(line): # cut off at position
                    (timestamp, data) = js_data_line(line)
                    line_result = [timestamp]

                    for inverter_counter in range(len(pv_system['inverters'])):
                        if pv_system['inverters'][inverter_counter]['is_production'] == 1:
                            inverter_input = data.pop(0)
                            inverter_output = {'ac': int(inverter_input.pop(0))}
                            nr_trackers = min(pv_system['inverters'][inverter_counter]['nr_trackers'], 3)
                            # 3-tracker limit in JS files
                            inverter_output['dc'] = []
                            for _ in range(nr_trackers):
                                inverter_output['dc'].append(int(inverter_input.pop(0)))
                            inverter_output['sum'] = int(inverter_input.pop(0))
                            inverter_output['voltage'] = []
                            for _ in range(nr_trackers):
                                inverter_output['voltage'].append(int(inverter_input.pop(0)))
                            inverter_output['temperature'] = 0 # skip for data protection data.pop(0)
                        else: # is not a production counter, just insert 0ed data for data protection
                            inverter_output = {'ac':0, 'dc':[0,0]}
                        line_result.append(inverter_output)
                else:
                    print(f"Parse error: no match {pv_system['id']} {path}: " + line, file=sys.stderr)
                result.append(line_result)
    return result

def js_data_line(line):
    """Parses a line of javascript min file.
    Returns: Timestamp and list of raw fields."""
    line = line.strip()[:-1]
    fragments = line.split("|")
    time_string = fragments.pop(0)[9:]
    timestamp = pytz.timezone('Europe/Brussels').localize(datetime.datetime.strptime(time_string, "%d.%m.%y %H:%M:%S"))
    data = []
    for fragment in fragments:
        data += [fragment.split(";")]
    return (timestamp, data)

def good_value(val, context):
    val = int(val)
    if val < 0 or val > 1000000:
        print(f"Error: Context:{context}, Bad value {val}", file=sys.stderr)
        return False
    else:
        return True

