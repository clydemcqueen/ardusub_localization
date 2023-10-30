#!/bin/bash

# Run sim_replay and use ardusub_log_tools to process the files

# Usage:
# run_replay.bash <params> <run_name> <speedup> <tlog_to_replay>
# run_replay params/fusion.params fusion 2.0 lutris.tlog

PARAMS=$1
RUN_NAME=$2
SPEEDUP=$3
TLOG_FILE=$4

echo "##########################"
echo ">>> RUNNING SIMULATION <<<"
echo "##########################"

python sim_replay.py --params ${PARAMS} --log /tmp/${RUN_NAME}.tlog --speedup ${SPEEDUP} ${TLOG_FILE}

echo "############################"
echo ">>> PROCESSING LOG FILES <<<"
echo "############################"

# Using pymavlink tools
mavlogdump.py --types GPS_INPUT --format csv /tmp/${RUN_NAME}.tlog > /tmp/${RUN_NAME}_GPS_INPUT.csv
mavlogdump.py --types GLOBAL_POSITION_INT --format csv /tmp/${RUN_NAME}.tlog > /tmp/${RUN_NAME}_GLOBAL_POSITION_INT.csv

# Using https://github.com/clydemcqueen/ardusub_log_tools
# show_types.py /tmp/${RUN_NAME}.tlog
# export TLOG_MERGE_MSGS=GLOBAL_POSITION_INT,GPS_INPUT,GPS_RAW_INT,LOCAL_POSITION_NED,VISION_POSITION_DELTA,SIMSTATE
# tlog_merge.py --types TLOG_MERGE_MSGS --rate /tmp/${RUN_NAME}.tlog
