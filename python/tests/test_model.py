"""Session / Record / Lap dataclasses."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rowing_data.constants import RecordingStrategy
from rowing_data.model import Lap, Record, RowingSession


def _ts(second: int) -> datetime:
    return datetime(2026, 1, 1, 12, 0, second, tzinfo=UTC)


def test_session_start_and_stroke_counts() -> None:
    records = (
        Record(timestamp=_ts(0), total_cycles=1, stroke_rate=20.0),
        Record(timestamp=_ts(2), total_cycles=1, stroke_rate=20.0),
        Record(timestamp=_ts(4), total_cycles=2, stroke_rate=21.0),
    )
    session = RowingSession(
        records=records,
        recording_strategy=RecordingStrategy.GPS_UPDATE,
        laps=(Lap(start_time=_ts(0), total_elapsed_s=4.0, total_distance_m=12.0),),
    )
    assert session.session_start() == _ts(0)
    assert session.stroke_counts() == [0, 0, 1]
    assert session.recording_strategy is RecordingStrategy.GPS_UPDATE


def test_empty_session_without_start_time_raises() -> None:
    session = RowingSession(records=())
    with pytest.raises(ValueError, match="no records"):
        session.session_start()
