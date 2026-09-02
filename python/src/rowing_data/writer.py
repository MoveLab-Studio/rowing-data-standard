"""Write a RowingSession to a Garmin FIT file (Draft v0.1, Levels 1–2)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fit_tool.base_type import BaseType as FitBaseType
from fit_tool.developer_field import DeveloperField
from fit_tool.field import Field
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.developer_data_id_message import DeveloperDataIdMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.field_description_message import FieldDescriptionMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.profile_type import (
    Activity,
    Event,
    EventType,
    FileType,
    Manufacturer,
    Sport,
    SubSport,
)

from .codec import encode
from .constants import APPLICATION_ID, CYCLE_LENGTH16_SCALE
from .fields import BaseType, FieldDef, field_by_id, field_by_name
from .model import RECORD_DEVELOPER_ATTRS, Record, RowingSession
from .strokes import native_cadence_parts

_DEV_INDEX = 0
_BASE_TYPE_TO_FIT = {
    BaseType.UINT8: FitBaseType.UINT8,
    BaseType.UINT16: FitBaseType.UINT16,
    BaseType.UINT32: FitBaseType.UINT32,
    BaseType.SINT16: FitBaseType.SINT16,
    BaseType.SINT32: FitBaseType.SINT32,
}
_BASE_TYPE_SIZE = {
    BaseType.UINT8: 1,
    BaseType.UINT16: 2,
    BaseType.UINT32: 4,
    BaseType.SINT16: 2,
    BaseType.SINT32: 4,
}

# Garmin FIT profile: cycle_length16 is field 87 (UINT16, metres, scale 100).
_CYCLE_LENGTH16_FIELD_ID = 87

# FIT stores lat/long as semicircles; fit-tool's setter takes degrees.
_DEGREES_PER_SEMICIRCLE = 180.0 / (1 << 31)


def write_fit(session: RowingSession, path: str | Path) -> None:
    """Serialize ``session`` to ``path`` as an Activity FIT file."""
    if not session.records:
        raise ValueError("cannot write a FIT file with no records")

    start = session.session_start()
    start_ms = _unix_ms(start)
    last_ms = _unix_ms(session.records[-1].timestamp)
    elapsed_s = max((last_ms - start_ms) / 1000.0, 0.0)
    total_distance = _last_distance(session)

    record_fields = _record_developer_fields_used(session)
    builder = FitFileBuilder(auto_define=True, min_string_size=64)

    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.DEVELOPMENT
    file_id.product = 0
    file_id.time_created = start_ms
    file_id.serial_number = 0
    builder.add(file_id)

    activity = ActivityMessage()
    activity.timestamp = start_ms
    activity.total_timer_time = elapsed_s
    activity.num_sessions = 1
    activity.type = Activity.MANUAL
    activity.event = Event.TIMER
    activity.event_type = EventType.START
    builder.add(activity)

    event_start = EventMessage()
    event_start.event = Event.TIMER
    event_start.event_type = EventType.START
    event_start.timestamp = start_ms
    builder.add(event_start)

    _add_developer_definitions(builder, record_fields)

    session_msg = SessionMessage(developer_fields=[_recording_strategy_field(session)])
    session_msg.message_index = 0
    session_msg.timestamp = start_ms
    session_msg.start_time = start_ms
    session_msg.total_elapsed_time = elapsed_s
    session_msg.total_timer_time = elapsed_s
    session_msg.total_distance = total_distance
    session_msg.sport = Sport.ROWING
    session_msg.sub_sport = SubSport.GENERIC
    builder.add(session_msg)

    laps = session.laps or ()
    if laps:
        for index, lap in enumerate(laps):
            lap_msg = LapMessage()
            lap_msg.message_index = index
            lap_msg.timestamp = _unix_ms(lap.start_time)
            lap_msg.start_time = _unix_ms(lap.start_time)
            if lap.total_elapsed_s is not None:
                lap_msg.total_elapsed_time = lap.total_elapsed_s
                lap_msg.total_timer_time = lap.total_elapsed_s
            if lap.total_distance_m is not None:
                lap_msg.total_distance = lap.total_distance_m
            lap_msg.sport = Sport.ROWING
            builder.add(lap_msg)
    else:
        lap_msg = LapMessage()
        lap_msg.message_index = 0
        lap_msg.timestamp = start_ms
        lap_msg.start_time = start_ms
        lap_msg.total_elapsed_time = elapsed_s
        lap_msg.total_timer_time = elapsed_s
        lap_msg.total_distance = total_distance
        lap_msg.sport = Sport.ROWING
        builder.add(lap_msg)

    for record in session.records:
        builder.add(_record_message(record, record_fields))

    event_stop = EventMessage()
    event_stop.event = Event.TIMER
    event_stop.event_type = EventType.STOP_ALL
    event_stop.timestamp = last_ms
    builder.add(event_stop)

    builder.build().to_file(str(path))


def _unix_ms(moment: datetime) -> int:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return int(moment.timestamp() * 1000)


def _last_distance(session: RowingSession) -> float:
    for record in reversed(session.records):
        if record.distance_m is not None:
            return float(record.distance_m)
    return 0.0


def _record_developer_fields_used(session: RowingSession) -> tuple[FieldDef, ...]:
    used: list[FieldDef] = []
    for field_id, attr in RECORD_DEVELOPER_ATTRS:
        if any(getattr(record, attr) is not None for record in session.records):
            used.append(field_by_id(field_id))
    return tuple(used)


def _add_developer_definitions(
    builder: FitFileBuilder, record_fields: tuple[FieldDef, ...]
) -> None:
    dev_id = DeveloperDataIdMessage()
    dev_id.application_id = APPLICATION_ID
    dev_id.developer_data_index = _DEV_INDEX
    builder.add(dev_id)
    builder.add(_field_description(field_by_id(10)))
    for field in record_fields:
        builder.add(_field_description(field))


def _field_description(field: FieldDef) -> FieldDescriptionMessage:
    message = FieldDescriptionMessage()
    message.developer_data_index = _DEV_INDEX
    message.field_definition_number = field.field_id
    message.fit_base_type_id = _BASE_TYPE_TO_FIT[field.base_type].value
    message.field_name = field.name
    message.scale = int(field.scale)
    message.offset = 0
    message.units = field.units
    return message


def _recording_strategy_field(session: RowingSession) -> DeveloperField:
    field = field_by_id(10)
    return _developer_field(field, int(session.recording_strategy))


def _developer_field(field: FieldDef, physical: float | int) -> DeveloperField:
    # Validate against type limits; fit-tool then applies the same scale.
    encode(field, physical)
    fit_type = _BASE_TYPE_TO_FIT[field.base_type]
    dev = DeveloperField(
        developer_data_index=_DEV_INDEX,
        field_id=field.field_id or 0,
        size=_BASE_TYPE_SIZE[field.base_type],
        name=field.name,
        base_type=fit_type,
        scale=field.scale,
        offset=0,
        units=field.units,
    )
    dev.set_value(0, physical)
    return dev


def _record_message(
    record: Record, record_fields: tuple[FieldDef, ...]
) -> RecordMessage:
    dev_fields = []
    for field in record_fields:
        attr = _attr_for_field_id(field.field_id)
        physical = getattr(record, attr)
        if physical is None:
            continue
        dev_fields.append(_developer_field(field, physical))

    rec = RecordMessage(developer_fields=dev_fields) if dev_fields else RecordMessage()
    rec.timestamp = _unix_ms(record.timestamp)
    _set_native_fields(rec, record)
    cadence, fraction = _native_cadence(record)
    if cadence is not None:
        encode(field_by_name("cadence"), cadence)
        rec.cadence = cadence
    if fraction is not None:
        encode(field_by_name("fractional_cadence"), fraction)
        rec.fractional_cadence = fraction
    return rec


def _set_native_fields(rec: RecordMessage, record: Record) -> None:
    if record.distance_m is not None:
        encode(field_by_name("distance"), record.distance_m)
        rec.distance = float(record.distance_m)
    if record.heart_rate is not None:
        encode(field_by_name("heart_rate"), record.heart_rate)
        rec.heart_rate = record.heart_rate
    if record.power is not None:
        encode(field_by_name("power"), record.power)
        rec.power = record.power
    if record.enhanced_speed_mps is not None:
        encode(field_by_name("enhanced_speed"), record.enhanced_speed_mps)
        rec.enhanced_speed = float(record.enhanced_speed_mps)
    if record.total_cycles is not None:
        encode(field_by_name("total_cycles"), record.total_cycles)
        rec.total_cycles = record.total_cycles
    if record.cycle_length_m is not None:
        _set_cycle_length16(rec, record.cycle_length_m)
    if record.position_lat is not None:
        encode(field_by_name("position_lat"), record.position_lat)
        rec.position_lat = record.position_lat * _DEGREES_PER_SEMICIRCLE
    if record.position_long is not None:
        encode(field_by_name("position_long"), record.position_long)
        rec.position_long = record.position_long * _DEGREES_PER_SEMICIRCLE


def _set_cycle_length16(rec: RecordMessage, metres: float) -> None:
    encode(field_by_name("cycle_length16"), metres)
    extra = Field(
        name="cycle_length16",
        field_id=_CYCLE_LENGTH16_FIELD_ID,
        base_type=FitBaseType.UINT16,
        offset=0,
        scale=float(CYCLE_LENGTH16_SCALE),
        size=2,
        units="m",
        growable=True,
    )
    extra.set_value(0, metres)
    rec.fields.append(extra)


def _attr_for_field_id(field_id: int | None) -> str:
    for fid, attr in RECORD_DEVELOPER_ATTRS:
        if fid == field_id:
            return attr
    raise KeyError(f"no Record attribute for developer field {field_id}")


def _native_cadence(record: Record) -> tuple[int | None, float | None]:
    """Integer cadence plus fractional part when a rate is known."""
    if record.stroke_rate is not None:
        integer, fraction = native_cadence_parts(record.stroke_rate)
        return integer, fraction
    if record.cadence is None and record.fractional_cadence is None:
        return None, None
    return record.cadence, record.fractional_cadence
