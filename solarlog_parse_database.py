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
import solarlog_parse_library

def parse_min_line_js(line, pv_system):
    """Parses a line of javascript min file."""
    line = line.strip()
    inverter_inputs = line.split("|")
    time_string = inverter_inputs.pop(0)
    timestamp = pytz.timezone(solarlog_parse_library.timezone).localize(datetime.datetime.strptime(time_string, "%d.%m.%y %H:%M:%S"))
    result = [timestamp]
    inverter_counter = 0
    inverter_is_production = pv_system.get_inverter_is_production()

    if len(inverter_inputs) != len(inverter_is_production):
        print(
            f"Parse error parse_min_line_js {pv_system.id} {timestamp} min file data %d > basevars file system data %d"
            % (len(inverter_inputs), len(inverter_is_production)), file=sys.stderr)
        return []

    for inverter_input in inverter_inputs:
        if inverter_is_production[inverter_counter] != 1:
            continue
        values = inverter_input.split(";")
        if pv_system.pv_inverters[inverter_counter].inv_type == 0:
            'inv_type == 0 ==> is inverter, not counter'
            # AC value for entire inverter
            if solarlog_parse_library.good_value(values[0], f"L{line}"):
                result.append(values[0])
            else:
                print(f"Parse error parse_min_line_js {pv_system.id} {timestamp}: bad value (first value)", file=sys.stderr)
                return []
            # counter_trck + 1: first data column here is AC for the entire inverter, we only collect \
            #    DC for the strings 
            for counter_trck in range(0, pv_system.pv_inverters[inverter_counter].pv_trackers_no):
                if counter_trck < 3:  # only the first three trackers are recorded
                    if solarlog_parse_library.good_value(values[counter_trck + 1], f"L{line}"):
                        result.append(values[counter_trck + 1])
                    else:
                        print(f"Parse error {pv_system.id} {timestamp}: bad value", file=sys.stderr)
                        return []
        inverter_counter += 1

    return result


def parse_min_line_csv(parts, inverter_offsets, tracker_offsets, pv_system):
    """Parses a line of CSV min file."""
    #if len(inverter_offsets) < len(pv_system.pv_inverters):
    #    print(f"Error: inverters ({len(inverter_offsets)}) missing in CSV header where ({len(pv_system.pv_inverters)})" + str(parts), file=sys.stderr)
    #    return
    # print(parts)
    # print(inverter_offsets)
    if len(parts) == 0:
        print(f"Parse error parse_min_line_csv {pv_system.id} (too little parts): ")
        return
    timestamp = pytz.timezone(solarlog_parse_library.timezone).localize(
        datetime.datetime.strptime(parts[0] + " " + parts[1], "%d.%m.%y %H:%M:%S"))
    result = [timestamp]

    pv_inverter_num = pv_system.get_inverter_is_production_number()

    if len(inverter_offsets) != pv_inverter_num:
        print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp}: inverter offsets {len(inverter_offsets)} != pv_system.pv_inverters "
              f"{pv_inverter_num}", file=sys.stderr)
        return []

    for counter_inv in range(0, len(inverter_offsets)):
        if counter_inv >= pv_inverter_num:
            print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp}: min data {counter_inv} > system data"
                  f" {pv_inverter_num}", file=sys.stderr)
            return []
        if pv_system.pv_inverters[counter_inv].inv_type == 0:
            'inv_type == 0 ==> is inverter, not counter'
            # AC value for entire inverter

            try:
                if solarlog_parse_library.good_value(parts[inverter_offsets[counter_inv]], str(parts)):
                    result.append(parts[inverter_offsets[counter_inv]])
                else:
                    print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp}: appending "
                        f"{counter_inv}", file=sys.stderr)
                    return []

            except ValueError:
                print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp} Exception: "
                      f"INV {str(counter_inv)} of (total) {str(len(inverter_offsets))} "
                      f"position {inverter_offsets[counter_inv]} "
                      f"parts {str(parts)}"
                      f"result {str(result)} ",
                      file=sys.stderr)
                return []

            if len(tracker_offsets[counter_inv]) != pv_system.pv_inverters[counter_inv].pv_trackers_no:
                print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp}: tracker offsets {len(tracker_offsets[counter_inv])} != pv_trackers_no "
                      f"{pv_system.pv_inverters[counter_inv].pv_trackers_no}", file=sys.stderr)
                return []

            for i in range(0, len(tracker_offsets[counter_inv])):
                if solarlog_parse_library.good_value(parts[tracker_offsets[counter_inv][i]], str(parts)):
                    result.append(parts[tracker_offsets[counter_inv][i]])
                else:
                    print(f"Parse error parse_min_line_csv {pv_system.id} {timestamp}: bad value", file=sys.stderr)
                    return []
    return result


