Data parser for PV data (currently supports Solar-Log)

Maintainer: holger.blasum@urstrom.de

* config.py: Configuration file (password etc)
* pvsystem.py: Abstraction of a PV system.
* solarlog_parse_library.py: Common routines.
* solarlog_parse_database.py: Database backend.
* solarlog_parse.py: Parse Solar-Log files.
* solarlog_parse_urstrom_all.py: Parse all UrStrom systems (example).
* solarlog_parse_filter.py: Filtering SolarLog data (keep production data, remove consumption data) for display on a webserver.
* solarlog_parse_filter_30min.py: Filtering updated data.
  
Database format (PostgreSQL):

```
CREATE TABLE public.solarlog_5min (
    system_id integer DEFAULT 18 NOT NULL,
    tracker_id_text character varying(8) NOT NULL,
    measurement_time timestamp without time zone NOT NULL,
    tz_offset integer,
    yield integer, 
    insertion_time timestamp without time zone,
    inverter_id integer NOT NULL,
    tracker_id integer NOT NULL,
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
