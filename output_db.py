import output, datetime, traceback

def db_write(data, pv_system):
    global cur
    # mapping = pv_system.get_mapping()
    time_string = None

    for line in data:
        for j in range(len(line)):
            if j == 0:
                time_string = f"'{line[0].replace(tzinfo=None)}','{int(line[0].utcoffset().total_seconds())}'"
                # time_string = f"'{line[0].astimezone(pytz.utc).replace(tzinfo=None)}','{line[0].utcoffset().total_seconds()}'"
            else:
                for tracker_counter in range (len(pv_system['inverters'])):# range(len(line[j]['dc'])):
                    if pv_system['inverters'][tracker_counter]['is_production'] == 1:
                        try:
                            # print(f"insert into tracker_5min (system_id, tracker_id, timestamp, tz_offset, yield) values ('{pv_system.id}','{mapping[j - 1]}',{time_string},{line[j]})")
                            sql_string = str(f"insert into solarlog_5min (system_id, inverter_id, tracker_id, measurement_time, "
                                  f"tz_offset, tracker_id_text, yield) values ('{pv_system['id']}', {j+1} , {tracker_counter+1}, "
                                  f"{time_string}, 'tr01',{line[j]['dc'][tracker_counter]})")
                            cur.execute(sql_string)
                        except TimeoutError as e:
                            print(f"Error: {e} from db_write")
                        except Exception as e:
                            print(f"Error: {e} from db_write")


def db_check(data, pv_system):
    '''Check database table for updates, record all actions in solarlog_5min_old'''
    import config
    import psycopg2
    try:
        con = psycopg2.connect(
            f"dbname={config.database_name} user={config.database_user} host={config.database_host} password={config.database_password}")
        cur = con.cursor()
        # mapping = pv_system.get_mapping()
        header = data.pop(0) # header string
        sql_string = f"insert into solarlog_5min (system_id, inverter_id, tracker_id, tracker_id_text, measurement_time, "
        sql_string += f"tz_offset, yield, insertion_time) values"
        for line in data:
            datetime_now = datetime.datetime.now()
            measurement_time = line.pop(0)
            time_string = f"'{measurement_time.replace(tzinfo=None)}'"
            time_string_insert = f"'{measurement_time.replace(tzinfo=None)}','{int(measurement_time.utcoffset().total_seconds())}'"
            for inverter_candidate_counter in range(len(pv_system['inverters'])):
                inverter_counter = 0
                if pv_system['inverters'][inverter_candidate_counter]['is_production'] == 1:
                    for tracker_counter in range(pv_system['inverters'][inverter_candidate_counter]['nr_trackers'] + 1): # +1: accomodate ac value
                        if tracker_counter == 0:
                            data_point = line[inverter_candidate_counter]['ac']
                        else:
                            data_point = line[inverter_candidate_counter]['dc'][tracker_counter - 1]  # -1: the first is used for ac
                        sql_string += f" ({pv_system['id']}, {inverter_candidate_counter + 1}, {tracker_counter}, '', "
                        sql_string += f"{time_string_insert},{data_point},'{datetime_now}'),"
                        tracker_counter += 1
                    inverter_counter += 1
        sql_string = sql_string[:-1] + " on conflict (system_id, inverter_id, tracker_id, measurement_time) "
        sql_string += "do update set measurement_time = excluded.measurement_time and yield = excluded.yield"
        cur.execute(sql_string)
        con.commit()
        con.close()
    except Exception as e:
        raise
        traceback.print_exc()
        print(f"Error: {e} at {pv_system['id']} and {time_string}")

def db_check_bulk(data, pv_system, cur):
    mapping = pv_system.get_mapping()
    time_string = None
    cur.execute(
        f"select yield from solarlog_5min where system_id = '{pv_system['id']}' "
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
