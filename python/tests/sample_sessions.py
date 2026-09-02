"""Shared Level 1–2 sample sessions for tests and generated fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

from rowing_data.constants import RecordingStrategy
from rowing_data.model import Lap, Record, RowingSession


def _ts(second: int) -> datetime:
    return datetime(2026, 1, 1, 12, 0, second, tzinfo=UTC)


def stroke_boundary_session() -> RowingSession:
    """One Record per stroke, RecordingStrategy=StrokeBoundary."""
    return RowingSession(
        recording_strategy=RecordingStrategy.STROKE_BOUNDARY,
        laps=(
            Lap(start_time=_ts(0), total_elapsed_s=4.0, total_distance_m=20.0),
        ),
        records=(
            Record(
                timestamp=_ts(0),
                distance_m=0.0,
                total_cycles=1,
                stroke_rate=28.5,
                drive_length_mm=1420,
                stroke_drive_time_ms=450,
                stroke_recovery_time_ms=1650,
                cycle_length_m=8.5,
                average_drive_force_n=412.3,
                peak_drive_force_n=780.0,
                stroke_work_j=250,
                heart_rate=140,
                power=210,
                enhanced_speed_mps=4.321,
            ),
            Record(
                timestamp=_ts(2),
                distance_m=10.0,
                total_cycles=2,
                stroke_rate=29.0,
                drive_length_mm=1410,
                stroke_drive_time_ms=440,
                stroke_recovery_time_ms=1630,
                average_drive_force_n=400.0,
                peak_drive_force_n=760.0,
                stroke_work_j=240,
                heart_rate=142,
                power=215,
                enhanced_speed_mps=4.4,
            ),
            Record(
                timestamp=_ts(4),
                distance_m=20.0,
                total_cycles=3,
                stroke_rate=28.5,
                drive_length_mm=1415,
                stroke_drive_time_ms=455,
                stroke_recovery_time_ms=1640,
                average_drive_force_n=405.0,
                peak_drive_force_n=770.0,
                stroke_work_j=245,
                heart_rate=141,
                power=212,
                enhanced_speed_mps=4.35,
            ),
        ),
    )


def gps_update_session() -> RowingSession:
    """GPS-update records: total_cycles may repeat across samples."""
    return RowingSession(
        recording_strategy=RecordingStrategy.GPS_UPDATE,
        records=(
            Record(
                timestamp=_ts(0),
                distance_m=0.0,
                total_cycles=10,
                stroke_rate=22.0,
                position_lat=620_000_000,
                position_long=-50_000_000,
            ),
            Record(
                timestamp=_ts(1),
                distance_m=4.0,
                total_cycles=10,
                stroke_rate=22.0,
                position_lat=620_000_100,
                position_long=-50_000_050,
            ),
            Record(
                timestamp=_ts(2),
                distance_m=8.5,
                total_cycles=12,
                stroke_rate=22.5,
                position_lat=620_000_200,
                position_long=-50_000_100,
            ),
        ),
    )
