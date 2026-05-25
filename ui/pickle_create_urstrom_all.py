import sys, os, datetime, pickle, pathlib
import pv_data, config, solarlog_parse, filter, output, pickle_create, urstrom

def pickle_create_urstrom_all(date_begin, date_end):

    for pv_system_id in range(1, urstrom.get_number_systems() + 1):

        parse_function = urstrom.get_parse_function(pv_system_id, date_begin, date_end)
        if parse_function is not None:
            pickle_create.pickle_create(
                pv_system_id, date_begin, date_end, parse_function)

        # pickle_create.pickle_create(pv_system_id, date_begin, date_end, parse_format)
    

if __name__ == "__main__":
    pickle_create_urstrom_all(sys.argv[1], sys.argv[2])
