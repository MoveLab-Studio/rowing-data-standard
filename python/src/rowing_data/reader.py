"""Read a Rowing Data Standard FIT file into a RowingSession."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from fitparse import FitFile

from .codec import decode
from .constants import APPLICATION_ID, RecordingStrategy
from .fields import FieldDef, field_by_id, field_by_name
from .model import ATTR_BY_FIELD_ID, Lap, Record, RowingSession

_NATIVE_NAMES = {
    "timestamp",
    "distance",
    "cadence",
    "fractional_cadence",
    "heart_rate",
    "power",
    "enhanced_speed",
    "position_lat",
    "position_long",
    "total_cycles",
    "cycle_length16",
    "cycle_length",
}


def read_fit(path: str | Path) -> RowingSession:
    """Parse ``path`` and return a session in physical units."""
    fit = FitFile(str(path), check_crc=False)
    messages = list(fit.messages)
    our_indexes = _developer_indexes_for_app(messages)
    scales = _developer_scales(messages, our_indexes)

    strategy = RecordingStrategy.UNKNOWN
    start_time: datetime | None = None
    for message in messages:
        if message.name != "session":
            continue
        start_time = _as_datetime(message.get_value("start_time")) or _as_datetime(
            message.get_value("timestamp")
        )
        raw_strategy = _developer_raw(message, "RecordingStrategy")
        if raw_strategy is not None:
            try:
                strategy = RecordingStrategy(int(raw_strategy))
            except ValueError:
                strategy = RecordingStrategy.UNKNOWN
        break

    laps = _laps(messages)
    records = tuple(
        _record(message, scales, laps)
        for message in messages
        if message.name == "record"
    )
    return RowingSession(
        records=records,
        recording_strategy=strategy,
        laps=tuple(laps),
        start_time=start_time,
    )


def _as_bytes(value: object) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes | bytearray):
        return bytes(value)
    if isinstance(value, list | tuple):
        return bytes(int(part) & 0xFF for part in value)
    return bytes(value)


def _developer_indexes_for_app(messages: list) -> set[int]:
    indexes: set[int] = set()
    for message in messages:
        if message.name != "developer_data_id":
            continue
        app_id = _as_bytes(message.get_value("application_id"))
        if app_id != APPLICATION_ID:
            continue
        index = message.get_value("developer_data_index")
        indexes.add(0 if index is None else int(index))
    return indexes


def _developer_scales(messages: list, our_indexes: set[int]) -> dict[str, FieldDef]:
    """Map developer field name -> FieldDef using the file's scale when present."""
    by_name: dict[str, FieldDef] = {}
    for message in messages:
        if message.name != "field_description":
            continue
        index = message.get_value("developer_data_index")
        if (0 if index is None else int(index)) not in our_indexes:
            continue
        field_id = message.get_value("field_definition_number")
        name = message.get_value("field_name")
        if field_id is None:
            continue
        try:
            registry = field_by_id(int(field_id))
        except KeyError:
            continue
        file_scale = message.get_value("scale")
        if file_scale in (None, 0):
            field = registry
        else:
            field = replace(registry, scale=float(file_scale))
        by_name[registry.name] = field
        if name:
            by_name[str(name)] = field
    return by_name


def _developer_raw(message, name: str) -> int | None:
    field = message.get(name)
    if field is None or field.raw_value is None:
        return None
    raw = field.raw_value
    if isinstance(raw, list | tuple):
        return None
    return int(raw)


def _as_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return None


def _laps(messages: list) -> list[Lap]:
    laps: list[Lap] = []
    for message in messages:
        if message.name != "lap":
            continue
        start = _as_datetime(message.get_value("start_time")) or _as_datetime(
            message.get_value("timestamp")
        )
        if start is None:
            continue
        elapsed = message.get_value("total_elapsed_time")
        distance = message.get_value("total_distance")
        laps.append(
            Lap(
                start_time=start,
                total_elapsed_s=None if elapsed is None else float(elapsed),
                total_distance_m=None if distance is None else float(distance),
            )
        )
    laps.sort(key=lambda lap: lap.start_time)
    return laps


def _lap_index(timestamp: datetime, laps: list[Lap]) -> int | None:
    if not laps:
        return None
    index = 0
    for i, lap in enumerate(laps):
        if lap.start_time <= timestamp:
            index = i
        else:
            break
    return index


def _record(message, scales: dict[str, FieldDef], laps: list[Lap]) -> Record:
    timestamp = _as_datetime(message.get_value("timestamp"))
    if timestamp is None:
        raise ValueError("record message is missing timestamp")

    kwargs: dict[str, object] = {
        "timestamp": timestamp,
        "distance_m": _native_float(message, "distance"),
        "cadence": _native_int(message, "cadence"),
        "fractional_cadence": _native_float(message, "fractional_cadence"),
        "heart_rate": _native_int(message, "heart_rate"),
        "power": _native_int(message, "power"),
        "enhanced_speed_mps": _native_float(message, "enhanced_speed"),
        "position_lat": _native_raw(message, "position_lat"),
        "position_long": _native_raw(message, "position_long"),
        "total_cycles": _native_int(message, "total_cycles"),
        "cycle_length_m": _cycle_length_m(message),
        "lap_index": _lap_index(timestamp, laps),
    }

    for field in message:
        if field.name in _NATIVE_NAMES or field.name in {
            "unknown",
            None,
        }:
            continue
        spec = scales.get(field.name)
        if spec is None:
            try:
                spec = field_by_name(field.name)
            except KeyError:
                continue
            if spec.native or spec.field_id is None:
                continue
        attr = ATTR_BY_FIELD_ID.get(spec.field_id)
        if attr is None:
            continue
        raw = field.raw_value
        if raw is None or isinstance(raw, list | tuple):
            continue
        kwargs[attr] = decode(spec, int(raw))

    return Record(**kwargs)  # type: ignore[arg-type]


def _native_int(message, name: str) -> int | None:
    value = message.get_value(name)
    if value is None:
        return None
    return int(value)


def _native_float(message, name: str) -> float | None:
    value = message.get_value(name)
    if value is None:
        return None
    return float(value)


def _native_raw(message, name: str) -> int | None:
    field = message.get(name)
    if field is None or field.raw_value is None:
        return None
    return int(field.raw_value)


def _cycle_length_m(message) -> float | None:
    field = message.get("cycle_length16")
    if field is not None and field.raw_value is not None:
        return decode(field_by_name("cycle_length16"), int(field.raw_value))
    value = message.get_value("cycle_length")
    if value is None:
        return None
    return float(value)
