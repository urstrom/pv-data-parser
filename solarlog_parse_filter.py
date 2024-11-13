#!/usr/bin/python3

# Parse solarlog min*.js files
# ' https://www.photonensammler.de/wiki/doku.php?id=solarlog_datenformat'

import sys
print(sys.path)

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
import config
import shutil
import pathlib

rebanner = re.compile("var BannerLink")
reclosed = re.compile('"\\s*$')

def js_production_5min(system_id, file, data_root_system, file_type, encoding, pv_system):
    """Parses an entire JS min file."""
    path_in = f"{data_root_system}/{file}.js"
    path_out = f"{data_root_system}w/{file}.js"
    print(f"parsing attempt: {path_in}", file=sys.stderr)
    if os.path.isfile(path_in):
        print(f"parsing minfile js_production_5min {path_in}\n", file=sys.stderr)
        try:
            min_file = open(path_in, "r")
            output_file = open(path_out, "w")
            lines = min_file.readlines()
            for line in lines:
                line = line.strip()
                inverter_inputs = line.split('|')
                inverter_outputs = [inverter_inputs.pop(0)] # directly move the date part to the outputs
                inverter_counter = 0
                inverter_is_production = pv_system.get_inverter_is_production()

                for inverter_input in inverter_inputs:
                    field_inputs = inverter_input.split(';')
                    field_outputs = []
                    field_counter = 0
                    for f in field_inputs:
                        if inverter_is_production[inverter_counter] != 1:
                            f = "0"
                        if pv_system.has_temperature == 1 \
                            and field_counter == len(field_inputs) - 1:
                            # print(f"bingo {inverter_counter};{field_counter};{f}")
                            f = "0"
                        field_outputs.append(f)
                        field_counter += 1
                    inverter_outputs.append(';'.join(field_outputs))
                    inverter_counter += 1

                output = "|".join(inverter_outputs)
                if not reclosed.search(output):
                    output += '"'
                print(output, file=output_file)
            min_file.close()
            output_file.close()
        except Exception as e:
            print(f"Exception {e} in parsing {path_in}")

def js_production_day(system_id, file_name):
    """Parses an entire JS min file."""
    data_root_system = f"{config.path_data_raw}/{system_id}"
    pv_system = solarlog_parse_library.parse_basevars_file(data_root_system)
    path_in = f"{data_root_system}/{file_name}"
    path_out = f"{config.path_data_raw}/{system_id}w/{file_name}"

    if os.path.isfile(path_in):
        print(f"parsing file {path_in}\n", file=sys.stderr)
        with open(path_in, "r") as input_file, open(path_out, "w") as output_file:
            lines = input_file.readlines()
            for line in lines:
                line.strip()
                inverter_inputs = line.split('|')
                inverter_outputs = [inverter_inputs.pop(0)] # directly move the date part to the outputs
                inverter_counter = 0
                inverter_is_production = pv_system.get_inverter_is_production()

                for inverter_input in inverter_inputs:
                    field_inputs = inverter_input.split(';')
                    field_outputs = []
                    field_counter = 0
                    for f in field_inputs:
                        if inverter_is_production[inverter_counter] != 1:
                            f = "0"
                        field_outputs.append(f)
                    inverter_outputs.append(';'.join(field_outputs))
                    inverter_counter += 1

                output = "|".join(inverter_outputs)
                if not reclosed.search(output):
                    output += '"'
                print(output, file=output_file)


def csv_production_5min(system_id, day, data_root_system, file_type, encoding, pv_system):
    """Parses an entire CSV min file."""

    tracker_offsets = []
    inverter_offsets = []
    row_counter = 0
    solarlog_csv_version = '0'

    path_in = f"{data_root_system}/min{day}.csv"
    path_out = f"{data_root_system}/w/min{day}.csv"

    result = []
    if os.path.isfile(path_in):
        print("parsing: " + path_in, file=sys.stderr)
        is_production = []
        try:
            file_in = open(path_in, newline='', encoding=encoding)
            file_out = open(path_out, "w", newline='', encoding=encoding)
        except IOError:
            print("File not found")
        reader = csv.reader(file_in, delimiter=';', quotechar='\"')
        for row in reader:
            if row_counter == 0:
                # is header row
                print(';'.join(row), file=file_out)
                if row[0][0:15] == '#SDS CSV V1.0.0':
                    solarlog_csv_version = '1.0.0'
                    print(';'.join(solarlog_csv_version), file=sys.stderr)
                else:  # old Solar-Log CSV version has header in 1st row
                    print("Old CSV without version", file=sys.stderr)
                    field_counter = 0
                    inverter_counter = 0
                    is_production_append = 0
                    for l in row:
                        # if l[0:3] == 'Pac':  # German or English
                        if l == 'INV':  # German or English
                            inverter_offsets.append(field_counter)
                            print(f"added inverter Pac {field_counter}", file=sys.stderr)
                            tracker_offsets.append([])
                            if pv_system.get_inverter_is_production()[inverter_counter] == 1:
                               is_production_append = 1
                            else:
                               is_production_append = 0
                            inverter_counter += 1
                        if l[0:3] == 'Pdc':  # tracker DC
                            tracker_offsets[-1].append(field_counter)
                        is_production.append(is_production_append)
                        field_counter += 1
                row_counter += 1
            elif row_counter == 1 and solarlog_csv_version == '1.0.0':
                field_counter = 0
                for f in row:
                    if field_counter <= 1 or 1 == pv_system.get_inverter_is_production()[int(f[0:1])]:
                        is_production.append(1)
                    else:
                        is_production.append(0)
                    field_counter += 1
                row_counter += 1
                print(';'.join(row), file=file_out)
            else:  # is data row
                output = []
                print("row data")
                field_counter = 0
                for f in row:
                    if is_production[field_counter]:
                        output.append(f)
                    else:
                        output.append("0")
                    field_counter += 1
                print(';'.join(output), file=file_out)
    return

