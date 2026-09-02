"""Stroke detection and stroke-rate resolution (spec §3.1)."""

from __future__ import annotations

from datetime import UTC, datetime

from rowing_data.model import Record
from rowing_data.strokes import resolve_stroke_rate, stroke_counts, strokes_between


def test_strokes_between_unchanged_plus_one_and_skip() -> None:
    assert strokes_between(None, 10) == 0
    assert strokes_between(10, None) == 0
    assert strokes_between(10, 10) == 0
    assert strokes_between(10, 11) == 1
    assert strokes_between(10, 13) == 3
    assert strokes_between(13, 10) == 0


def test_stroke_counts_across_a_sequence() -> None:
    assert stroke_counts([1, 1, 2, 5, None, 6]) == [0, 0, 1, 3, 0, 1]


def test_resolve_stroke_rate_precedence() -> None:
    assert (
        resolve_stroke_rate(stroke_rate=28.5, cadence=18, fractional_cadence=0.25)
        == 28.5
    )
    assert resolve_stroke_rate(cadence=18, fractional_cadence=0.25) == 18.25
    assert resolve_stroke_rate(cadence=18) == 18.0
    assert resolve_stroke_rate() is None
    assert resolve_stroke_rate(fractional_cadence=0.5) is None


def test_record_resolved_stroke_rate() -> None:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    with_dev = Record(
        timestamp=ts, stroke_rate=22.1, cadence=22, fractional_cadence=0.0
    )
    assert with_dev.resolved_stroke_rate() == 22.1
    native_only = Record(timestamp=ts, cadence=19, fractional_cadence=0.4)
    assert native_only.resolved_stroke_rate() == 19.4
