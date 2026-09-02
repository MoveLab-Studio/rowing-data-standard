"""Read a Rowing Data Standard FIT file into a RowingSession."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fitparse import FitFile

from .codec import decode
from .constants import APPLICATION_ID, RecordingStrategy
from .fields import FieldDef, field_by_id, field_by_name
from .model import ATTR_BY_FIELD_ID, Lap, Record, RowingSession
from .validation import Issue

# Garmin FIT profile number for cycle_length16 (UINT16, scale 100). fitparse
# 1.2.0 does not name this field, so readers must also match unknown_87.
_CYCLE_LENGTH16_DEF_NUM = 87

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
    f"unknown_{_CYCLE_LENGTH16_DEF_NUM}",
}


def read_fit(path: str | Path) -> RowingSession:
    """Parse ``path`` and return a session in physical units (Draft v0.1)."""
    fit = FitFile(str(path), check_crc=False)
    messages = list(fit.messages)
    our_indexes = _developer_indexes_for_app(messages)
    our_fields, issues = _our_developer_fields(messages, our_indexes)

    strategy = RecordingStrategy.UNKNOWN
    start_time: datetime | None = None
    for message in messages:
        if message.name != "session":
            continue
        start_time = _as_datetime(message.get_value("start_time")) or _as_datetime(
            message.get_value("timestamp")
        )
        strategy, strategy_issue = _recording_strategy(message, our_fields)
        if strategy_issue is not None:
            issues.append(strategy_issue)
        break

    laps = _laps(messages)
    records = tuple(
        _record(message, our_fields, laps)
        for message in messages
        if message.name == "record"
    )
    return RowingSession(
        records=records,
        recording_strategy=strategy,
        laps=tuple(laps),
        start_time=start_time,
        read_issues=tuple(issues),
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


def _our_developer_fields(
    messages: list, our_indexes: set[int]
) -> tuple[dict[str, FieldDef], list[Issue]]:
    """Map names to registry FieldDefs for the standard application UUID only.

    Decode always uses Draft v0.1 scales/units. A file that advertises a
    different scale (for example pre-v1.2 DriveLength in metres) is not
    converted; a warning is recorded instead.
    """
    by_name: dict[str, FieldDef] = {}
    issues: list[Issue] = []
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
        if (
            file_scale not in (None, 0)
            and float(file_scale) != float(registry.scale)
        ):
            issues.append(
                Issue(
                    "warning",
                    "field_scale",
                    f"{registry.name} (ID {registry.field_id}) has file scale "
                    f"{file_scale}, Draft v0.1 scale is {registry.scale}; "
                    "decoded with v0.1 units, not converted",
                )
            )
        by_name[registry.name] = registry
        if name:
            by_name[str(name)] = registry
    return by_name, issues


def _recording_strategy(
    message, our_fields: dict[str, FieldDef]
) -> tuple[RecordingStrategy, Issue | None]:
    spec = our_fields.get("RecordingStrategy")
    if spec is None or spec.field_id != 10:
        return RecordingStrategy.UNKNOWN, None
    field = message.get("RecordingStrategy")
    if field is None or field.raw_value is None:
        return RecordingStrategy.UNKNOWN, None
    raw = field.raw_value
    if isinstance(raw, list | tuple):
        return RecordingStrategy.UNKNOWN, None
    value = int(raw)
    try:
        return RecordingStrategy(value), None
    except ValueError:
        return RecordingStrategy.UNKNOWN, Issue(
            "warning",
            "recording_strategy",
            f"RecordingStrategy {value} is not 0, 1, or 2; treating as Unknown",
        )


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


def _record(message, our_fields: dict[str, FieldDef], laps: list[Lap]) -> Record:
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
        if field.name in _NATIVE_NAMES or field.name in {"unknown", None}:
            continue
        spec = our_fields.get(field.name)
        if spec is None or spec.native or spec.field_id is None:
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
    spec = field_by_name("cycle_length16")
    for field in message:
        if field.name not in (
            "cycle_length16",
            f"unknown_{_CYCLE_LENGTH16_DEF_NUM}",
        ):
            continue
        raw = field.raw_value
        if raw is None or isinstance(raw, list | tuple):
            return None
        return decode(spec, int(raw))
    return None
