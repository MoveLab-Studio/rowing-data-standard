"""Conformance checks for a RowingSession (Draft v0.1, core fields).

Hard errors are type-limit violations and an unknown RecordingStrategy value.
Typical-range and timing consistency checks are warnings only (§8).
"""

from __future__ import annotations

from dataclasses import dataclass

from .codec import CodecError, encode
from .constants import RecordingStrategy
from .fields import field_by_id, field_by_name
from .model import NATIVE_RECORD_ATTRS, RECORD_DEVELOPER_ATTRS, Record, RowingSession

# Informative typical ranges from spec §8.1 — not encoding limits.
_TYPICAL = {
    "average_drive_force": (0.0, 2000.0),
    "peak_drive_force": (0.0, 2000.0),
    "drive_length_mm": (300.0, 1500.0),
    "stroke_rate": (10.0, 100.0),
}


@dataclass(frozen=True, slots=True)
class Issue:
    level: str  # "error" or "warning"
    code: str
    message: str
    record_index: int | None = None


def validate(session: RowingSession) -> list[Issue]:
    """Return errors and warnings. Does not modify ``session``."""
    issues: list[Issue] = list(session.read_issues)
    for index, record in enumerate(session.records):
        issues.extend(_record_issues(record, index, session))
    return issues


def _record_issues(record: Record, index: int, session: RowingSession) -> list[Issue]:
    issues: list[Issue] = []
    for field_id, attr in RECORD_DEVELOPER_ATTRS:
        physical = getattr(record, attr)
        if physical is None:
            continue
        try:
            encode(field_by_id(field_id), physical)
        except CodecError as exc:
            issues.append(Issue("error", "overflow", str(exc), index))
        lo_hi = _TYPICAL.get(attr)
        if lo_hi is not None:
            lo, hi = lo_hi
            value = float(physical)
            if value < lo or value > hi:
                issues.append(
                    Issue(
                        "warning",
                        "typical_range",
                        f"{attr}={physical!r} is outside typical [{lo}, {hi}]",
                        index,
                    )
                )

    for attr, native_name in NATIVE_RECORD_ATTRS:
        physical = getattr(record, attr)
        if physical is None:
            continue
        try:
            encode(field_by_name(native_name), physical)
        except CodecError as exc:
            issues.append(Issue("error", "overflow", str(exc), index))

    lap = _lap_for(record, session)
    if (
        lap is not None
        and lap.intensity is not None
        and record.workout_state is not None
        and record.workout_state != lap.intensity
    ):
        issues.append(
            Issue(
                "warning",
                "workout_state",
                "WorkoutState disagrees with lap intensity; the lap wins",
                index,
            )
        )

    if (
        record.stroke_state is not None
        and session.recording_strategy is not RecordingStrategy.TIME_SAMPLED
    ):
        issues.append(
            Issue(
                "warning",
                "stroke_state",
                "StrokeState is only meaningful when RecordingStrategy is TimeSampled",
                index,
            )
        )

    if record.heart_rate == 0:
        issues.append(
            Issue(
                "warning",
                "heart_rate",
                "heart_rate 0 is omitted; leave the field out when there is no sensor",
                index,
            )
        )

    rate = record.resolved_stroke_rate()
    drive = record.stroke_drive_time_ms
    recovery = record.stroke_recovery_time_ms
    if rate and rate > 0 and drive is not None and recovery is not None:
        period_ms = 60_000.0 / rate
        measured = float(drive + recovery)
        if abs(measured - period_ms) > max(150.0, 0.2 * period_ms):
            issues.append(
                Issue(
                    "warning",
                    "stroke_timing",
                    f"drive+recovery {measured:.0f} ms vs period "
                    f"{period_ms:.0f} ms",
                    index,
                )
            )
    return issues


def _lap_for(record: Record, session: RowingSession):
    if record.lap_index is None:
        return None
    if record.lap_index < 0 or record.lap_index >= len(session.laps):
        return None
    return session.laps[record.lap_index]
