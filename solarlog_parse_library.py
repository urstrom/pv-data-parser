#!/usr/bin/python3

# Parse solarlog min*.js files
# ' https://www.photonensammler.de/wiki/doku.php?id=solarlog_datenformat'

import re
import datetime
import os
import sys
import pytz
import time
import csv
import pvsystem
import sys

"""
Filtering: good_value
Import: 
    parse_js_array: generic helper, returns array
    parse_basevars_file: return pv_system, sets inverter_is_production
    parse_min_line_js, parse_min_line_csv, returning two-dim result array
    csv_production(system_id, day, data_root_system, file_type, encoding, target)
    deduplicate_zeros: operating on result array
    parse_min_file_name_js, parse_min_file_name_csv (path, encoding, pv_system) 
    
Output:
    csv_write_header, csv_write_body -> produce legacy CSV for pandas, based on sparse mapping
    db_write_body, db_check_body -> check database outputs timedbsql
    db_influxdb -> old stuff for influxdb, not used
    solarlog_csv_export_write_body_result_only -> CSV export based on result
    csv_filter -> 
    
File-level: 
    parse_file: entire file-based parser
    db_refresh_solarlog_day: refreshes materialzed view 

"""

sep = ','  # output CVS separator

re_min_file = re.compile(r"^min(\d+)\.(js|csv)")
re_js_array = re.compile(r"^(.*?)\s*=\s*new\s+Array\((.*)\)\s*$")
re_js_array_name = re.compile(r"^([^\[]*)\s*(.*)$")
re_js_array_index = re.compile(r"^\[(\d+)]\s*(.*)$")
re_js_array_value = re.compile(r"^(\"([^\"]*)\"|([^),]+))[,)]?(.*)")
re_min = re.compile(r"^m\[mi\+\+]=\"(.*)\"\s*$")
re_is_temp = re.compile(r"^var\s+isTemp\s*=\s*true\s*$")
data_file_name = "data.csv"

file_handle = None
timezone = 'Europe/Brussels'


def good_value(val, context):
    val = int(val)
    if val < 0 or val > 1000000:
        print(f"Error: Context:{context}, Bad value {val}", file=sys.stderr)
        return False
    else:
        return True


def parse_js_array(lhs, rhs):
    """Parses javascript array, return a python array,
    consisting of variable name, list of indices, list of fields."""
    arr = []
    m = re_js_array_name.match(lhs)
    arr.append(m.group(1))
    lhs = m.group(2)
    ' create list of indices'
    arr.append([])
    while re_js_array_index.search(lhs):
        m = re_js_array_index.match(lhs)
        arr[1].append(m.group(1))
        lhs = m.group(2)
    'create list of values'
    arr.append([])
    while re_js_array_value.search(rhs):
        m = re_js_array_value.match(rhs)
        arr[2].append(m.group(2) if m.group(2) is not None else m.group(3))
        rhs = m.group(4)
    return arr


def parse_basevars_file(data_root):
    """Parses solarlog basevars file."""
    path = f"{data_root}/base_vars.js"
    pv_system = pvsystem.PvSystem("")
    inverter_is_production = []
    pv_system.has_temperature = 0

    if os.path.isfile(path):
        with open(path, encoding='utf8') as basevars_file:
            for line in basevars_file:
                line = line.strip()
                if re_js_array.search(line):
                    if line[0:9] == "var SLTyp":
                        pv_system.solarlog_type = line[14:]
                    m = re_js_array.match(line)
                    arr = parse_js_array(m.group(1), m.group(2))
                    'assumption is that WRInfo follow after each other in numerical order'
                    'e.g. WRInfo[0]=new Array("S0-IN","         1",20000,1,"Verbrauch",0,null,null,0,null,9,2,0,1000,null)'
                    if arr[0] == 'WRInfo' and len(arr[1]) == 1:
                        # catch-all if there is just a simple line 
                        print(f"inverter has initial line: {line}", file=sys.stderr)
                        'e.g. WRInfo[1]=new Array("PRO380-Mod 100A","1",15000,1,"Zähler",0,null,null,0,null,151,2,0,1000,null)'
                        if arr[2][4] in ["Batterie", "Zähler", "Varta Speicher", "Netzzähler", "PRO380-Mod CT"] or arr[2][11] != "0": # field 11 is documented in https://web.archive.org/web/20150417231430/http://photonensammler.homedns.org/wiki/doku.php?id=solarlog_datenformat
                            print(f"battery or consumption counter: {arr[2][4]}", file=sys.stderr)
                            inverter_is_production.append(0)
                        else:
                            inverter_is_production.append(1)
                        pv_inverter = pvsystem.PvInverter(arr[2][0], arr[2][2], arr[2][5], arr[2][11])
                        pv_system.pv_inverters.append(pv_inverter)
                        pv_string = pvsystem.PvTracker("default")
                        pv_system.pv_inverters[-1].pv_trackers = [pv_string]
                        pv_system.pv_inverters[-1].pv_trackers[0].dc = int(arr[2][8])
                    'e.g. WRInfo[1][6]=new Array("SO: String1,2,3","NW: String 4,5,6")'
                    if arr[0] == 'WRInfo' and len(arr[1]) == 2 and arr[1][1] == "6":
                        # usually overriding some of the previous branch 
                        print(f"inverter has x-6 line: {line}", file=sys.stderr)
                        pv_system.pv_inverters[-1].pv_trackers = []
                        for pv_string_name in arr[2]:
                            pv_string = pvsystem.PvTracker(pv_string_name)
                            pv_system.pv_inverters[-1].pv_trackers.append(pv_string)
                        pv_system.pv_inverters[-1].pv_trackers_no \
                            = len(pv_system.pv_inverters[-1].pv_trackers)
                    'e.g. WRInfo[1][9]=new Array(18423,18423)'
                    if arr[0] == 'WRInfo' and len(arr[1]) == 2 and arr[1][1] == "9":
                        print(f"inverter has x-9 line: {line}", file=sys.stderr)
                        counter = 0
                        for pv_string_dc in arr[2]:
                            pv_system.pv_inverters[-1].pv_trackers[counter].dc = int(pv_string_dc)
                            counter = counter + 1
                if re_is_temp.search(line):
                    print(f"pv system has temperature", file=sys.stderr)
                    pv_system.has_temperature = 1
        basevars_file.close()
    else:
        print("Error: File path not found: %s" % path, file=sys.stderr)
    pv_system.max_tracker_data = 3
    pv_system.set_inverter_is_production(inverter_is_production)
    if len(pv_system.pv_inverters)  != len(inverter_is_production):
        print("Inconsistent parsing in parse_basevars_file")
        sys.exit(-1)

    return pv_system

