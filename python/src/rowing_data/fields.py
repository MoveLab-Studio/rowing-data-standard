"""Machine-readable field registry for Draft v0.1 (core fields).

Developer-field rows match spec/FIT_STANDARD.md and registry/field-ids.md.
Native FIT fields are listed because producers SHOULD use them instead of
reinventing the same quantities as developer fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .constants import (
    CADENCE256_SCALE,
    CYCLE_LENGTH16_SCALE,
    DISTANCE_SCALE,
    ENHANCED_SPEED_SCALE,
)


class MessageType(StrEnum):
    RECORD = "record"
    SESSION = "session"


class BaseType(StrEnum):
    UINT8 = "UINT8"
    UINT16 = "UINT16"
    UINT32 = "UINT32"
    SINT16 = "SINT16"
    SINT32 = "SINT32"


# Integer limits of FIT base types (encoded raw value must fit).
BASE_TYPE_RANGE: dict[BaseType, tuple[int, int]] = {
    BaseType.UINT8: (0, 255),
    BaseType.UINT16: (0, 65535),
    BaseType.UINT32: (0, 4_294_967_295),
    BaseType.SINT16: (-32768, 32767),
    BaseType.SINT32: (-2_147_483_648, 2_147_483_647),
}


@dataclass(frozen=True, slots=True)
class FieldDef:
    """One assigned field: either a standard developer field or a native FIT field."""

    name: str
    message: MessageType
    base_type: BaseType
    scale: float
    units: str
    field_id: int | None = None
    native: bool = False
    deprecated: bool = False
    notes: str = ""


def _dev(
    field_id: int,
    name: str,
    message: MessageType,
    base_type: BaseType,
    scale: float,
    units: str,
    *,
    deprecated: bool = False,
    notes: str = "",
) -> FieldDef:
    return FieldDef(
        name=name,
        message=message,
        field_id=field_id,
        base_type=base_type,
        scale=scale,
        units=units,
        native=False,
        deprecated=deprecated,
        notes=notes,
    )


def _native(
    name: str,
    base_type: BaseType,
    scale: float,
    units: str,
    *,
    notes: str = "",
) -> FieldDef:
    return FieldDef(
        name=name,
        message=MessageType.RECORD,
        field_id=None,
        base_type=base_type,
        scale=scale,
        units=units,
        native=True,
        notes=notes,
    )


# Assigned core developer fields. IDs 11–18, 20–92, 200–211 are later.
DEVELOPER_FIELDS: tuple[FieldDef, ...] = (
    _dev(0, "DriveLength", MessageType.RECORD, BaseType.UINT16, 1, "mm"),
    _dev(1, "StrokeDriveTime", MessageType.RECORD, BaseType.UINT16, 1, "ms"),
    _dev(2, "DragFactor", MessageType.RECORD, BaseType.UINT16, 1, ""),
    _dev(3, "StrokeRecoveryTime", MessageType.RECORD, BaseType.UINT16, 1, "ms"),
    _dev(6, "AverageDriveForce", MessageType.RECORD, BaseType.UINT16, 10, "N"),
    _dev(7, "PeakDriveForce", MessageType.RECORD, BaseType.UINT16, 10, "N"),
    _dev(8, "AverageBoatSpeed", MessageType.RECORD, BaseType.UINT16, 255, "m/s"),
    _dev(
        9,
        "WorkoutState",
        MessageType.RECORD,
        BaseType.UINT8,
        1,
        "",
        notes="Opaque UINT8; the draft has no enum table.",
    ),
    _dev(10, "RecordingStrategy", MessageType.SESSION, BaseType.UINT8, 1, ""),
    _dev(94, "SlipThreshold", MessageType.SESSION, BaseType.UINT16, 1, "N"),
    _dev(95, "WashThreshold", MessageType.SESSION, BaseType.UINT16, 1, "N"),
    _dev(19, "StrokeWork", MessageType.RECORD, BaseType.UINT16, 1, "J"),
    _dev(96, "StrokeState", MessageType.RECORD, BaseType.UINT8, 1, ""),
)

NATIVE_FIELDS: tuple[FieldDef, ...] = (
    _native(
        "timestamp",
        BaseType.UINT32,
        1,
        "s",
        notes="Seconds since Garmin FIT epoch 1989-12-31 UTC.",
    ),
    _native("distance", BaseType.UINT32, DISTANCE_SCALE, "m"),
    _native("cadence", BaseType.UINT8, 1, "spm"),
    _native(
        "cadence256",
        BaseType.UINT16,
        CADENCE256_SCALE,
        "spm",
        notes="Fractional stroke rate; physical = raw / 256. Native record field 52.",
    ),
    _native("heart_rate", BaseType.UINT8, 1, "bpm"),
    _native("power", BaseType.UINT16, 1, "W"),
    _native("enhanced_speed", BaseType.UINT32, ENHANCED_SPEED_SCALE, "m/s"),
    _native("position_lat", BaseType.SINT32, 1, "semicircles"),
    _native("position_long", BaseType.SINT32, 1, "semicircles"),
    _native("total_cycles", BaseType.UINT32, 1, ""),
    _native(
        "cycle_length16",
        BaseType.UINT16,
        CYCLE_LENGTH16_SCALE,
        "m",
        notes=(
            "Distance the boat travels during one stroke cycle. "
            "Not cumulative distance, and not handle travel (DriveLength)."
        ),
    ),
)

_BY_ID: dict[int, FieldDef] = {
    field.field_id: field for field in DEVELOPER_FIELDS if field.field_id is not None
}
_BY_NAME: dict[str, FieldDef] = {
    field.name: field for field in (*DEVELOPER_FIELDS, *NATIVE_FIELDS)
}


def field_by_id(field_id: int) -> FieldDef:
    """Return the developer field assigned to ``field_id``."""
    try:
        return _BY_ID[field_id]
    except KeyError as exc:
        raise KeyError(f"No developer field with ID {field_id}") from exc


def field_by_name(name: str) -> FieldDef:
    """Return a developer or native field by its canonical name."""
    try:
        return _BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"Unknown field name {name!r}") from exc
