"""Consumer helpers required by spec §3.1.

Strokes are inferred from native ``total_cycles``, never from Record count.
Stroke rate prefers native ``cadence256``, then the caller's ``stroke_rate``,
then integer ``cadence``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .constants import CADENCE256_SCALE


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
    cadence256: float | None = None,
    stroke_rate: float | None = None,
    cadence: int | None = None,
) -> float | None:
    """Stroke rate in spm, following spec §3.1 item 5.

    ``cadence256`` is the value read from the file. ``stroke_rate`` is the
    physical rate a caller asked to write, used when the file value is absent.
    """
    if cadence256 is not None:
        return float(cadence256)
    if stroke_rate is not None:
        return float(stroke_rate)
    if cadence is None:
        return None
    return float(cadence)


def native_cadence_parts(stroke_rate_spm: float) -> tuple[int, int]:
    """Rounded integer cadence and ``cadence256`` raw value, half up.

    28.5 spm becomes cadence 29 and raw 7296.
    """
    rate = float(stroke_rate_spm)
    integer = math.floor(rate + 0.5)
    raw = math.floor(rate * CADENCE256_SCALE + 0.5)
    return int(integer), int(raw)
