"""Physical value <-> FIT integer conversion."""

from __future__ import annotations

import pytest

from rowing_data.codec import CodecError, decode, encode
from rowing_data.fields import field_by_id, field_by_name


@pytest.mark.parametrize(
    ("field_id", "physical", "raw"),
    [
        (0, 1420, 1420),  # DriveLength mm, scale 1
        (1, 450, 450),  # StrokeDriveTime ms
        (6, 412.3, 4123),  # AverageDriveForceN, scale 10
        (7, 0, 0),  # measured zero is a real value
        (8, 4.0, 1020),  # AverageBoatSpeed, scale 255
        (19, 250, 250),  # StrokeWork J
        (93, 28.50, 2850),  # StrokeRate, scale 100
        (10, 1, 1),  # RecordingStrategy
        (4, 90.5, 905),  # deprecated pounds still encode
    ],
)
def test_developer_encode_decode(field_id: int, physical: float, raw: int) -> None:
    field = field_by_id(field_id)
    assert encode(field, physical) == raw
    decoded = decode(field, raw)
    if field.scale == 1:
        assert decoded == physical
    else:
        assert decoded == pytest.approx(physical)


def test_none_is_omitted_not_placeholder() -> None:
    field = field_by_id(0)
    assert encode(field, None) is None
    assert decode(field, None) is None


def test_native_distance_and_speed_scales() -> None:
    distance = field_by_name("distance")
    assert encode(distance, 2000.12) == 200012
    assert decode(distance, 200012) == pytest.approx(2000.12)

    speed = field_by_name("enhanced_speed")
    assert encode(speed, 4.321) == 4321
    assert decode(speed, 4321) == pytest.approx(4.321)

    frac = field_by_name("fractional_cadence")
    assert encode(frac, 0.5) == 64
    assert decode(frac, 64) == pytest.approx(0.5)

    cycle = field_by_name("cycle_length16")
    assert encode(cycle, 8.50) == 850
    assert decode(cycle, 850) == pytest.approx(8.50)


def test_sint32_position_roundtrip() -> None:
    lat = field_by_name("position_lat")
    raw = encode(lat, -123456789)
    assert raw == -123456789
    assert decode(lat, raw) == -123456789


def test_encode_overflow_raises() -> None:
    force = field_by_id(6)
    # UINT16 max 65535 / scale 10 => 6553.5 N is in range; 7000 N is not.
    with pytest.raises(CodecError, match="AverageDriveForceN"):
        encode(force, 7000)

    cadence = field_by_name("cadence")
    with pytest.raises(CodecError):
        encode(cadence, 300)


def test_uint16_upper_bound_accepted() -> None:
    work = field_by_id(19)
    assert encode(work, 65535) == 65535
    with pytest.raises(CodecError):
        encode(work, 65536)
