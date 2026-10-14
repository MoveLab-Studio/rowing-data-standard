"""Encode physical values to FIT integers and decode them back.

FIT stores integers. A field's ``scale`` is the FIT-profile scale:
``physical = raw / scale`` and ``raw = round(physical * scale)``.

Absent values are ``None`` and MUST be omitted from the file — never encoded
as a placeholder such as -1 or 999. Each base type's FIT invalid value (spec
§7.2) means "no data": ``encode`` never produces it for a measurement, and
``decode`` returns ``None`` for it.
"""

from __future__ import annotations

from .fields import BASE_TYPE_INVALID, BASE_TYPE_RANGE, FieldDef


class CodecError(ValueError):
    """A physical value cannot be represented in the field's FIT base type."""


def encode(field: FieldDef, physical: float | int | None) -> int | None:
    """Convert a physical value to a FIT raw integer, or ``None`` if absent."""
    if physical is None:
        return None
    raw = round(float(physical) * field.scale)
    lo, hi = BASE_TYPE_RANGE[field.base_type]
    if raw < lo or raw > hi:
        raise CodecError(
            f"{field.name}: encoded value {raw} does not fit {field.base_type} "
            f"range [{lo}, {hi}] (physical={physical!r}, scale={field.scale})"
        )
    invalid = BASE_TYPE_INVALID[field.base_type]
    if raw == invalid:
        return invalid - 1
    return raw


def decode(field: FieldDef, raw: int | None) -> float | int | None:
    """Convert a FIT raw integer to a physical value, or ``None`` if absent."""
    if raw is None or raw == BASE_TYPE_INVALID[field.base_type]:
        return None
    if field.scale == 1:
        return int(raw)
    return raw / field.scale
