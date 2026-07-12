Data parser for PV data (currently supports Solar-Log).

Maintainer: holger.blasum@urstrom.de

# Entry point and files

The central function "data_range" (pv_data.py) function takes a filesystem path to Solar-Log data, a beginning and end date, and on the files specified by these parameters executes the specified parse function (e.g. parsing CSV or JS), (optional) filter functions (e.g. to select only production values, but not consumption values) and output functions (e.g. to database or Python pickle format). The user interface (with some example combinations) are functions in the ui folder.

* pv_data.py: main control module
* config.py: Configuration file (password etc)
* solarlog_parse.py: Routines for parsing Solar-Log.
* filter.py: Functions for filtering.
* output.py: Output functions (generic/stdout/file).
* output_db.py: Output functions to database.
* test/*: Python unit tests.
* ui/*: Interfaces directly called by the user.


# Data exchange interfaces

## DDF: Day data format: Used for data exchange between functions solarlog_parse/filter/output*

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
CREATE TABLE solarlog_5min (
    system_id integer NOT NULL,
    measurement_time timestamp without time zone NOT NULL,
    tz_offset integer,
    yield integer, 
    insertion_time timestamp without time zone,
    inverter_id integer NOT NULL,
    tracker_id integer NOT NULL,
    inverter_id_recorded integer NOT NULL
);
ALTER TABLE solarlog_5min ADD PRIMARY KEY (system_id, inverter_id, tracker_id, measurement_time);
```

# Possible ways of usage

## Daily run

Check out git to $HOME/pv-data-parser

Edit pv-data-parser/config.py

mkdir pv-data-parser/log

Run pv-data-parser/ui/daily.sh, this calls db_import_from_pickle_urstrom_all.py

python3 ui/pickle_create_urstrom_all.py 2026-05-10 2026-05-11

## Tracker masks

A tracker mask can be defined in config to select only certain trackers per inverter in case your CSV has empty columns for some particular PV system. The following tracker mask makes the program ignore the odd values for the first and second inverter of system 20.
```
tracker_mask = {20: ((0,2,4,6),(0,2,4,6),(0,1,2,3,4,5,6,7,8,9,10,11),(0,1,2,3,4,5,6,7,8,9,10,11))}
```

## Pickling files

If the database server is different from the server collecting solarlog files, optionally, in a two-step process, parsed files can be exported to Python pickle files, which then can be copied to another server hosting the database import.

## Archiving Solar-Log configuration changes (basevars.js)  

This is not directly part of this pv-data-parser.py, but can (e.g.) be achieved with git by
```
(cd /your/home/data/directory && (for i in `seq -w 1 31` ; do git add ${i}/base_vars.js ; done) && git commit -m'Archive base_vars')
```

## Display yields graphically with e.g. Grafana

In the database, create a materialized view:

```
CREATE MATERIALIZED VIEW solarlog_5min_text AS
 SELECT system_id,
    (((inverter_id)::text || '-'::text) || (tracker_id)::text) AS tracker_id_text,
    measurement_time,
    tz_offset,
    yield,
    insertion_time,
    inverter_id,
    tracker_id
   FROM solarlog_5min
  WITH NO DATA;
refresh materialized view solarlog_5min_text;
```

Then display it with Grafana: 
```
SELECT
  $__timeGroupAlias(measurement_time,$__interval),
  avg(yield) AS "yield",
  tracker_id_text
FROM solarlog_5min_text
WHERE
  $__timeFilter(measurement_time) AND
  system_id = $sysid
GROUP BY 1, tracker_id_text
ORDER BY 1
```

## Display relative yields

Keep a database of tracker data, e.g.:

```
CREATE TABLE tracker (
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
ALTER TABLE tracker
    ADD PRIMARY KEY (system_id, inverter_id, tracker_id);
```

Have a materialized view linking both tables: 

```
CREATE MATERIALIZED VIEW solarlog_5min_w_per_kwp AS
 SELECT solarlog_5min.system_id,
    (((solarlog_5min.inverter_id)::text || '-'::text) || (solarlog_5min.tracker_id)::text) AS tracker_id_text,
    solarlog_5min.measurement_time,
    ((solarlog_5min.yield * 1000) / tracker.power) AS w_per_kwp
   FROM (solarlog_5min
     LEFT JOIN tracker ON (((tracker.system_id = solarlog_5min.system_id) AND (tracker.inverter_id = solarlog_5min.inverter_id) AND (tracker.tracker_id = solarlog_5min.tracker_id))))
    WHERE solarlog_5min.tracker_id != 0
  WITH NO DATA;
refresh materialized view solarlog_5min_w_per_kwp;
```

Display it with Grafana: 
```
SELECT
  $__timeGroupAlias(measurement_time,$__interval),
  avg(w_per_kwp) AS "w_per_kwp",
  tracker_id_text
FROM solarlog_5min_w_per_kwp
WHERE
  $__timeFilter(measurement_time) AND
  system_id = $sysid 
GROUP BY 1, tracker_id_text
ORDER BY 1
```

## Archiving updates of yields
Sometimes Solar-Log corrects yields from the previous day.
Thus, it can be useful to log (automatic) corrections of recorded yields.

For this create an additional table recording the updates:
```
CREATE TABLE solarlog_5min_updates (
    system_id integer,
    measurement_time timestamp without time zone,
    tz_offset integer,
    yield integer,
    insertion_time timestamp without time zone,
    inverter_id integer,
    tracker_id integer,
    inverter_id_recorded integer
);

```

And create a PostgreSQL trigger:
```
CREATE FUNCTION log_solarlog_5min_updates() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.yield IS DISTINCT FROM OLD.yield THEN
INSERT INTO solarlog_5min_updates (system_id, inverter_id, inverter_id_recorded, tracker_id, measurement_time, tz_offset, yield, insertion_time) VALUES ( OLD.system_id, OLD.inverter_id, OLD.inverter_id_recorded, OLD.tracker_id, OLD.measurement_time, OLD.tz_offset, OLD.yield, OLD.insertion_time  );
END IF;
RETURN NEW;
END;
$$;
```
Add the trigger to the update function:
```
CREATE TRIGGER solarlog_5min_yield_update_trigger
AFTER UPDATE ON solarlog_5min
FOR EACH ROW
EXECUTE FUNCTION log_solarlog_5min_updates();
```

And create an additional constraint:
```
ALTER TABLE solarlog_5min
ADD CONSTRAINT solarlog_5min_unique
UNIQUE (system_id, inverter_id_recorded, tracker_id, measurement_time);
```

## Testing

Folder test, file pv_data_test.py contains tests. First the description of the test is printed, followed by outputs to sys.stderr. These sys.stderr outputs may be intentional for inspection purposes.

## Installation at UrStrom

First, pulled from the repository and ran testing. 

```
$ test/pv_data_test.py
```

Next, adapted config.py.

Next, set up the database and assigned to a user.

Next, set up table for solarlog data: (CREATE TABLE solarlog_5min, see above and also create a primary key as above).

Next, set up table for updates (CREATE TABLE solarlog_5min_updates, see above), added trigger (log_solarlog_5min_updates, see above, and added constraint solarlog_5min_unique).

Next, ran data import on a single system.

```
$ ui/daily.sh
```

Last, add this to crontab with crontab -e. 

