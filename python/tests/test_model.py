"""Session / Record / Lap dataclasses."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rowing_data import validate
from rowing_data.constants import RecordingStrategy, WorkoutState
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


def test_workout_state_enum_matches_fit_intensity() -> None:
    assert WorkoutState.ACTIVE == 0
    assert WorkoutState.REST == 1
    assert WorkoutState.WARMUP == 2
    assert WorkoutState.COOLDOWN == 3
    assert WorkoutState.RECOVERY == 4
    assert WorkoutState.INTERVAL == 5
    assert WorkoutState.OTHER == 6


def test_lap_intensity_wins_when_workout_state_disagrees() -> None:
    record = Record(
        timestamp=_ts(0),
        workout_state=WorkoutState.ACTIVE,
        lap_index=0,
    )
    lap = Lap(start_time=_ts(0), intensity=WorkoutState.REST)
    session = RowingSession(records=(record,), laps=(lap,))
    assert record.resolved_workout_state(lap) is WorkoutState.REST
    issues = validate(session)
    assert any(
        issue.code == "workout_state" and issue.level == "warning" for issue in issues
    )


def test_empty_session_without_start_time_raises() -> None:
    session = RowingSession(records=())
    with pytest.raises(ValueError, match="no records"):
        session.session_start()