def csv_production_5min_stdout(system_id, day, data_root_system, file_type, encoding, pv_system):
    """Parses an entire CSV min file."""

    tracker_offsets = []
    inverter_offsets = []
    row_counter = 0
    solarlog_csv_version = '0'

    path_in = f"{data_root_system}/min{day}.csv"
    path_out = sys.stdout

    result = []
    if os.path.isfile(path_in):
        print("parsing: " + path_in, file=sys.stderr)
        is_production = []
        try:
            file_in = open(path_in, newline='', encoding=encoding)
            file_out = sys.stdout
        except IOError:
            print("File not found")
        reader = csv.reader(file_in, delimiter=';', quotechar='\"')
        for row in reader:
            if row_counter == 0:
                # is header row
                print(';'.join(row), file=file_out)
                if row[0][0:15] == '#SDS CSV V1.0.0':
                    solarlog_csv_version = '1.0.0'
                    print(';'.join(solarlog_csv_version), file=sys.stderr)
                else:  # old Solar-Log CSV version has header in 1st row
                    print("Old CSV without version", file=sys.stderr)
                    field_counter = 0
                    inverter_counter = 0
                    is_production_append = 0
                    for l in row:
                        # if l[0:3] == 'Pac':  # German or English
                        if l == 'INV':  # German or English
                            inverter_offsets.append(field_counter)
                            print(f"added inverter Pac {field_counter}", file=sys.stderr)
                            tracker_offsets.append([])
                            if pv_system.get_inverter_is_production()[inverter_counter] == 1:
                               is_production_append = 1
                            else:
                               is_production_append = 0
                            inverter_counter += 1
                        if l[0:3] == 'Pdc':  # tracker DC
                            tracker_offsets[-1].append(field_counter)
                        is_production.append(is_production_append)
                        field_counter += 1
                row_counter += 1
            elif row_counter == 1 and solarlog_csv_version == '1.0.0':
                field_counter = 0
                firstline = []
                for f in row:
                    if field_counter <= 1 or 1 == pv_system.get_inverter_is_production()[int(f[0:1])]:
                        is_production.append(1)
                    else:
                        is_production.append(0)
                    if f.find('[W]') > -1 and f.find('PDC') > -1 or field_counter < 2:
                        firstline.append(f)
                    else:
                        is_production[-1] = 0
                    field_counter += 1
                row_counter += 1
                print(';'.join(firstline), file=file_out)
            else:  # is data row
                output = []
                # print("row data")
                field_counter = 0
                for f in row:
                    if is_production[field_counter]:
                        output.append(f)
                    field_counter += 1
                print(';'.join(output), file=file_out)
    return



def csv_write_header(pv_system, fh):
    """Write the header line of the CSV"""
    csv_str = "ts"
    mapping = pv_system.get_mapping()
    for m in mapping:
        csv_str += f"{solarlog_parse_library.sep}{m}"
    print(csv_str, file=fh)

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


def csv_write_body(result, fh):
    for line in result:
        print(solarlog_parse_library.sep.join(map(str, line)), file=fh)

def setup_banner_link(source_dir, system_id):
    path_in = f"{source_dir}/urstrom-base_vars.js"
    path_out = f"{source_dir}w/urstrom-base_vars.js"

    if os.path.isfile(path_in):
        print(f"parsing file {path_in}\n", file=sys.stderr)
        input_file = open(path_in, "r")
        output_file = open(path_out, "w")
        lines = input_file.readlines()
        for line in lines:
            if rebanner.search(line):
                print(f'var BannerLink = "www.urstrom-projektspiegel.com/monitoring/anlagen/{("%02d" % system_id)}w"', file=output_file, end="")
            else:
                print(line, file=output_file, end="")
        input_file.close()
        print(f"closing output file {path_out}")
        output_file.close()

