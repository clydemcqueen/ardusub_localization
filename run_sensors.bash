#!/bin/bash

# Run sim_sensors and use ardusub_log_tools to process the files

# Usage:
# run_sensors.bash <params> <run_name> <speedup> <time> <mode>

# Example:
# run_sensors params/fusion.params fusion 2.0 150 0

PARAMS=$1
RUN_NAME=$2
SPEEDUP=$3
DURATION=$4
MODE=$5

echo "##########################"
echo ">>> RUNNING SIMULATION <<<"
echo "##########################"

python sim_sensors.py --params ${PARAMS} --log /tmp/${RUN_NAME}.tlog --speedup ${SPEEDUP} --time ${DURATION} --mode ${MODE}

echo "############################"
echo ">>> PROCESSING LOG FILES <<<"
echo "############################"

# Using pymavlink tools
mavlogdump.py --types GPS_INPUT --format csv /tmp/${RUN_NAME}.tlog > /tmp/${RUN_NAME}_GPS_INPUT.csv
mavlogdump.py --types GLOBAL_POSITION_INT --format csv /tmp/${RUN_NAME}.tlog > /tmp/${RUN_NAME}_GLOBAL_POSITION_INT.csv

# Using https://github.com/clydemcqueen/ardusub_log_tools
# show_types.py /tmp/${RUN_NAME}.tlog
# export TLOG_MERGE_MSGS=GLOBAL_POSITION_INT,GPS_INPUT,GPS_RAW_INT,LOCAL_POSITION_NED,VISION_POSITION_DELTA,SIMSTATE
# tlog_merge.py --types ${TLOG_MERGE_MSGS} --rate /tmp/${RUN_NAME}.tlog
