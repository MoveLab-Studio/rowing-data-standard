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
    assert resolve_stroke_rate(cadence256=28.5, stroke_rate=22.0, cadence=18) == 28.5
    assert resolve_stroke_rate(stroke_rate=28.5, cadence=18) == 28.5
    assert resolve_stroke_rate(cadence=18) == 18.0
    assert resolve_stroke_rate() is None


def test_native_cadence_parts_rounds_half_up() -> None:
    from rowing_data.strokes import native_cadence_parts

    assert native_cadence_parts(28.5) == (29, 7296)
    assert native_cadence_parts(28.4) == (28, 7270)


def test_record_resolved_stroke_rate() -> None:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    from_caller = Record(timestamp=ts, stroke_rate=22.1, cadence=22)
    assert from_caller.resolved_stroke_rate() == 22.1
    from_file = Record(timestamp=ts, cadence256=19.4, cadence=19)
    assert from_file.resolved_stroke_rate() == 19.4
    native_only = Record(timestamp=ts, cadence=19)
    assert native_only.resolved_stroke_rate() == 19.0