def initial_setup(root, system_id):
        source_dir = f"{root}/{('%02d' % system_id)}"
        target_path = f"{source_dir}w"
        pathlib.Path(target_path).mkdir(parents=True, exist_ok=True)

        files = ["anlageninfo.html", "b_000000.gif", "b_0000ff.gif", "back.gif", "background.jpg", "back_links.jpg",
                 "backward.gif", "banner.html", "banner_leer.jpg", "base_vars.js", "b_ff0000.gif",
                 "b.gif", "bg_palm.jpg", "black.gif", "choose.gif", "clear.gif", "d_000000.gif", "d_0000ff.gif",
                 "dateformat.js", "d_ff0000.gif", "diagram.css", "diagram_dom.js", "diagram.js", "diagram_nav.js",
                 "e.gif", "empty.gif", "evalsafe.js", "favicon.ico", "fenster_maske_1.gif", "forward.gif",
                 "functions.js", "h_blue.gif", "h_green.gif", "h_orange.gif", "h_red.gif", "iframe.html",
                 "index.html", "lang_DE.js", "lang_DK.js", "lang_EN.js", "lang_ES.js", "lang_FR.js", "lang_IT.js",
                 "lang_NL.js", "links.html", "o_000000.gif", "o_0000ff.gif", "o_ff0000.gif", "p_000000.gif",
                 "p_0000ff.gif", "palm2.js", "palm.html", "p_ff0000.gif", "pi.gif", "q_000000.gif", "q_0000ff.gif",
                 "q_ff0000.gif", "red.gif", "smile.gif", "solaranlage.jpg", "string1.png", "string2.png", "string3.png",
                 "transparent.gif", "urstrom-banner.html", "urstrom-banner.php", "urstrom-base_vars.js",
                 "v_blue.gif", "v_green.gif", "view.gif", "view.png", "visu.html", "v_orange.gif", "v_red.gif",
                 "wz_tooltip.js", "ydot.gif", "y.gif"]
        for f in files:
            if os.path.exists(os.path.join(source_dir, f)):
                shutil.copyfile(os.path.join(source_dir, f), os.path.join(target_path, f))
        setup_banner_link(source_dir, i)

def parse_file(system_id, day, data_root_system, file_type, encoding, target):
    result = None
    pv_system = solarlog_parse_library.parse_basevars_file(data_root_system)
    pv_system.id = system_id
    day = day.replace('-', '')
    if len(day) == 8:
        day = day[2:8]

    if target == "csv_production_5min":
        csv_production_5min(system_id, day, data_root_system, file_type, encoding, pv_system)
    if target == "js_production_5min":
        js_production_5min(system_id, f"min{day}", data_root_system, file_type, encoding, pv_system)

def parse_file_time_range(system_id, time_begin, time_end, file_type, encoding, target):
    import config
    time_begin = datetime.datetime.strptime(time_begin, "%Y-%m-%d")
    time_end = datetime.datetime.strptime(time_end, "%Y-%m-%d")
    delta = time_end - time_begin
    for day in range(delta.days + 1):
        target_date = (time_begin + datetime.timedelta(days=day)).strftime("%y%m%d")
        # if target != "db" and target != "influxdb" and target != "influxdb2" and target != 'postgresql' \
        #        and target != 'postgresql_check' and target != "raw" and target != 'solarlog_csv_export'\
        #        and target != 'csv_production' and target != 'js_production':
        #    target = f"{config.path_data_processed}/data-5min-{system_id}-{target_date}.csv"
        parse_file(system_id, target_date,
                   f"{config.path_data_raw}/{system_id}", file_type, encoding, target)

def filter_time_range(system_id, time_begin, time_end, encoding):
    parse_file_time_range(system_id, time_begin, time_end, 'js', encoding, 'js_production_5min')
    # parse_file_time_range(system_id, time_begin, time_end, 'csv', encoding, 'cvs_production_5min')
    js_production_day(system_id, 'days.js')
    js_production_day(system_id, 'days_hist.js')
    js_production_day(system_id, 'months.js')
    js_production_day(system_id, 'years.js')

if __name__ == "__main__":
    for i in [1,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]:
        initial_setup(config.path_data_raw, i)
        end_day_day = datetime.datetime.now()
        end_day = end_day_day.strftime('%Y-%m-%d')
        begin_day = (end_day_day + datetime.timedelta(days=-10)).strftime('%Y-%m-%d')
        filter_time_range(("%02d" % i), begin_day, end_day, 'utf-8')
        # filter_time_range(("%02d" % i), '2010-01-01', '2025-01-01', 'utf-8')

    ### FIXEME filter_time_range("10", '2015-01-01', '2025-01-01', 'utf-8')
    #parse_file_time_range('06', '2021-01-01', '2021-12-31', 'js', 'utf-8', 'influxdb2')
