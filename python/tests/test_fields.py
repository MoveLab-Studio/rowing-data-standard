"""Registry matches Draft v0.1 assigned Level 1–2 fields."""

from __future__ import annotations

from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest

from rowing_data import APPLICATION_ID, APPLICATION_UUID, STANDARD_VERSION
from rowing_data.constants import RecordingStrategy
from rowing_data.fields import (
    DEVELOPER_FIELDS,
    NATIVE_FIELDS,
    BaseType,
    MessageType,
    field_by_id,
    field_by_name,
)

# (id, name, message, base_type, scale, units, deprecated)
EXPECTED_DEVELOPER = (
    (0, "DriveLength", MessageType.RECORD, BaseType.UINT16, 1, "mm", False),
    (1, "StrokeDriveTime", MessageType.RECORD, BaseType.UINT16, 1, "ms", False),
    (2, "DragFactor", MessageType.RECORD, BaseType.UINT16, 1, "", False),
    (3, "StrokeRecoveryTime", MessageType.RECORD, BaseType.UINT16, 1, "ms", False),
    (4, "AverageDriveForceLbs", MessageType.RECORD, BaseType.UINT16, 10, "lbs", True),
    (5, "PeakDriveForceLbs", MessageType.RECORD, BaseType.UINT16, 10, "lbs", True),
    (6, "AverageDriveForceN", MessageType.RECORD, BaseType.UINT16, 10, "N", False),
    (7, "PeakDriveForceN", MessageType.RECORD, BaseType.UINT16, 10, "N", False),
    (8, "AverageBoatSpeed", MessageType.RECORD, BaseType.UINT16, 255, "m/s", False),
    (9, "WorkoutState", MessageType.RECORD, BaseType.UINT8, 1, "", False),
    (10, "RecordingStrategy", MessageType.SESSION, BaseType.UINT8, 1, "", False),
    (19, "StrokeWork", MessageType.RECORD, BaseType.UINT16, 1, "J", False),
    (93, "StrokeRate", MessageType.RECORD, BaseType.UINT16, 100, "spm", False),
)

EXPECTED_NATIVE_SCALES = {
    "timestamp": (BaseType.UINT32, 1, "s"),
    "distance": (BaseType.UINT32, 100, "m"),
    "cadence": (BaseType.UINT8, 1, "spm"),
    "fractional_cadence": (BaseType.UINT8, 128, "spm"),
    "heart_rate": (BaseType.UINT8, 1, "bpm"),
    "power": (BaseType.UINT16, 1, "W"),
    "enhanced_speed": (BaseType.UINT32, 1000, "m/s"),
    "position_lat": (BaseType.SINT32, 1, "semicircles"),
    "position_long": (BaseType.SINT32, 1, "semicircles"),
    "total_cycles": (BaseType.UINT32, 1, ""),
    "cycle_length16": (BaseType.UINT16, 100, "m"),
}


def test_standard_version_is_draft_0_1() -> None:
    assert STANDARD_VERSION == "0.1"


def test_application_uuid_is_uuid5_dns_rowingdata() -> None:
    expected = uuid5(NAMESPACE_DNS, "rowingdata")
    assert APPLICATION_UUID == expected
    assert APPLICATION_UUID == UUID("89e86158-6d47-5c98-9d46-7d29437f27b9")
    assert APPLICATION_ID == expected.bytes
    assert len(APPLICATION_ID) == 16


def test_developer_fields_match_draft_tables() -> None:
    by_id = {field.field_id: field for field in DEVELOPER_FIELDS}
    assert set(by_id) == {row[0] for row in EXPECTED_DEVELOPER}
    for field_id, name, message, base_type, scale, units, deprecated in (
        EXPECTED_DEVELOPER
    ):
        field = by_id[field_id]
        assert field.name == name
        assert field.message == message
        assert field.base_type == base_type
        assert field.scale == scale
        assert field.units == units
        assert field.deprecated is deprecated
        assert field.native is False


def test_developer_field_ids_are_unique() -> None:
    ids = [field.field_id for field in DEVELOPER_FIELDS]
    assert len(ids) == len(set(ids))


def test_field_lookup() -> None:
    assert field_by_id(93).name == "StrokeRate"
    assert field_by_name("DriveLength").field_id == 0
    assert field_by_name("cadence").native is True
    with pytest.raises(KeyError):
        field_by_id(11)
    with pytest.raises(KeyError):
        field_by_name("not-a-field")


def test_native_field_scales_match_spec_section_4() -> None:
    by_name = {field.name: field for field in NATIVE_FIELDS}
    assert set(by_name) == set(EXPECTED_NATIVE_SCALES)
    for name, (base_type, scale, units) in EXPECTED_NATIVE_SCALES.items():
        field = by_name[name]
        assert field.native is True
        assert field.field_id is None
        assert field.message == MessageType.RECORD
        assert field.base_type == base_type
        assert field.scale == scale
        assert field.units == units


def test_recording_strategy_enum() -> None:
    assert RecordingStrategy.UNKNOWN == 0
    assert RecordingStrategy.STROKE_BOUNDARY == 1
    assert RecordingStrategy.GPS_UPDATE == 2
