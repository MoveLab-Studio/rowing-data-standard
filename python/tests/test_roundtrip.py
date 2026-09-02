"""Reader, validator, and write/read round-trip."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rowing_data import read_fit, validate, write_fit
from rowing_data.constants import RecordingStrategy
from rowing_data.model import Record, RowingSession
from sample_sessions import gps_update_session, stroke_boundary_session


def test_roundtrip_stroke_boundary(tmp_path: Path) -> None:
    original = stroke_boundary_session()
    path = tmp_path / "stroke.fit"
    write_fit(original, path)
    loaded = read_fit(path)

    assert loaded.recording_strategy is RecordingStrategy.STROKE_BOUNDARY
    assert len(loaded.records) == len(original.records)
    assert loaded.laps
    assert loaded.records[0].lap_index == 0
    for got, want in zip(loaded.records, original.records, strict=True):
        _assert_record_roundtrip(got, want)
    assert loaded.stroke_counts() == [0, 1, 1]
    assert validate(loaded) == []


def test_roundtrip_gps_update(tmp_path: Path) -> None:
    original = gps_update_session()
    path = tmp_path / "gps.fit"
    write_fit(original, path)
    loaded = read_fit(path)

    assert loaded.recording_strategy is RecordingStrategy.GPS_UPDATE
    assert loaded.stroke_counts() == [0, 0, 2]
    for got, want in zip(loaded.records, original.records, strict=True):
        _assert_record_roundtrip(got, want)
        assert got.position_lat == pytest.approx(want.position_lat, abs=2)
        assert got.position_long == pytest.approx(want.position_long, abs=2)


def test_validate_warns_on_typical_range_and_timing() -> None:
    session = RowingSession(
        recording_strategy=RecordingStrategy.STROKE_BOUNDARY,
        records=(
            Record(
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                stroke_rate=24.0,
                drive_length_mm=2200,
                stroke_drive_time_ms=400,
                stroke_recovery_time_ms=400,
            ),
        ),
    )
    issues = validate(session)
    codes = {issue.code for issue in issues}
    assert "typical_range" in codes
    assert "stroke_timing" in codes
    assert all(issue.level == "warning" for issue in issues)


def test_validate_overflow_is_error() -> None:
    session = RowingSession(
        records=(
            Record(
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                average_drive_force_n=7000,
            ),
        )
    )
    issues = validate(session)
    assert any(issue.level == "error" and issue.code == "overflow" for issue in issues)


def _assert_record_roundtrip(got: Record, want: Record) -> None:
    assert got.timestamp == want.timestamp
    if want.distance_m is not None:
        assert got.distance_m == pytest.approx(want.distance_m, abs=0.01)
    assert got.total_cycles == want.total_cycles
    assert got.resolved_stroke_rate() == pytest.approx(want.resolved_stroke_rate())
    assert got.drive_length_mm == want.drive_length_mm
    assert got.stroke_drive_time_ms == want.stroke_drive_time_ms
    assert got.stroke_recovery_time_ms == want.stroke_recovery_time_ms
    if want.average_drive_force_n is not None:
        assert got.average_drive_force_n == pytest.approx(want.average_drive_force_n)
    if want.peak_drive_force_n is not None:
        assert got.peak_drive_force_n == pytest.approx(want.peak_drive_force_n)
    assert got.stroke_work_j == want.stroke_work_j
    assert got.heart_rate == want.heart_rate
    assert got.power == want.power
    if want.cycle_length_m is not None:
        assert got.cycle_length_m == pytest.approx(want.cycle_length_m, abs=0.01)
    if want.enhanced_speed_mps is not None:
        assert got.enhanced_speed_mps == pytest.approx(
            want.enhanced_speed_mps, abs=0.001
        )
