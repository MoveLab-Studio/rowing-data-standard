"""Consumer helpers required by spec §3.1.

Strokes are inferred from native ``total_cycles``, never from Record count.
Stroke rate prefers developer field 93, then cadence plus fractional cadence,
then integer cadence alone.
"""

from __future__ import annotations

from collections.abc import Sequence


def strokes_between(previous_total: int | None, current_total: int | None) -> int:
    """How many strokes occurred after the previous record.

    A change of 0 means the same stroke (typical GPS-update). A change greater
    than 1 means intermediate strokes were not recorded.
    """
    if previous_total is None or current_total is None:
        return 0
    delta = current_total - previous_total
    return delta if delta > 0 else 0


def stroke_counts(total_cycles: Sequence[int | None]) -> list[int]:
    """Per-record stroke counts since the previous record (first record is 0)."""
    counts: list[int] = []
    previous: int | None = None
    for current in total_cycles:
        counts.append(strokes_between(previous, current))
        if current is not None:
            previous = current
    return counts


def resolve_stroke_rate(
    *,
    stroke_rate: float | None = None,
    cadence: int | None = None,
    fractional_cadence: float | None = None,
) -> float | None:
    """Stroke rate in spm, following spec §3.1 item 5."""
    if stroke_rate is not None:
        return float(stroke_rate)
    if cadence is None:
        return None
    fraction = 0.0 if fractional_cadence is None else float(fractional_cadence)
    return float(cadence) + fraction


def native_cadence_parts(stroke_rate_spm: float) -> tuple[int, float]:
    """Split a rate into native integer cadence and fractional part in [0, 1)."""
    integer = int(stroke_rate_spm)
    return integer, float(stroke_rate_spm) - integer
