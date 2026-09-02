"""Canonical session model in physical units (not FIT integers)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from .constants import RecordingStrategy
from .strokes import resolve_stroke_rate, stroke_counts


@dataclass(frozen=True, slots=True)
class Record:
    """One FIT Record: a stroke or a GPS sample, depending on recording strategy."""

    timestamp: datetime
    distance_m: float | None = None
    cadence: int | None = None
    fractional_cadence: float | None = None
    heart_rate: int | None = None
    power: int | None = None
    enhanced_speed_mps: float | None = None
    position_lat: int | None = None  # semicircles
    position_long: int | None = None  # semicircles
    total_cycles: int | None = None
    cycle_length_m: float | None = None
    drive_length_mm: int | None = None
    stroke_drive_time_ms: int | None = None
    drag_factor: int | None = None
    stroke_recovery_time_ms: int | None = None
    average_drive_force_lbs: float | None = None
    peak_drive_force_lbs: float | None = None
    average_drive_force_n: float | None = None
    peak_drive_force_n: float | None = None
    average_boat_speed_mps: float | None = None
    workout_state: int | None = None
    stroke_work_j: int | None = None
    stroke_rate: float | None = None
    lap_index: int | None = None

    def resolved_stroke_rate(self) -> float | None:
        return resolve_stroke_rate(
            stroke_rate=self.stroke_rate,
            cadence=self.cadence,
            fractional_cadence=self.fractional_cadence,
        )


@dataclass(frozen=True, slots=True)
class Lap:
    start_time: datetime
    total_elapsed_s: float | None = None
    total_distance_m: float | None = None


@dataclass(frozen=True, slots=True)
class RowingSession:
    records: tuple[Record, ...]
    recording_strategy: RecordingStrategy = RecordingStrategy.UNKNOWN
    laps: tuple[Lap, ...] = field(default_factory=tuple)
    start_time: datetime | None = None
    # Warnings collected by read_fit (invalid RecordingStrategy, pre-v1.2 scales).
    read_issues: tuple = ()

    def session_start(self) -> datetime:
        if self.start_time is not None:
            return self.start_time
        if not self.records:
            raise ValueError("RowingSession has no records and no start_time")
        return self.records[0].timestamp

    def stroke_counts(self) -> list[int]:
        return stroke_counts([record.total_cycles for record in self.records])


# Record attributes that map to developer field IDs (Levels 1–2).
RECORD_DEVELOPER_ATTRS: Sequence[tuple[int, str]] = (
    (0, "drive_length_mm"),
    (1, "stroke_drive_time_ms"),
    (2, "drag_factor"),
    (3, "stroke_recovery_time_ms"),
    (4, "average_drive_force_lbs"),
    (5, "peak_drive_force_lbs"),
    (6, "average_drive_force_n"),
    (7, "peak_drive_force_n"),
    (8, "average_boat_speed_mps"),
    (9, "workout_state"),
    (19, "stroke_work_j"),
    (93, "stroke_rate"),
)

ATTR_BY_FIELD_ID = dict(RECORD_DEVELOPER_ATTRS)

# Record attributes that map to native FIT fields in spec §4.
NATIVE_RECORD_ATTRS: Sequence[tuple[str, str]] = (
    ("distance_m", "distance"),
    ("cadence", "cadence"),
    ("fractional_cadence", "fractional_cadence"),
    ("heart_rate", "heart_rate"),
    ("power", "power"),
    ("enhanced_speed_mps", "enhanced_speed"),
    ("position_lat", "position_lat"),
    ("position_long", "position_long"),
    ("total_cycles", "total_cycles"),
    ("cycle_length_m", "cycle_length16"),
)
