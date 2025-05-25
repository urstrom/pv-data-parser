import datetime

import solarlog_parse

def compare_single(system_id, inverter_id, tracker_id, timestamp, fetch_new, fetch_old):
    if fetch_new != fetch_old:
        print(f"System({system_id}) Inverter({inverter_id}) Tracker({tracker_id}) Measurement_Time({timestamp})"
             f" NEW{fetch_new} OLD{fetch_old}")

def compare(system_id_set, begin_time, end_time):
    import config
    testvar = 4
    import psycopg2
    con_new = psycopg2.connect(
        f"dbname={config.database_name} user={config.database_user} host={config.database_host} password={config.database_password}")
    cur_new = con_new.cursor()
    con_old = psycopg2.connect(
        f"dbname='sunshinedb' user={config.database_user} host={config.database_host} password={config.database_password}")
    cur_old = con_old.cursor()

    for system_id in system_id_set:
        pv_system = solarlog_parse.js_basevars(
            f"{config.path_base}/{'%02d' % system_id}/base_vars.js", system_id)
        measurement_time = datetime.datetime.fromisoformat(begin_time)
        measurement_last = datetime.datetime.fromisoformat(end_time)
        while measurement_time <= measurement_last:
            sql_string_old = \
                (f"select yield from solarlog_5min where system_id = {system_id} and measurement_time = '2024-01-05 11:05:00' order"
                 f" by tracker_id_text;")
            cur_old.execute(sql_string_old)
            for inverter_id in range(1, len(pv_system['inverters'])+1):
                if pv_system['inverters'][inverter_id - 1]['is_production']:
                    for timestamp in ["2024-01-05 11:05:00"]:
                        fetch_old = cur_old.fetchone()
                        sql_string_new = \
                            f"select yield from solarlog_5min where system_id = {system_id} and tracker_id = 0 " \
                            f"and inverter_id = {inverter_id} and measurement_time = '{timestamp}';"
                        cur_new.execute(sql_string_new)
                        fetch_new = cur_new.fetchone()
                        compare_single(system_id, inverter_id, 0, timestamp, fetch_new, fetch_old)
            for inverter_id in range(1, len(pv_system['inverters']) + 1):
                if pv_system['inverters'][inverter_id - 1]['is_production']:
                    for tracker_id in range(1, pv_system['inverters'][inverter_id - 1]['nr_trackers'] + 1):
                        for timestamp in ["2024-01-05 11:05:00"]:
                            sql_string_new = \
                                f"select yield from solarlog_5min where system_id = {system_id} and tracker_id = {tracker_id} " \
                                f"and inverter_id = {inverter_id} and measurement_time = '{timestamp}';"
                            cur_new.execute(sql_string_new)
                            fetch_new = cur_new.fetchone()
                            fetch_old = cur_old.fetchone()
                            compare_single(system_id, inverter_id, tracker_id, timestamp, fetch_new, fetch_old)
            measurement_time += datetime.timedelta(minutes=5)

compare( [1] + list(range(4,18)),  "2024-01-05 11:05:00", "2024-01-05 11:05:00")