#!/bin/bash

# Sensor modes:
#     UGPS_AND_INTERMITTENT_DVL = 0 (default) -- the UGPS is always on and the DVL turns on/off
#     UGPS_ONLY = 1
#     DVL_ONLY = 2
#     UGPS_AND_DVL = 3

# DVL-only parameters:
source run_sensors.bash params/lutris.params mode_0_lutris 20.0 400 0
source run_sensors.bash params/lutris.params mode_1_lutris 20.0 400 1
source run_sensors.bash params/lutris.params mode_2_lutris 20.0 400 2
source run_sensors.bash params/lutris.params mode_3_lutris 20.0 400 3

# Fusion parameters:
source run_sensors.bash params/fusion.params mode_0_fusion 20.0 400 0
source run_sensors.bash params/fusion.params mode_1_fusion 20.0 400 1
source run_sensors.bash params/fusion.params mode_2_fusion 20.0 400 2
source run_sensors.bash params/fusion.params mode_3_fusion 20.0 400 3
