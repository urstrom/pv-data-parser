#!/usr/bin/python3

import re, datetime, sys, os, pytz, csv, output_db, pickle

import config


# Parse solarlog min*.js files
# ' https://www.photonensammler.de/wiki/doku.php?id=solarlog_datenformat'

# date_range(path,date_begin, date_end, parse_function, output_function)
# csv_data(path, pv_system, output_function)
# csv_data_line(pv_system)
# js_basevars(path)
# js_data(path, pv_system)
# js_data_line(line)

def csv_data(path, pv_system, encoding='utf-8'):
    """Parses an entire CSV min file.
    Arguments:
        path: Path the CSV file.
        pv_system: Parameters of the PV system.
    Returns DDF (see README) or None if error is encountered"""

    path += ".csv"
    row_counter = 0
    solarlog_csv_version = '0'
    result = []
    header = {'path': path, 'offsets': []} # first row of header

    if os.path.isfile(path):
        print("csv_data: parsing " + path, file=sys.stderr)
        with open(path, newline='', encoding=encoding) as i:
            reader = csv.reader(i, delimiter=';', quotechar='\"')
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
                        field_counter = range(2, len(row))  # skip date and time at beginning
                        inverter_counter = -1 # set to -1 to allow incrementing when finding 'INV'
                        for i in field_counter:
                            if row[i] == 'INV':
                                inverter_counter += 1
                                header['offsets'].append({'dc': []})
                            if row[i] == 'Pac':  # German or English
                                header['offsets'][inverter_counter]['ac'] = i
                            if row[i][0:3] == 'Pdc':  # tracker DC
                                header['offsets'][inverter_counter]['dc'].append(i)
                        result.append(header)
                    row_counter += 1
                elif row_counter == 1 and solarlog_csv_version == '1.0.0':
                    # version 1.0.0 of Solar-Log CSV has header in 2nd row
                    print(row, file=sys.stderr)
                    pv_system['row_length'] = len(row)
                    header['line2'] = row
                    inverter_counter = -1
                    re_1_0_0_field = re.compile("(\\d)-(.*)")

                    field_counter = range(2, len(row))  # skip date and time at beginning
                    for i in field_counter:
                        m = re_1_0_0_field.match(row[i])
                        number = m.group(1)
                        if int(number) > inverter_counter:
                            inverter_counter = int(number)
                            header['offsets'].append({'dc': []})
                        if row[i][2:10] == 'CH_PAC-0' or row[i][2:15] == 'CH_PAC_CHARGE':
                            header['offsets'][inverter_counter]['ac'] = i
                        if row[i][2:8] == 'CH_PDC':
                            header['offsets'][inverter_counter]['dc'].append(i)
                    if header['offsets'] == []:
                        print(f"Parse error {pv_system['path']}: Invalid offsets, file=sys.stderr", file=sys.stderr)
                        return []
                    result.append(header)
                    row_counter += 1
                else:  # is data row
                    csv_data = csv_data_line(row, header['offsets'], pv_system)
                    if csv_data != []: # case where an error has occurred in csv_data_line
                        result.append(csv_data)
        return result

