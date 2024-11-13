class PvTracker:
    dc = 0
    tilt = -1
    azimuth = -1

    def __init__(self, name):
        self.name = name

    def __str__(self):
        rstr = "  Tracker: " + self.name + ", DC: " + str(self.dc) + ", Azimuth: " + str(
            self.azimuth) + ", Tilt: " + str(self.tilt) + "\n"
        # for key, value in sorted(self.data.items()):
        #    rstr = rstr + " " + str(key) + ": " + str(value) + " "
        return rstr


class PvInverter:
    def __init__(self, name, inv_size, inv_pv_trackers_no, inv_type):
        self.name = name
        self.inv_size = int(inv_size)
        self.inv_type = int(inv_type)
        if inv_pv_trackers_no == "0":
            inv_pv_trackers_no = "1"
        self.pv_trackers_no = int(inv_pv_trackers_no)
        self.pv_trackers = []

    def __str__(self):
        rstr = " PvInverter: " + self.name + ", Type: " + str(self.inv_type) \
               + ", DC: " + str(self.inv_size) + ", #Trackers: " + str(self.pv_trackers_no) + "\n"
        for tracker in self.pv_trackers:
            rstr = rstr + str(tracker)
        return rstr


class PvSystem:
    name = ""
    solarlog_type = ""
    max_tracker_data = None

    def __init__(self, identity):
        self.id = identity
        self.pv_inverters = []

    def __str__(self):
        rstr = "PvSystem: " + self.id + ", " + self.name + ", SolarLog-Type: " + self.solarlog_type + "\n"
        for inverter in self.pv_inverters:
            rstr = rstr + str(inverter)
        return rstr

    def set_row_length(self, row_length):
        self.row_length = row_length

    def get_row_length(self):
        return self.row_length

    def set_tracker_offsets(self, tracker_offsets):
        self.tracker_offsets = tracker_offsets

    def get_tracker_offsets(self):
        return self.tracker_offsets

    def set_inverter_is_production(self, inverter_is_production):
        self.inverter_is_production = inverter_is_production

    def get_inverter_is_production(self):
        return self.inverter_is_production

    def get_inverter_is_production_number(self):
        counter = 0
        for inverter in self.inverter_is_production:
            counter += inverter
        return counter

    def set_inverter_has_temperature(self, inverter_has_temperature):
        self.inverter_has_temperature = inverter_has_temperature

    def get_inverter_has_temperature(self):
        return self.inverter_has_temperature


    def set_inverter_offsets(self, inverter_offsets):
        self.inverter_offsets = inverter_offsets

    def get_inverter_offsets(self):
        return self.inverter_offsets

    def no_of_trackers(self):
        rval = 0
        for inverter in self.pv_inverters:
            rval = rval + len(inverter.pv_trackers)
        return rval

    def tracker_by_number(self, number):
        counter = 0
        for inverter in self.pv_inverters:
            if counter + len(inverter.pv_trackers) > number:
                # print("n%d c%d l%d" % ( number, counter, len(inverter.pv_trackers)))
                return inverter.pv_trackers[number - counter]
            counter += len(inverter.pv_trackers)
        return None

    def tracker_by_name(self, name):
        number = int(name[2:])
        counter = 1
        for inverter in self.pv_inverters:
            if counter + len(inverter.pv_trackers) > number:
                # print("n%d c%d l%d" % ( number, counter, len(inverter.pv_trackers)))
                return inverter.pv_trackers[number - counter]
            counter += len(inverter.pv_trackers)
        return None

    def tracker_by_name_type(self, name):
        number = int(name[2:])
        counter = 1
        for inverter in self.pv_inverters:
            if counter + len(inverter.pv_trackers) > number:
                # print("n%d c%d l%d" % ( number, counter, len(inverter.pv_trackers)))
                return inverter.pv_trackers[number - counter], inverter.inv_type
            counter += len(inverter.pv_trackers)
        return None

    def compare(self, pvsystem):
        invcounter = 0
        for inverter in self.pv_inverters:
            tracker_counter = 0
            for tracker in inverter.pv_trackers:
                print(f"me: {tracker.dc}, other: {pvsystem.pv_inverters[invcounter].pv_trackers[tracker_counter].dc}, "
                    f"tracker counter: {tracker_counter}, inverter counter {invcounter}")
                tracker_counter += 1
            invcounter += 1

    def get_mapping(self):
        """Get the mapping for the DB."""
        mapping = []
        tracker_counter = 0
        consumer_counter = 0
        inverter_counter = 0

        for counter_inv in range(0, len(self.pv_inverters)):
            if self.pv_inverters[counter_inv].inv_type != 0:
                # consumer
                consumer_counter += 1
                continue
            mapping.append("inv" + ("%02d" % (counter_inv + 1)))
            for _ in range(0, self.pv_inverters[counter_inv].pv_trackers_no):
                tracker_counter += 1
                mapping.append("tr" + ("%02d" % tracker_counter))
                inverter_counter += 1
                # only three trackers per inverter in Solar-Log
                # if invcounter <= 3:
        return mapping


