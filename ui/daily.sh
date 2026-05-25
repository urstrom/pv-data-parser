#!/bin/bash
BACKLOG=5
if [ "$#" -gt 0 ]; then
    SYSTEM="$1"
fi
if [ "$#" -gt 1 ]; then
    BACKLOG="$2"
fi
export ANALYSIS_BEGIN=`date -d "-$BACKLOG days" "+%Y-%m-%d"`
export ANALYSIS_END=`date -d "yesterday" "+%Y-%m-%d"`
(cd $HOME/pv-data-parser && export PYTHONPATH=. && python3 ui/db_import_from_pickle_urstrom_all.py $ANALYSIS_BEGIN $ANALYSIS_END $SYSTEM) > ~/pv-data-parser/log/cron-sunshine-$ANALYSIS_END-parse 2>&1
