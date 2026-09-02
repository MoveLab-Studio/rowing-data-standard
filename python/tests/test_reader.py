"""Reader binds only the standard application UUID; read warnings."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fit_tool.base_type import BaseType
from fit_tool.developer_field import DeveloperField
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.developer_data_id_message import DeveloperDataIdMessage
from fit_tool.profile.messages.field_description_message import FieldDescriptionMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.profile_type import FileType, Manufacturer

from rowing_data import APPLICATION_ID, read_fit, validate
from rowing_data.constants import RecordingStrategy
from rowing_data.fields import field_by_id


def _ts_ms() -> int:
    return int(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC).timestamp() * 1000)


def test_foreign_developer_drive_length_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "foreign.fit"
    other_app = uuid4().bytes
    builder = FitFileBuilder(auto_define=True, min_string_size=64)

    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.DEVELOPMENT
    file_id.time_created = _ts_ms()
    builder.add(file_id)

    dev_id = DeveloperDataIdMessage()
    dev_id.application_id = other_app
    assert other_app != APPLICATION_ID
    dev_id.developer_data_index = 0
    builder.add(dev_id)

    desc = FieldDescriptionMessage()
    desc.developer_data_index = 0
    desc.field_definition_number = 0
    desc.fit_base_type_id = BaseType.UINT16.value
    desc.field_name = "DriveLength"
    desc.scale = 1
    desc.offset = 0
    desc.units = "mm"
    builder.add(desc)

    session = SessionMessage()
    session.start_time = _ts_ms()
    session.timestamp = _ts_ms()
    builder.add(session)

    drive = DeveloperField(
        developer_data_index=0,
        field_id=0,
        size=2,
        name="DriveLength",
        base_type=BaseType.UINT16,
        scale=1,
        offset=0,
        units="mm",
    )
    drive.set_value(0, 1420)
    rec = RecordMessage(developer_fields=[drive])
    rec.timestamp = _ts_ms()
    rec.distance = 0.0
    builder.add(rec)
    builder.build().to_file(str(path))

    loaded = read_fit(path)
    assert loaded.records[0].drive_length_mm is None


def test_mismatched_file_scale_warns_and_uses_v01_units(tmp_path: Path) -> None:
    path = tmp_path / "old_scale.fit"
    field = field_by_id(0)
    builder = FitFileBuilder(auto_define=True, min_string_size=64)

    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.DEVELOPMENT
    file_id.time_created = _ts_ms()
    builder.add(file_id)

    dev_id = DeveloperDataIdMessage()
    dev_id.application_id = APPLICATION_ID
    dev_id.developer_data_index = 0
    builder.add(dev_id)

    desc = FieldDescriptionMessage()
    desc.developer_data_index = 0
    desc.field_definition_number = field.field_id
    desc.fit_base_type_id = BaseType.UINT16.value
    desc.field_name = field.name
    desc.scale = 100  # pre-v1.2 metres encoding
    desc.offset = 0
    desc.units = "m"
    builder.add(desc)

    session = SessionMessage()
    session.start_time = _ts_ms()
    session.timestamp = _ts_ms()
    builder.add(session)

    drive = DeveloperField(
        developer_data_index=0,
        field_id=0,
        size=2,
        name="DriveLength",
        base_type=BaseType.UINT16,
        scale=100,
        offset=0,
        units="m",
    )
    drive.set_value(0, 1.42)  # encoded 142 under scale 100
    rec = RecordMessage(developer_fields=[drive])
    rec.timestamp = _ts_ms()
    builder.add(rec)
    builder.build().to_file(str(path))

    loaded = read_fit(path)
    assert any(issue.code == "field_scale" for issue in loaded.read_issues)
    # Draft v0.1 treats raw 142 as millimetres, not 1.42 m.
    assert loaded.records[0].drive_length_mm == 142
    assert any(issue.code == "field_scale" for issue in validate(loaded))


def test_invalid_recording_strategy_is_unknown_with_warning(tmp_path: Path) -> None:
    path = tmp_path / "bad_strategy.fit"
    builder = FitFileBuilder(auto_define=True, min_string_size=64)

    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.DEVELOPMENT
    file_id.time_created = _ts_ms()
    builder.add(file_id)

    dev_id = DeveloperDataIdMessage()
    dev_id.application_id = APPLICATION_ID
    dev_id.developer_data_index = 0
    builder.add(dev_id)

    desc = FieldDescriptionMessage()
    desc.developer_data_index = 0
    desc.field_definition_number = 10
    desc.fit_base_type_id = BaseType.UINT8.value
    desc.field_name = "RecordingStrategy"
    desc.scale = 1
    desc.offset = 0
    desc.units = ""
    builder.add(desc)

    strategy = DeveloperField(
        developer_data_index=0,
        field_id=10,
        size=1,
        name="RecordingStrategy",
        base_type=BaseType.UINT8,
        scale=1,
        offset=0,
        units="",
    )
    strategy.set_value(0, 3)
    session = SessionMessage(developer_fields=[strategy])
    session.start_time = _ts_ms()
    session.timestamp = _ts_ms()
    builder.add(session)

    rec = RecordMessage()
    rec.timestamp = _ts_ms()
    builder.add(rec)
    builder.build().to_file(str(path))

    loaded = read_fit(path)
    assert loaded.recording_strategy is RecordingStrategy.UNKNOWN
    assert any(issue.code == "recording_strategy" for issue in loaded.read_issues)
