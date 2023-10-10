#!/usr/bin/env python3

"""
Replay VISION_POSITION_DELTA and GPS_INPUT sensor messages.

Caveat: I've tested speedup as high as 10.0. I am seeing odd / missing messages from mavproxy when speedup > 1.0, but
results are still interesting.
"""

import argparse
import os
import time

# Use MAVLink2 wire protocol, must include this before importing pymavlink.mavutil
os.environ['MAVLINK20'] = '1'

# Late import
from pymavlink import mavutil

import sim_runner

# TODO the delay between GPS_RAW_INT and GLOBAL_POSITION_INT is large... what is going on?
# TODO is it possible to run simulation using the timestamps from the tlog file we're reading?


class SimReplay(sim_runner.SimRunner):
    REPLAY_MSGS = ['VISION_POSITION_DELTA', 'GPS_INPUT']

    def __init__(self, replay_path: str, params_path: str | None, log_path: str | None, speedup: float):
        super().__init__(params_path, log_path, speedup)
        self.replay_tlog = mavutil.mavlink_connection(replay_path)

    def run(self) -> None:
        self.print('replay started')
        now_msg1 = None
        timestamp_msg1 = None
        msg_types = []
        msg_count = 0

        while (msg := self.replay_tlog.recv_match(blocking=False, type=SimReplay.REPLAY_MSGS)) is not None:
            self.recv_messages_from_ardusub()

            timestamp_msg = getattr(msg, '_timestamp', 0.0)
            now = time.time()

            if now_msg1 is None:
                # Track the current time and the timestamp for msg1
                now_msg1 = now
                timestamp_msg1 = timestamp_msg
                self.print(f'delta is {now_msg1 - timestamp_msg1 :.2f} seconds')
            else:
                # Calc how long we'll need to wait to send this message
                d_wait = (timestamp_msg - timestamp_msg1) / self.speedup - (now - now_msg1)
                if d_wait > 0.0:
                    time.sleep(d_wait)

            self.send_to_ardusub(msg)
            msg_count += 1

            msg_type = msg.get_type()
            if msg_type not in msg_types:
                self.print(f'replay first {msg_type} message')
                msg_types.append(msg_type)

            if msg_count % 1000 == 0:
                elapsed_s = timestamp_msg - timestamp_msg1
                elapsed_m = elapsed_s / 60.0
                self.print(f'sent {msg_count} messages, elapsed sim time {elapsed_s :.2f}s ({elapsed_m :.2f}m)')

        self.print('simulation stopped')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)
    parser.add_argument('--params', type=str, default=None, help='path of parameter file')
    parser.add_argument('--log', type=str, default=None, help='write a new log')
    parser.add_argument('--speedup', type=float, default=1.0, help='SIM_SPEEDUP value')
    parser.add_argument('path')
    args = parser.parse_args()
    runner = SimReplay(args.path, args.params, args.log, args.speedup)
    runner.run()


if __name__ == '__main__':
    main()
