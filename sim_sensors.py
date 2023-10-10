#!/usr/bin/env python3

"""
Demonstrate sensor fusion with two sensors: a MAVLink DVL and a MAVLink UGPS (Underwater GPS).
"""

import argparse
import math
import time

from pymavlink.dialects.v20 import ardupilotmega as apm2

import param
import position
import sim_runner


def default_heartbeat_msg() -> apm2.MAVLink_heartbeat_message:
    """
    Build a HEARTBEAT message using a particular dialect, overriding the conn dialect.
    This also helps Pycharm (and presumably other IDEs) provide features like "go to type".
    mavlink_version=3 refers to the xml message format version, not the wire protocol version.
    """
    return apm2.MAVLink_heartbeat_message(
        apm2.MAV_TYPE_CAMERA, apm2.MAV_AUTOPILOT_INVALID, 0, 0, 0, 3)


def default_vision_position_delta_msg() -> apm2.MAVLink_vision_position_delta_message:
    time_usec = 0  # Same as WL DVL extension
    time_delta_usec = int(1000000 * SimSensors.FAST_LOOP_PERIOD)
    confidence = 99.8

    # Updated per tick:
    angle_delta = [0.0, 0.0, 0.0]
    position_delta = [0.0, 0.0, 0.0]

    return apm2.MAVLink_vision_position_delta_message(
        time_usec, time_delta_usec, angle_delta, position_delta, confidence)


def default_gps_input_msg() -> apm2.MAVLink_gps_input_message:
    # Matches the WL UGPS extension:
    time_usec = 0
    gps_id = 0
    ignore_flags = (apm2.GPS_INPUT_IGNORE_FLAG_ALT |
                    apm2.GPS_INPUT_IGNORE_FLAG_VEL_HORIZ |
                    apm2.GPS_INPUT_IGNORE_FLAG_VEL_VERT |
                    apm2.GPS_INPUT_IGNORE_FLAG_SPEED_ACCURACY |
                    apm2.GPS_INPUT_IGNORE_FLAG_VERTICAL_ACCURACY)

    # These fields are ignored by ArduSub:
    alt = 0
    vn = 0
    ve = 0
    vd = 0
    speed_accuracy = 0
    vert_accuracy = 0
    yaw = 0  # 0 means "invalid yaw"

    # Reasonable values?
    fix_type = 3
    hdop = 1  # Must be <= 2.5 for NavEKF3_core::calcGpsGoodToAlign() to succeed
    horiz_accuracy = 0
    vdop = 4
    satellites_visible = 10

    # Hmm... are these used?
    time_week_ms = 0
    time_week = 0

    # Updated per tick:
    lat = 0
    lon = 0

    return apm2.MAVLink_gps_input_message(time_usec, gps_id, ignore_flags, time_week_ms,
                                          time_week, fix_type, lat, lon, alt, hdop, vdop, vn, ve,
                                          vd, speed_accuracy, horiz_accuracy, vert_accuracy,
                                          satellites_visible, yaw)


# TODO handle --speedup
class SimSensors(sim_runner.SimRunner):
    FAST_LOOP_PERIOD = 0.2
    SLOW_LOOP_COUNT = 5

    def __init__(self, params_path: str, log_path: str, duration: int, switch: bool, ):
        print(f'SIM SENSORS: run for {duration}s')
        super().__init__(params_path, log_path, 1.0)
        self.duration = duration
        self.switch = switch
        self.heartbeat_msg = default_heartbeat_msg()
        self.vision_position_delta_msg = default_vision_position_delta_msg()
        self.gps_input_msg = default_gps_input_msg()
        self.position = position.Position()
        self.dvl_is_active = False

    def set_ekf_src(self, n: int):
        """
        Select an EKF source set. Is this supported on the Sub-4.1 branch?
        """
        print(f'SIM SENSORS: switching EKF to SRC{n}')
        self.send_to_ardusub(apm2.MAVLink_command_long_message(
            1, 1, apm2.MAV_CMD_SET_EKF_SOURCE_SET, 0,
            n, 0, 0, 0, 0, 0, 0))

    def slow_loop(self):
        self.send_to_ardusub(self.heartbeat_msg)
        self.gps_input_msg.lat, self.gps_input_msg.lon = self.position.noisy_gps()
        self.send_to_ardusub(self.gps_input_msg)

    def fast_loop(self):
        self.recv_messages_from_ardusub()

        self.position.update(SimSensors.FAST_LOOP_PERIOD)

        dvl_should_be_active = self.position.theta > math.pi
        if self.dvl_is_active != dvl_should_be_active:
            if dvl_should_be_active:
                print('SIM SENSORS: DVL on')
                if self.switch:
                    self.set_ekf_src(param.MULTI_SRC_DVL_ON)
            else:
                print('SIM SENSORS: DVL off')
                if self.switch:
                    self.set_ekf_src(param.MULTI_SRC_DVL_OFF)
            self.dvl_is_active = dvl_should_be_active

        if self.dvl_is_active:
            self.vision_position_delta_msg.angle_delta = self.position.angle_delta
            self.vision_position_delta_msg.position_delta = self.position.position_delta
            self.send_to_ardusub(self.vision_position_delta_msg)

    def run(self) -> None:
        print(f'SIM SENSORS: simulation started')
        count = 0
        start = time.time()

        while time.time() - start < self.duration:
            time.sleep(SimSensors.FAST_LOOP_PERIOD)
            if count % SimSensors.SLOW_LOOP_COUNT == 0:
                self.slow_loop()
            self.fast_loop()
            count += 1

        print(f'SIM SENSORS: simulation stopped')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)
    parser.add_argument('--params', type=str, default=None, help='path of parameter file')
    parser.add_argument('--log', type=str, default=None, help='enable logging')
    parser.add_argument('--time', type=int, default=60, help='how long to run the simulation')
    parser.add_argument('--switch', action='store_true', help='switch EKF sources when DVL goes on/off')
    args = parser.parse_args()
    runner = SimSensors(args.params, args.log, args.time, args.switch)
    runner.run()


if __name__ == '__main__':
    main()
