"""Session / Record / Lap dataclasses."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from rowing_data import validate
from rowing_data.constants import LapIntensity, RecordingStrategy
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


def test_lap_intensity_enum_matches_fit_intensity() -> None:
    assert LapIntensity.ACTIVE == 0
    assert LapIntensity.REST == 1
    assert LapIntensity.WARMUP == 2
    assert LapIntensity.COOLDOWN == 3
    assert LapIntensity.RECOVERY == 4
    assert LapIntensity.INTERVAL == 5
    assert LapIntensity.OTHER == 6


def test_empty_session_without_start_time_raises() -> None:
    session = RowingSession(records=())
    with pytest.raises(ValueError, match="no records"):
        session.session_start()


def test_moving_time_sums_every_lap_except_rest() -> None:
    session = RowingSession(
        records=(),
        laps=(
            Lap(
                start_time=_ts(0),
                total_elapsed_s=100.0,
                intensity=LapIntensity.WARMUP,
            ),
            Lap(
                start_time=_ts(10),
                total_elapsed_s=60.0,
                total_timer_s=50.0,
                intensity=LapIntensity.INTERVAL,
            ),
            Lap(
                start_time=_ts(20),
                total_elapsed_s=90.0,
                intensity=LapIntensity.REST,
            ),
            Lap(
                start_time=_ts(30),
                total_elapsed_s=30.0,
                intensity=LapIntensity.RECOVERY,
            ),
        ),
    )
    assert session.moving_time_s() == 180.0


def test_rowing_in_a_rest_lap_is_flagged() -> None:
    laps = (Lap(start_time=_ts(0), intensity=LapIntensity.REST),)
    rowing = Record(timestamp=_ts(1), stroke_rate=20.0, lap_index=0)
    idle = Record(timestamp=_ts(2), heart_rate=90, lap_index=0)
    issues = validate(RowingSession(records=(rowing, idle), laps=laps))
    flagged = [i.record_index for i in issues if i.code == "rest_lap_rowing"]
    assert flagged == [0]