def deduplicate_zeros(input_table):
    """Deletes repetitions of lines that have all 0 value. One copy of all-zero line is kept at each boundary.
    Also keep lines where the interval to preceding line is not 5 minutes."""
    result = []
    if input_table is None:
        return result
    skip_mode = 0  # if skip_mode == 1, then are we in a region where we are skipping, because all values are zeros
    last_line_inserted = -1  # pointer to avoid inserting a line twice
    for i in range(len(input_table)):
        # line is empty, skip
        if input_table[i] is None or len(input_table[i]) == 0:
            continue
        # inspect whether all line values are zero
        this_line_is_nonzero = 0
        for j in range(1, len(input_table[i])):
            if input_table[i][j] != "0" and input_table[i][j] != 0:
                this_line_is_nonzero = 1
        # first and last line, always accept and continue
        if i == len(input_table) - 1 or i == 0:
            result.append(input_table[i])
            if this_line_is_nonzero == 0:
                skip_mode = 1  # relevant if first line is only zeros
            last_line_inserted = i
            continue
        # we are not in skip mode, hence we accept
        if skip_mode == 0:
            result.append(input_table[i])
            if this_line_is_nonzero == 0:
                skip_mode = 1  # enter skip mode
                last_line_inserted = i
        else:  # We are in skip mode, only accept if we found a line that is nonzero or a line following and empty line or a time delta that is not 300 seconds, but then we may have also to accept its predecessor.
            if this_line_is_nonzero == 1 or len(input_table[i - 1]) == 0 or 300 != (
                    input_table[i - 1][0] - input_table[i][0]).seconds:
                if i > last_line_inserted + 1:  # last line (zeros) has not been inserted yet
                    result.append(input_table[i - 1])  # so let's insert it
                result.append(input_table[i])
                last_line_inserted = i
                skip_mode = 0
    return result


def parse_min_file_name_js(path, encoding, pv_system):
    """Parses an entire javascript min file."""
    result = []
    if os.path.isfile(path):
        print(f"parsing (parse_min_file_name_js) minfile {path}\n", file=sys.stderr)
        with open(path, "rb") as min_file:
            for line in min_file:
                try:
                    line = line.decode(encoding)
                except ValueError:
                    print(f"Parse error {pv_system.id} {path}: no match " + encoding, file=sys.stderr)
                    continue
                if solarlog_parse_library.re_min.search(line):
                    m = solarlog_parse_library.re_min.match(line)
                    result.append(parse_min_line_js(m.group(1), pv_system))
                else:
                    print(f"Parse error: no match {pv_system.id} {path}: " + line, file=sys.stderr)
        min_file.close()
    return deduplicate_zeros(result)

