"""
Utilities to set parameters.

These params are already set in ArduSub 4.1:
        AHRS_EKF_TYPE, apm2.MAV_PARAM_TYPE_UINT8, 3
        EK2_ENABLE, apm2.MAV_PARAM_TYPE_UINT8, 0
        EK3_ENABLE, apm2.MAV_PARAM_TYPE_UINT8, 1

This param was removed from ArduSub 4.1:
        EK3_GPS_TYPE, apm2.MAV_PARAM_TYPE_UINT8, 3
"""

from enum import IntEnum
from typing import NamedTuple

from pymavlink.dialects.v20 import ardupilotmega as apm2


# For source switching: param files should have SRC1 when the DVL is off, and SRC2 when the DVL is on
MULTI_SRC_DVL_OFF = 1
MULTI_SRC_DVL_ON = 2

# For reference only, see param files for the actual values
VISO_TYPE_MAVLINK = 1
GPS_TYPE_MAVLINK = 14
RANGEFINDER_TYPE_MAVLINK = 10


# Copied from the C++ code for reference
class SourceXY(IntEnum):
    NONE = 0,
    # BARO = 1 (not applicable)
    # RANGEFINDER = 2 (not applicable)
    GPS = 3,
    BEACON = 4,
    OPTFLOW = 5,
    EXTNAV = 6,
    WHEEL_ENCODER = 7


class SourceZ(IntEnum):
    NONE = 0,
    BARO = 1,
    RANGEFINDER = 2,
    GPS = 3,
    BEACON = 4,
    # OPTFLOW = 5 (not applicable, optical flow can be used for terrain alt but not relative or absolute alt)
    EXTNAV = 6
    # WHEEL_ENCODER = 7 (not applicable)


class SourceYaw(IntEnum):
    NONE = 0,
    COMPASS = 1,
    GPS = 2,
    GPS_COMPASS_FALLBACK = 3,
    EXTNAV = 6,
    GSF = 8


class Param(NamedTuple):
    id : bytes
    value: float
    type: int

    def get_set_param_msg(self) -> apm2.MAVLink_param_set_message:
        return apm2.MAVLink_param_set_message(1, 1, self.id, self.value, self.type)


def parse_param(line: str) -> Param or None:
    try:
        # Split on whitespace (tabs, spaces)
        fields = line.split()
        return Param(bytes(fields[2], 'ascii'), float(fields[3]), int(fields[4]))
    except Exception as e:
        print(f'exception "{e}" parsing "{line}"')
        return None


def parse_params(path) -> list[Param]:
    result = []
    with open(path) as file:
        for line in file:
            if len(line) < 2 or line.startswith('#'):
                continue
            param = parse_param(line)
            if param is not None:
                result.append(param)
    return result
