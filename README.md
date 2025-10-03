Data parser for PV data (currently supports Solar-Log)

Maintainer: holger.blasum@urstrom.de

# Files

* pv_data.py: main control module
* config.py: Configuration file (password etc)
* solarlog_parse.py: Routines for parsing Solar-Log.
* filter.py: Functions for filtering.
* output.py: Output functions (generic/stdout/file).
* output_db.py: Output functions to database.
* test/*: Python unit tests.


# Data exchange interfaces

## DDF: Day data format: Used between solarlog_parse/filter/output*

This is an array of data rows, characterized as follows: 
* the first data row contains the header, which is a dictionary to represent properties of the original file
	* version: Solar-Log export format version
	* path: path information
	* line1: original line1 of day yield file
	* line2: original line2 of day yield file
	* offsets: list of offsets of inverters and trackers in a CSV row
* the other data rows ("body") each contains an array
	* timestamps
	* inverter dictionaries
		* each inverter dictionary has the keys
			'ac', 'dc', 'sum', 'voltage', 'temperature'

## PV system representation: pv_system

This is a dictionary with the following keys:
* id: ID of the PV system
* row_length: length of CSV row
* inverters: list of inverters, each inverter has the keys: 
	* name: name of inverter
	* is_production: is it a real inverter that produces electricity or is it a placeholder for a (consumption) meter 
	* size: size of inverter (kWp)
	* nr_trackers: number of trackers 
	* type: type of inverter, as per Solar-Log basevars.js format 
* has_temperature: does the PV system store temperature data



# Database format 

Database format (PostgreSQL):

* tracker_id != 0 is tracker_id DC, tracker_id = 0 is inverter_id AC
* inverter_id_recorded: can be used to track old recorded inverter IDs in the event of inverter reordering

```
CREATE TABLE public.solarlog_5min (
    system_id integer DEFAULT 18 NOT NULL,
    measurement_time timestamp without time zone NOT NULL,
    tz_offset integer,
    yield integer, 
    insertion_time timestamp without time zone,
    inverter_id integer NOT NULL,
    tracker_id integer NOT NULL,
    inverter_id_recorded integer NOT NULL,
);
CREATE TABLE public.tracker (
    tracker_id_str character varying(20) NOT NULL,
    inverter_id_str character varying(15) NOT NULL,
    tracker_shorthand character varying(10) NOT NULL,
    tracker_orientation character varying(30) NOT NULL,
    tracker_position character varying(10) NOT NULL,
    field integer NOT NULL,
    azimuth integer NOT NULL,
    tilt integer NOT NULL,
    number_parallel integer NOT NULL,
    number_seriell integer NOT NULL,
    number_modules integer NOT NULL,
    module_power integer NOT NULL,
    power integer NOT NULL,
    tracker_id_global_str character varying(16),
    system_id integer,
    inverter_id integer,
    tracker_id integer,
    tracker_id_global integer,
    tracker_tr character varying
);

```

# TYPICAL USAGE

# Tracker masks

A tracker mask can be defined in config to select only certain trackers per inverter in case your CSV has empty columns for some system. The following tracker mask makes the program ignore the odd values for the first and second inverter of system 20.
```
tracker_mask = {20: ((0,2,4,6),(0,2,4,6),(0,1,2,3,4,5,6,7,8,9,10,11),(0,1,2,3,4,5,6,7,8,9,10,11))}
```