def parse_min_file_name_csv(path, encoding, pv_system):
    """Parses an entire CSV min file."""

    tracker_offsets = []
    inverter_offsets = []
    row_counter = 0
    solarlog_csv_version = '0'

    result = []
    if os.path.isfile(path):
        print("parse_min_file_name_csv: parsing " + path, file=sys.stderr)
        with open(path, newline='', encoding=encoding) as f:
            reader = csv.reader(f, delimiter=';', quotechar='\"')
            for row in reader:
                if row_counter == 0:
                    # is header row
                    print(row, file=sys.stderr)
                    if row[0][0:15] == '#SDS CSV V1.0.0':
                        solarlog_csv_version = '1.0.0'
                        print(solarlog_csv_version, file=sys.stderr)
                    else:  # old Solar-Log CSV version has header in 1st row
                        print("Old CSV without version", file=sys.stderr)
                        field_counter = 0
                        for l in row:
                            # if l[0:3] == 'Pac':  # German or English
                            if l == 'Pac':  # German or English
                                inverter_offsets.append(field_counter)
                                print(f"added inverter Pac {field_counter}", file=sys.stderr)
                                tracker_offsets.append([])
                            if l[0:3] == 'Pdc':  # tracker DC
                                tracker_offsets[-1].append(field_counter)
                            field_counter += 1
                    row_counter += 1
                elif row_counter == 1 and solarlog_csv_version == '1.0.0':
                    # version 1.0.0 of Solar-Log CSV has header in 2nd row
                    print(row, file=sys.stderr)
                    # 1st pass: identify trackers with DC devices attached
                    pdc_fields = {} # AC devices connected to DC trackers
                    pv_system.set_row_length(len(row))
                    for l in row:
                        if l[1:8] == '-CH_PDC':
                            pdc_fields[l[0:1]] = 1
                    # 2nd pass; identify inverters
                    field_counter = 0 # keep track of field offsets
                    inverter_numbers = {} # mapping of inverter numbers to possibly lower count (if some "inverters") are something else
                    inverter_counter = 0
                    for l in row:
                        if l[0:1] in pdc_fields:
                            if l[1:10] == '-CH_PAC-0':
                                print(f"adding inverter {l[0:10]} {field_counter}", file=sys.stderr)
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
                    print("Inverter offsets: ", file=sys.stderr)
                    print(inverter_offsets, file=sys.stderr)
                    pv_system.set_inverter_offsets(inverter_offsets) # side-effect, use for regeneration of clean csv files
                    print("Tracker offsets: ", file=sys.stderr)
                    print(tracker_offsets, file=sys.stderr)
                    pv_system.set_tracker_offsets(tracker_offsets) # side-effect
                    if inverter_offsets == [] or tracker_offsets == []:
                        print(f"Parse error {pv_system.id} {path}: Invalid offsets, file=sys.stderr", file=sys.stderr)
                        return []
                else:  # is data row
                    result.append(parse_min_line_csv(row, inverter_offsets, tracker_offsets, pv_system))
        f.close()
    return deduplicate_zeros(result)



def db_write_body(data, pv_system, cur):
    mapping = pv_system.get_mapping()
    time_string = None
    for line in data:
        for j in range(len(line)):
            if j == 0:
                time_string = f"'{line[0].replace(tzinfo=None)}','{int(line[0].utcoffset().total_seconds())}'"
                # time_string = f"'{line[0].astimezone(pytz.utc).replace(tzinfo=None)}','{line[0].utcoffset().total_seconds()}'"
            else:
                try:
                    # print(f"insert into tracker_5min (system_id, tracker_id, timestamp, tz_offset, yield) values ('{pv_system.id}','{mapping[j - 1]}',{time_string},{line[j]})")
                    cur.execute(
                       f"insert into solarlog_5min (system_id, inverter_id, tracker_id, tracker_id_text, measurement_time, "
                       f"tz_offset, yield) values ('{pv_system.id}', 1 , {j},'{mapping[j-1]}', {time_string},{line[j]})")
                except TimeoutError as e:
                    print(f"Error: {e}")
                except Exception as e:
                    print(f"Error: {e}")


