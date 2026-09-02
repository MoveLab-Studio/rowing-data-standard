"""Constants for Draft v0.1 of the Rowing Data Standard.

The application UUID is uuid5(NAMESPACE_DNS, "rowingdata") and MUST be written
as a 16-byte array in FIT DeveloperDataIdMessage.
"""

from __future__ import annotations

from enum import IntEnum
from uuid import NAMESPACE_DNS, UUID, uuid5

# Draft version this package implements. Not a ratified standard.
STANDARD_VERSION = "0.1"

APPLICATION_UUID: UUID = uuid5(NAMESPACE_DNS, "rowingdata")
APPLICATION_ID: bytes = APPLICATION_UUID.bytes

# Garmin FIT timestamps count seconds from 1989-12-31 00:00:00 UTC.
# Native `timestamp` uses this epoch (seconds), despite the draft table saying
# milliseconds — that wording is a FIT-profile mismatch, not a second epoch.
FIT_EPOCH_UNIX = 631065600

# Native FIT field scales: physical = raw / scale (FIT profile convention).
DISTANCE_SCALE = 100  # metres
ENHANCED_SPEED_SCALE = 1000  # m/s
CYCLE_LENGTH16_SCALE = 100  # metres
FRACTIONAL_CADENCE_SCALE = 128  # fraction of 1 spm


class RecordingStrategy(IntEnum):
    """Session developer field ID 10."""

    UNKNOWN = 0
    STROKE_BOUNDARY = 1
    GPS_UPDATE = 2