def csv_data_line(parts, offsets, pv_system):
    """Parses a line of CSV min file."""
    """Returns a list of dictionaries for each inverter"""
    if len(parts) == 0:
        print(f"Parse error csv_data_line {pv_system['id']} {pv_system['path']} (too little parts): ")
        return
    timestamp = pytz.timezone('Europe/Brussels').localize(
        datetime.datetime.strptime(parts[0] + " " + parts[1], "%d.%m.%y %H:%M:%S"))
    result = [timestamp]

    for inverter_counter in range(0, len(offsets)):
        # inv_type == 0 ==> is inverter, not counter
        inverter = {}
        # AC value for entire inverter
        try:
            if 'ac' not in offsets[inverter_counter]: # e.g. battery
                inverter['ac'] = None
            elif good_value(parts[offsets[inverter_counter]['ac']], str(parts)):
                inverter['ac'] = int(parts[offsets[inverter_counter]['ac']])
            else:
                print(f"Parse error csv_data_line id: {pv_system['id']} path: {pv_system['path']} {timestamp}: appending "
                    f"{inverter_counter}", file=sys.stderr)
                return []

        except ValueError:
            print(f"Parse error csv_data_line id: {pv_system['id']} path: {pv_system['path']} {timestamp} Exception: "
                  f"INV {str(inverter_counter)} of (total) {str(len(offsets))} "
                  f"position {offsets[inverter_counter]['inverter']} "
                  f"parts {str(parts)}"
                  f"result {str(result)} ",
                  file=sys.stderr)
            return []

        if len(offsets[inverter_counter]['dc']) != pv_system['inverters'][inverter_counter]['nr_trackers'] and 'tracker_mask' not in pv_system:
            print(f"Parse error csv_data_line pv_system id: {pv_system['id']} path: {pv_system['path']}, inverter {inverter_counter}, {timestamp}: "
                  f"tracker offsets {len(offsets[inverter_counter]['dc'])} != pv_trackers_no "
                  f"{pv_system['inverters'][inverter_counter]['nr_trackers']}", file=sys.stderr)
            return []

        inverter['dc'] = []
        for i in range(0, len(offsets[inverter_counter]['dc'])):
            if good_value(parts[offsets[inverter_counter]['dc'][i]], str(parts)):
                if 'tracker_mask' not in pv_system:
                    inverter['dc'].append(int(parts[offsets[inverter_counter]['dc'][i]]))
                else:
                    if i in pv_system['tracker_mask'][inverter_counter]:
                        inverter['dc'].append(int(parts[offsets[inverter_counter]['dc'][i]]))
            else:
                print(f"Parse error cvs_data_line id: {pv_system['id']} path: {pv_system['path']} {timestamp}: bad value", file=sys.stderr)
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
                    if varname == 'WRInfo' and len(idx_list) == 2 and idx_list[1] == "9":
                        pv_system['inverters'][-1]['trackers'] = list(map(int, values))
                if re_is_temp.search(line): #r"^var\s+isTemp\s*=\s*true\s*$"
                    pv_system['has_temperature'] = 1

            try:
                if pv_system['id'] in config.tracker_mask:
                    print("Applying tracker_mask for this system")
                    pv_system['tracker_mask'] = config.tracker_mask[pv_system['id']]
            except NameError: pass
            # print(pv_system, file=sys.stderr)
            return pv_system
    else:
        print("Error: File path not found: %s" % path, file=sys.stderr)
    # pv_system.max_tracker_data = 3


def js_data(path, pv_system, encoding='utf-8'):
    """Parses an entire Javascript min file.
    Arguments:
        path: Path the Javascript file (without extension).
        pv_system: Parameters of the PV system.
    Returns DDF (see README) or None if error is encountered"""

    path += ".js"
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
                        try:
                            inverter_input = data.pop(0)
                        except IndexError:
                            print(f"Inverter input too short {path}", file=sys.stderr)
                            return result
                        if pv_system['inverters'][inverter_counter]['is_production'] == 1:
                            inverter_output = {'ac': int(inverter_input.pop(0))}
                            nr_trackers = min(pv_system['inverters'][inverter_counter]['nr_trackers'], 3)
                            # 3-tracker limit in JS files
                            inverter_output['dc'] = []
                            for _ in range(nr_trackers):
                                inverter_output['dc'].append(int(inverter_input.pop(0)))
                            try:
                                inverter_output['sum'] = int(inverter_input.pop(0))
                            except Exception as e:
                                print(f"{path}: {e}")
                            inverter_output['voltage'] = []
                            try:
                                for _ in range(nr_trackers):
                                    inverter_output['voltage'].append(int(inverter_input.pop(0)))
                            except Exception as e:
                                print(f"{path}: {e}")
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

