"""
Run an ArduSub simulation.
"""

import os
import subprocess
import time

from pymavlink.dialects.v20 import ardupilotmega as apm2

import position
import log_writer

# Use MAVLink2 wire protocol, must include this before importing pymavlink.mavutil
os.environ['MAVLINK20'] = '1'

# Late import
from pymavlink import mavutil

import param


def run_cmd(cmd):
    try:
        p = subprocess.Popen(cmd)
        return p.pid
    except Exception as e:
        print(f"SIM RUNNER: exception occurred with command: '{' '.join(cmd)}'")
        print(f'SIM RUNNER: {e}')
        return 0


# TODO the origin is off by the radius
def start_ardusub(speedup: float):
    ardupilot_home = os.environ.get('ARDUPILOT_HOME')
    print('SIM RUNNER: starting ArduSub')
    pid = run_cmd([
        f'{ardupilot_home}/build/sitl/bin/ardusub',
        '-S',
        '-w',
        '--model', 'vectored',
        '--speedup', f'{speedup :.2f}',
        '--slave', '0',
        '--defaults', f'{ardupilot_home}/Tools/autotest/default_params/sub.parm',
        '--sim-address=127.0.0.1',
        '-I0',
        '--home', f'{position.Position.ORIGIN.lat},{position.Position.ORIGIN.lon},-0.1,0.0',
    ])

    if pid == 0:
        print('SIM RUNNER: ArduSub failed to start')
        exit(1)
    else:
        return pid


class SimRunner:
    """
    Manage a simulation. Subclasses should call receive_all_messages() periodically.

    Limitation: this class connects directly to ArduSub and does not route MAVLink messages.
    I.e., you cannot use this class with another ground control station like QGroundControl.
    """

    REQUEST_MSG_IDS = [
        apm2.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
        apm2.MAVLINK_MSG_ID_GPS_RAW_INT,
        apm2.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
        apm2.MAVLINK_MSG_ID_SIMSTATE,
    ]

    REQUEST_MSG_RATE = 3  # Hz

    GPS_MSGS = ['GPS_RAW_INT', 'GLOBAL_POSITION_INT']

    SPAMMY_PARAMS = ['BARO1_GND_PRESS', 'BARO2_GND_PRESS', 'STAT_RUNTIME', 'STAT_FLTTIME']

    def __init__(self, params_path: str or None, log_path: str or None, speedup: float):
        # Start the clock
        self.start = time.time()
        self.speedup = speedup

        self.print(f'run at {speedup}X wall time')

        if log_path:
            self.print(f'logging to {log_path}')
            self.log_writer = log_writer.LogWriter(log_path)
        else:
            self.print('not logging')
            self.log_writer = None

        self.ardusub_pid = start_ardusub(speedup)

        self.print('connecting to ArduSub...')
        self.ardusub = mavutil.mavlink_connection(
            'tcp:127.0.0.1:5760', source_system=255, source_component=0, autoreconnect=True)

        self.print('connected, waiting for a HEARTBEAT message...')
        self.ardusub.wait_heartbeat()
        self.print('HEARTBEAT received')

        if params_path:
            self.set_params(param.parse_params(params_path))

        self.request_msgs()

        # True if we've seen the "ArduPilot ready" message
        self.ardusub_ready = False

        # True if the AHRS origin has been set
        self.ardusub_origin = False

    def sim_time(self):
        return (time.time() - self.start) * self.speedup

    def print(self, message):
        print(f'[{self.sim_time() :.2f}] {message}')

    def print_ardusub(self, level, message):
        print(f'[{self.sim_time() :.2f}] ardusub {level}: {message}')

    def send_to_ardusub(self, msg):
        """
        Send a message to ArduSub.
        send() will pack the message as a side effect, so call it first.
        """
        self.ardusub.mav.send(msg)
        if self.log_writer:
            self.log_writer.write(msg)

    def set_params(self, params: list[param.Param]):
        self.print('setting parameters')
        for p in params:
            self.send_to_ardusub(p.get_set_param_msg())

    def request_msg(self, msg_id: int, msg_rate: int):
        self.print(f'request {msg_rate}Hz rate for message id {msg_id}')
        self.send_to_ardusub(apm2.MAVLink_command_long_message(
            1, 1, apm2.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
            msg_id, int(1e6 / msg_rate), 0, 0, 0, 0, 0))

    def request_msgs(self):
        """
        Request a list of interesting messages.
        """
        for msg_type in SimRunner.REQUEST_MSG_IDS:
            self.request_msg(msg_type, SimRunner.REQUEST_MSG_RATE)

    @staticmethod
    def severity_name(severity: int) -> str:
        if severity == apm2.MAV_SEVERITY_CRITICAL:
            return 'CRITICAL'
        elif severity == apm2.MAV_SEVERITY_WARNING:
            return 'WARNING'
        elif severity == apm2.MAV_SEVERITY_INFO:
            return 'INFO'
        else:
            return 'unknown'

    def recv_messages_from_ardusub(self):
        """
        Receive all queued messages and log them.
        Normally this is pretty quick, but if QGC starts up we will see a zillion PARAM_VALUE messages.
        """
        while msg := self.ardusub.recv_match():
            msg_type: str = msg.get_type()
            if msg_type == 'PARAM_VALUE':
                if msg.param_id not in SimRunner.SPAMMY_PARAMS:
                    self.print(f'{msg.param_id} = {msg.param_value}')
            elif msg_type == 'COMMAND_ACK':
                # Ignore MAV_CMD_GET_HOME_POSITION errors -- spammy
                if msg.command != apm2.MAV_CMD_GET_HOME_POSITION:
                    self.print(f'command {msg.command} was acknowledged with result {msg.result}')
            elif msg_type == 'STATUSTEXT':
                if msg.text == 'ArduPilot Ready':
                    self.ardusub_ready = True
                if msg.text != 'Field Elevation Set: 0m':
                    self.print_ardusub(SimRunner.severity_name(msg.severity), msg.text)
            elif msg_type == 'HOME_POSITION':
                self.print_ardusub(msg_type, f'({msg.latitude}, {msg.longitude}), ({msg.x}, {msg.y})')
                self.ardusub_origin = True
            elif msg_type == 'GPS_GLOBAL_ORIGIN':
                self.print_ardusub(msg_type, f'({msg.latitude}, {msg.longitude})')
                self.ardusub_origin = True

            if self.log_writer and (self.ardusub_origin or msg.get_type() not in SimRunner.GPS_MSGS):
                self.log_writer.write(msg)
