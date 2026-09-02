"""Read committed fixtures; optionally the rowingdata golden FIT file."""

from __future__ import annotations

from pathlib import Path

import pytest
from fitparse import FitFile

from rowing_data import APPLICATION_ID, read_fit, write_fit
from rowing_data.constants import RecordingStrategy
from sample_sessions import stroke_boundary_session

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
ROWINGDATA_GOLDEN = (
    Path(__file__).resolve().parents[2]
    / "rowingdata"
    / "testdata"
    / "rowingdata_standard_example.fit"
)


def test_committed_stroke_boundary_fixture() -> None:
    path = FIXTURE_DIR / "stroke-boundary.fit"
    session = read_fit(path)
    assert session.recording_strategy is RecordingStrategy.STROKE_BOUNDARY
    assert len(session.records) == 3
    assert session.records[0].drive_length_mm == 1420
    assert session.records[0].resolved_stroke_rate() == pytest.approx(28.5)
    assert session.stroke_counts() == [0, 1, 1]


def test_committed_gps_update_fixture() -> None:
    path = FIXTURE_DIR / "gps-update.fit"
    session = read_fit(path)
    assert session.recording_strategy is RecordingStrategy.GPS_UPDATE
    assert session.stroke_counts() == [0, 0, 2]
    assert session.records[0].position_lat is not None


def test_written_file_has_standard_application_id(tmp_path: Path) -> None:
    path = tmp_path / "id.fit"
    write_fit(stroke_boundary_session(), path)
    fit = FitFile(str(path), check_crc=True)
    app = next(fit.get_messages("developer_data_id")).get_value("application_id")
    if not isinstance(app, bytes):
        app = bytes(app)
    assert app == APPLICATION_ID


def test_rowingdata_golden_file_if_present() -> None:
    if not ROWINGDATA_GOLDEN.is_file():
        pytest.skip(f"rowingdata golden FIT not found at {ROWINGDATA_GOLDEN}")
    session = read_fit(ROWINGDATA_GOLDEN)
    assert session.recording_strategy in {
        RecordingStrategy.UNKNOWN,
        RecordingStrategy.STROKE_BOUNDARY,
        RecordingStrategy.GPS_UPDATE,
    }
    assert len(session.records) > 0
    # Level 3 curve fields are ignored; core metrics should still parse.
    assert any(record.total_cycles is not None for record in session.records) or any(
        record.stroke_rate is not None or record.cadence is not None
        for record in session.records
    )
