#!/bin/bash

# Run sim_replay and use ardusub_log_tools to process the files

# Usage:
# run_replay.bash <params> <run_name> <speedup> <tlog_to_replay>
# run_replay params/fusion.params fusion 2.0 lutris.tlog

echo "##########################"
echo ">>> RUNNING SIMULATION <<<"
echo "##########################"

python sim_replay.py --params $1 --log /tmp/$2.tlog --speedup $3 $4

echo "############################"
echo ">>> PROCESSING LOG FILES <<<"
echo "############################"

export TLOG_MERGE_MSGS=GLOBAL_POSITION_INT,GPS_INPUT,GPS_RAW_INT,LOCAL_POSITION_NED,VISION_POSITION_DELTA
tlog_map_maker.py /tmp/$2.tlog
tlog_merge.py --types TLOG_MERGE_MSGS --rate /tmp/$2.tlog
