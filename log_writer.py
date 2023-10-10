"""
Write MAVLink messages to a tlog file.
"""

import struct
import time


class LogWriter:
    def __init__(self, path: str):
        self.path = path
        self.file = open(path, 'wb')

    def write(self, msg):
        """
        Write a 64-bit unsigned timestamp, followed by the packed MAVLink message.
        """
        usec = int(time.time() * 1.0e6)
        usec_buf = bytearray(struct.pack('>Q', usec))
        self.file.write(usec_buf)

        msg_buf = msg.get_msgbuf()
        if msg_buf is None or len(msg_buf) == 0:
            raise "TODO not implemented yet"

        self.file.write(msg_buf)
        self.file.flush()
