#!/bin/bash

# Run sim_sensors and use ardusub_log_tools to process the files

# Usage:
# run_sensors.bash <params> <run_name> <time>
# run_sensors params/fusion.params fusion 150

echo "##########################"
echo ">>> RUNNING SIMULATION <<<"
echo "##########################"

python sim_sensors.py --params $1 --log /tmp/$2.tlog --time $3

echo "############################"
echo ">>> PROCESSING LOG FILES <<<"
echo "############################"

export TLOG_MERGE_MSGS=GLOBAL_POSITION_INT,GPS_INPUT,GPS_RAW_INT,LOCAL_POSITION_NED,VISION_POSITION_DELTA
tlog_map_maker.py /tmp/$2.tlog
tlog_merge.py --types $TLOG_MERGE_MSGS --rate /tmp/$2.tlog