def db_check_body(data, pv_system, cur):
    mapping = pv_system.get_mapping()
    time_string = None
    for line in data:
        dt = datetime.datetime.now()
        for j in range(len(line)):
            if j == 0:
                time_string = f"'{line[0].replace(tzinfo=None)}'"
                time_string_insert = f"'{line[0].replace(tzinfo=None)}','{int(line[0].utcoffset().total_seconds())}'"
                # time_string = f"'{line[0].astimezone(pytz.utc).replace(tzinfo=None)}','{line[0].utcoffset().total_seconds()}'"
            else:
                try:
                    # print(f"insert into tracker_5min (system_id, tracker_id, timestamp, tz_offset, yield) values ('{pv_system.id}','{mapping[j - 1]}',{time_string},{line[j]})")
                    cur.execute(
                       f"select yield from solarlog_5min where system_id = '{pv_system.id}' and tracker_id = '{j}' and measurement_time = {time_string}")
                    fetched = cur.fetchone()
                    if fetched is None:
                        try:
                            # print(f"insert into tracker_5min (system_id, tracker_id, timestamp, tz_offset, yield) values ('{pv_system.id}','{mapping[j - 1]}',{time_string},{line[j]})")
                            cur.execute(
                                f"insert into solarlog_5min (system_id, inverter_id, tracker_id, tracker_id_text, measurement_time, "
                                f"tz_offset, yield, insertion_time) values ('{pv_system.id}', 1 , {j},'{mapping[j - 1]}', {time_string_insert},{line[j]},'{dt}')")
                        except Exception as e:
                            print(f"Error: {e}")
                    else:
                        fetched = fetched[0]
                        if int(fetched) != int(line[j]):
                            print(f"Fetched {fetched} Parsed {line[j]} System_id {pv_system.id} measurement_time {time_string}")
                            try:
                                # print(f"insert into tracker_5min (system_id, tracker_id, timestamp, tz_offset, yield) values ('{pv_system.id}','{mapping[j - 1]}',{time_string},{line[j]})")
                                dt = datetime.datetime.now()
                                cur.execute(f"insert into solarlog_5min_old select * from solarlog_5min where system_id = {pv_system.id} and tracker_id = '{j}' and measurement_time = {time_string};")
                                cur.execute(
                                    f"update solarlog_5min set yield = '{line[j]}', "
                                    f"insertion_time = '{dt}' where system_id = "
                                    f"'{pv_system.id}' and tracker_id = '{j}' and "
                                    f"measurement_time = {time_string}")
                            except Exception as e:
                                print(f"Error: {e} at updating {pv_system.id} and {time_string}")
                except Exception as e:
                    print(f"Error: {e}")

def db_check_body_bulk(data, pv_system, cur):
    mapping = pv_system.get_mapping()
    time_string = None
    cur.execute(
        f"select yield from solarlog_5min where system_id = '{pv_system.id}' "
        f"and measurement_time::date = '{datetime.date(data[0][0].strftime('%Y-%m-%d'))}'"
        f"order by measurement_time desc, tracker_id asc")
    fetched = cur.all()
    fetched_offset = 0

    for line in data:
        dt = datetime.datetime.now()
        for j in range(len(line)):
            if j == 0:
                time_string = f"'{line[0].replace(tzinfo=None)}'"
                time_string_insert = f"'{line[0].replace(tzinfo=None)}','{int(line[0].utcoffset().total_seconds())}'"
                # time_string = f"'{line[0].astimezone(pytz.utc).replace(tzinfo=None)}','{line[0].utcoffset().total_seconds()}'"
            else:
                if int(fetched[fetched_offset][0]) != int(line[fetched_offset]):
                    print(f"Fetched {fetched[fetched_offset][0]} at offset {fetched_offset} Parsed {line[j]} System_id {pv_system.id} measurement_time {time_string}")
                fetched_offset += 1



