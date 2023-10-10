# ArduSub Localization

## Overview

Tools to run ArduSub localization experiments.

There are 2 tools: [SimSensors](sim_sensors.py) and [SimReplay](sim_replay.py).
Both do the following:
* start ardusub and connect to it
* set a bunch of parameters
* send GPS_INPUT and VISION_POSITION_DELTA MAVLink messages
* write the MAVLINK messages to a tlog file

The source of the MAVLink messages differs:
* [SimSensors](sim_sensors.py) simulates a sub moving slowly in a circle
* [SimReplay](sim_replay.py) opens a tlog file and reads the GPS_INPUT and VISION_POSITION_DELTA messages

## Usage

Build ardusub first:
~~~
cd $ARDUPILOT_HOME
./waf configure --board sitl
./waf sub
~~~

To simulate a sub moving slowly in a circle:
~~~
python sim_sensors.py --params params/fusion.params --log /tmp/fusion.tlog --time 180
~~~

To replay a previous dive:
~~~
python sim_replay.py --params params/fusion.params --log /tmp/fusion.tlog --speedup 10.0
~~~

## Caveats

The simulated IMUs (accel, gyro) are indicating no movement, and therefore not aiding the EKF.

The tools do not route or forward MAVLink messages to other systems or components. I.e., QGC will not connect.

## Reference

### Interesting MAVLink Messages

| Message               | Sender  | Value                                            |
|-----------------------|---------|--------------------------------------------------|
| VISION_POSITION_DELTA | Sensor  | DVL sensor data                                  |
| GPS_INPUT             | Sensor  | GPS sensor data                                  |
| GPS_RAW_INT           | ArduSub | GPS sensor data                                  | 
| GLOBAL_POSITION_INT   | ArduSub | EKF output (GPS sensor data until origin is set) |
| LOCAL_POSITION_NED    | ArduSub | EKF output                                       |
| GPS_GLOBAL_ORIGIN     | ArduSub | Origin (sent once when origin is set)            |
| HOME_POSITION         | ArduSub | Origin (sent once when origin is set)            |

### Interesting Dataflash Tables

* VISO is the same data that appears in VISION_POSITION_DELTA
* POS is the same data that appears in GLOBAL_POSITION_INT
