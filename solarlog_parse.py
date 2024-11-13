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
import solarlog_parse_database
import solarlog_parse_filter




def parse_file(system_id, day, data_root_system, file_type, encoding, target):
    result = None
    pv_system = solarlog_parse_library.parse_basevars_file(data_root_system)
    pv_system.id = system_id
    day = day.replace('-', '')
    if len(day) == 8:
        day = day[2:8]


    # Parsing the data into result.

    if file_type == 'js':
        result = solarlog_parse_database.parse_min_file_name_js(f'{data_root_system}/min{day}.js', encoding, pv_system)
    if file_type == 'csv':
        result = solarlog_parse_database.parse_min_file_name_csv(f'{data_root_system}/min{day}.csv', encoding, pv_system)

    # Writing result into output.

    if target == "db":
        import config
        import mariadb
        con = mariadb.connect(
            user=config.database_user,
            password=config.database_password,
            host=config.database_host,
            port=config.database_port,
            database=config.database_name)
        cur = con.cursor()
        solarlog_parse_database.db_write_body(result, pv_system, cur)
        con.commit()
        con.close()
    if target == "solarlog_csv_export":
        solarlog_parse_filter.solarlog_csv_export_write_body_result_only(result, pv_system, data_root_system, file_type, target)
    elif target == "postgresql":
        import config
        import psycopg2
        con = psycopg2.connect(f"host={config.database_host} dbname={config.database_name} user={config.database_user} password={config.database_password}")
        cur = con.cursor()
        try:
            solarlog_parse_database.db_write_body(result, pv_system, cur)
        except Exception as e: 
            print(e)
        con.commit()
        con.close()
    elif target == "postgresql_check":
        # print("postgresql_check")
        ### simply check ###
        import config
        import psycopg2
        con = psycopg2.connect(f"host={config.database_host} dbname={config.database_name} user={config.database_user} password={config.database_password}")
        cur = con.cursor()
        try:
            solarlog_parse_database.db_check_body(result, pv_system, cur)
        except Exception as e:
            print(e)
        con.commit()
        con.close()
    elif target == "postgresql_check_bulk":
        # print("postgresql_check")
        ### simply check ###
        import config
        import psycopg2
        con = psycopg2.connect(
            f"host={config.database_host} dbname={config.database_name} user={config.database_user} password={config.database_password}")
        cur = con.cursor()
        try:
            solarlog_parse_database.db_check_body_bulk(result, pv_system, cur)
        except Exception as e:
            print(e)
        con.commit()
        con.close()
    elif target == "influxdb":
        from influxdb import InfluxDBClient
        client = InfluxDBClient(host='localhost', port=8086)
        client.switch_database('trackermon')
        influxdb_write_body(result, pv_system, client)
    elif target == "influxdb2":
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        org = "hbl"
        bucket = "hbl"
        query = 'from(bucket: "hbl")\
        |> range(start: -10m)\
        |> filter(fn: (r) => r._measurement == "h2o_level")\
        |> filter(fn: (r) => r._field == "water_level")\
        |> filter(fn: (r) => r.location == "coyote_creek")'
        client = InfluxDBClient(url="http://localhost:8086", token='xxx', org='hbl')
        # client = InfluxDBClient(host='localhost', port=8086)
        write_api = client.write_api()
        query_api = client.query_api()
        influxdb2_write_body(result, pv_system, write_api)
        # create and write the point
        # return the table and print the result
        result = client.query_api().query(org=org, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_value(), record.get_field()))
        print(results)
        #client.switch_database('trackermon')
        #influxdb2_write_body(result, pv_system, client)
    elif target == "raw":
        f1 = open("/home/hbl/analysis_tr1_large.txt", "a")
        f2 = open("/home/hbl/analysis_tr2_large.txt", "a")
        f3 = open("/home/hbl/analysis_equal.txt", "a")
        solarlog_parse_database.analysis_raw(result, pv_system, f1, f2, f3)
        f1.close()
        f2.close()
        f3.close()
    else:
        if not os.path.exists(f'{data_root_system}/min{day}.{file_type}'):
            print(f"{data_root_system}/min{day}.{file_type} does not exist", file=sys.stderr)
            return
        try:
            fh = open(target, "w", encoding="utf-8")
        except ValueError:
            print(f"Error: Cannot open {target} for writing", file=sys.stderr)
            return
        solarlog_parse_filter.csv_write_header(pv_system, fh)
        solarlog_parse_filter.csv_write_body(result, fh)
        fh.close()


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

