"""FIT writer emits the standard application ID and Level 1–2 fields."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fitparse import FitFile

from rowing_data import APPLICATION_ID, APPLICATION_UUID, write_fit
from rowing_data.codec import CodecError
from rowing_data.constants import RecordingStrategy
from rowing_data.model import Record, RowingSession


def _ts(second: int) -> datetime:
    return datetime(2026, 1, 1, 12, 0, second, tzinfo=UTC)


def _session(
    *records: Record,
    strategy: RecordingStrategy = RecordingStrategy.STROKE_BOUNDARY,
) -> RowingSession:
    return RowingSession(records=records, recording_strategy=strategy)


def _app_id(fit: FitFile) -> bytes:
    messages = list(fit.get_messages("developer_data_id"))
    assert messages, "missing developer_data_id"
    value = messages[0].get_value("application_id")
    if isinstance(value, bytes):
        return value
    return bytes(value)


def test_write_fit_requires_records(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no records"):
        write_fit(RowingSession(records=()), tmp_path / "empty.fit")


def test_writer_application_id_and_recording_strategy(tmp_path: Path) -> None:
    path = tmp_path / "core.fit"
    write_fit(
        _session(
            Record(
                timestamp=_ts(0),
                distance_m=0.0,
                total_cycles=1,
                stroke_rate=28.5,
                drive_length_mm=1420,
                stroke_work_j=0,
                average_drive_force_n=412.3,
            ),
            Record(
                timestamp=_ts(2),
                distance_m=10.5,
                total_cycles=2,
                stroke_rate=28.5,
                drive_length_mm=1410,
            ),
        ),
        path,
    )
    fit = FitFile(str(path), check_crc=True)
    assert _app_id(fit) == APPLICATION_ID
    assert APPLICATION_UUID.bytes == APPLICATION_ID

    descriptions = {
        msg.get_value("field_definition_number"): msg.get_value("field_name")
        for msg in fit.get_messages("field_description")
    }
    assert descriptions[10] == "RecordingStrategy"
    assert descriptions[93] == "StrokeRate"
    assert descriptions[0] == "DriveLength"
    assert descriptions[19] == "StrokeWork"
    assert descriptions[6] == "AverageDriveForceN"
    assert 7 not in descriptions  # omitted PeakDriveForceN

    sessions = list(fit.get_messages("session"))
    strategy = next(field for field in sessions[0] if field.name == "RecordingStrategy")
    assert strategy.value == RecordingStrategy.STROKE_BOUNDARY

    records = list(fit.get_messages("record"))
    assert len(records) == 2
    first = records[0]
    assert first.get_value("cadence") == 28
    frac = first.get("fractional_cadence")
    assert frac is not None
    assert frac.raw_value == 64
    stroke_rate = next(field for field in first if field.name == "StrokeRate")
    assert stroke_rate.raw_value == 2850
    drive = next(field for field in first if field.name == "DriveLength")
    assert drive.raw_value == 1420
    work = next(field for field in first if field.name == "StrokeWork")
    assert work.raw_value == 0
    force = next(field for field in first if field.name == "AverageDriveForceN")
    assert force.raw_value == 4123
    assert first.get_value("total_cycles") == 1
    assert first.get_value("distance") == pytest.approx(0.0)

    second = records[1]
    names = {field.name for field in second}
    assert "StrokeWork" not in names
    assert second.get_value("distance") == pytest.approx(10.5)


def test_writer_rejects_values_that_overflow_fit_types(tmp_path: Path) -> None:
    with pytest.raises(CodecError):
        write_fit(
            _session(
                Record(timestamp=_ts(0), average_drive_force_n=7000),
            ),
            tmp_path / "overflow.fit",
        )


def test_writer_rejects_native_values_that_overflow(tmp_path: Path) -> None:
    with pytest.raises(CodecError):
        write_fit(
            _session(Record(timestamp=_ts(0), cadence=300)),
            tmp_path / "cadence.fit",
        )