def tracker_labels_from_df(df):
    tracker_nums = []
    for t in df.columns:
        if t[0:2] == "tr":
            tracker_nums.append(int(t[2:]))
    tracker_nums = sorted(tracker_nums, key=int)
    trackers = []
    for t in tracker_nums:
        trackers.append("tr%02d" % t)
    return trackers

def get_trackers(cur, system_id):
    cur.execute(
        f"select tracker_id_str, field, power from tracker where system_id = {system_id} order by tracker_id_str;")
    res = cur.fetchall()
    return res

# parse system data from own table and MariaDB strings table
def pvsystem_parse(path, identity):
    import pandas as pd
    system_data = pd.read_csv(path + "/systems.csv", index_col="id")
    # print(system_data)
    # print(system_data.at[name, "location"])
    pv_system = PvSystem("")
    pv_system.id = identity
    pv_system.name = system_data.at[identity, "name"]
    pv_system.lat = system_data.at[identity, "lat"]
    pv_system.long = system_data.at[identity, "long"]
    pv_system.initdata = system_data.at[identity, "initdata"]
    string_data = pd.read_csv(path + "/strings.csv")

    string_data['system'] = string_data['str_id'].str.slice(0, 5)
    string_data['inv'] = string_data['str_id'].str.slice(7, 9)
    string_data = string_data[string_data['system'] == pv_system.id]

    inverters = {}
    inverter_idx = -1

    for _, row in string_data.iterrows():
        inv = row['inv']
        if inv.isdigit():  # filter consumption counters
            if inv not in inverters:
                inverters[inv] = 1
                inv_data = string_data[string_data['inv'] == inv]
                pv_inverter = PvInverter(inv, 0, len(inv_data.index), 0)
                pv_system.pv_inverters.append(pv_inverter)
                inverter_idx += 1
                lasttrackerstring = None
                pv_string = None
                for _, row_inv in inv_data.iterrows():
                    addition = 0
                    if row_inv['tracker'] is not None and isinstance(row_inv['tracker'], str) \
                            and len(row_inv['tracker']) > 0 and row_inv['tracker'] == lasttrackerstring:
                        addition = row_inv['str_leistung']
                    if addition == 0:
                        if pv_string is not None:
                            pv_system.pv_inverters[inverter_idx].pv_trackers.append(pv_string)
                        pv_string = PvTracker(row_inv['str_id'])
                        pv_string.dc = row_inv['str_leistung']
                        pv_string.azimuth = row_inv['str_ausrichtung']
                        pv_string.tilt = row_inv['str_neigung']
                    else:
                        pv_string.dc += addition
                    lasttrackerstring = row_inv['tracker']
                if pv_string is not None:
                    pv_system.pv_inverters[inverter_idx].pv_trackers.append(pv_string)
    print(string_data)
    return pv_system