def influxdb_write_body_old(result, pv_system, client):
    mapping = pv_system.get_mapping()
    time_string = None
    json_string = "["
    counter = 0
    for line in result:
        json_string += f"""
        {{"measurement": "tracker_5min",
            "tags": {{"pv_system": "{pv_system.id}" }},
            "time": "{line[0]}",
            "fields": {{"""
        for j in range(1, len(line)):
            json_string += f'"{mapping[j - 1]}": {line[j]}'
            if j < len(line) - 1:
                json_string += ','
        json_string += "}}"
        counter += 1
        if counter < len(result):
            json_string += ","
    json_string += "]"
    # print(json_string)
    import json
    json_term = json.loads(json_string)
    # print(json_term)
    client.write_points(json_term)

def influxdb_write_body(result, pv_system, client):
    mapping = pv_system.get_mapping()
    time_string = None
    json_string = "["
    counter = 0
    for line in result:
        for j in range(1, len(line)):
            json_string += f"""
                    {{"measurement": "tracker_5min",
                        "tags": {{"pv_system": "{pv_system.id}", "device": "{mapping[j-1]}" }},
                        "time": "{line[0]}",
                        "fields": {{"power": {line[j]}}}}}"""
            counter += 1
            if counter < len(result) * (len(line) - 1):
                json_string += ","
    json_string += "]"
    # print(json_string)
    import json
    json_term = json.loads(json_string)
    # print(json_term)
    client.write_points(json_term)


def solarlog_csv_export_write_body_result_only(result, pv_system, data_root_system, file_type, outfile_name):
    for row in result:
        output = []
        for _ in range(pv_system.get_row_length()):
            output.append(0)
        ts = row.pop(0)
        output[0] = ts.strftime("%d.%m.%Y")
        output[1] = ts.strftime("%H:%M:%S")
        inverter_offsets = pv_system.get_inverter_offsets()
        tracker_offsets = pv_system.get_tracker_offsets()
        inverter_counter = 0
        for inverter in pv_system.pv_inverters:
            output[inverter_offsets[inverter_counter]] = row.pop(0)
            tracker_counter = 0
            for i in range(len(tracker_offsets[inverter_counter])):
                output[tracker_offsets[inverter_counter][tracker_counter]] = row.pop(0)
                tracker_counter += 1
            inverter_counter += 1
        for i in range(pv_system.get_row_length()):
            print(f"{output[i]};", end="")
        print("")

def influxdb2_write_body(result, pv_system, write_api):
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS

    mapping = pv_system.get_mapping()
    time_string = None
    counter = 0
    for line in result:
        for j in range(1, len(line)):
            p = Point("tm2").tag("device_id", mapping[j-1]).tag("pv_system", pv_system.id).field("yield", int(line[j])).time(line[0])
            write_api.write(bucket='hbl', org='hbl', record=p)


def analysis_raw(result, pv_system, f1, f2, f3):
    mapping = pv_system.get_mapping()
    time_string = None
    for line in result:
        if line[3] != '0' and int(line[3]) > 99:
            ratio = float(line[2])/int(line[3])
            if ratio > 1.25:
                    f = f1
            elif ratio < 0.8:
                    f = f2
            else:
                    f = f3
            print(f"Time {line[0]} Inverter: {int(line[1]):6d} Tracker 1:{int(line[2]):6d} Tracker 2 {int(line[3]):6d}: Ratio: {ratio}", file = f)

def db_refresh_solarlog_day():
    import config
    import psycopg2
    con = psycopg2.connect(f"dbname={config.database_name} user={config.database_user}")
    cur = con.cursor()
    cur.execute("refresh materialized view solarlog_day;")
    cur.execute("refresh materialized view solarlog_5min_w_per_kwp;")
    cur.execute("refresh materialized view solarlog_5min_w_per_kwp_inv;")
    print("refreshing materialized view solarlog_day", file=sys.stderr)
    con.commit()
    con.close()
