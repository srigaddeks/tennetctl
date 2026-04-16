from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module


_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
start_operation_span = _telemetry_module.start_operation_span
_LOGGER = get_logger("backend.time")


def utc_now_sql() -> datetime:
    with start_operation_span("time.utc_now_sql"):
        value = datetime.now(tz=UTC).replace(tzinfo=None)
        _LOGGER.debug(
            "time_utc_now_sql_generated",
            extra={"action": "time.utc_now_sql", "outcome": "success"},
        )
        return value


def to_sql_timestamp(value: datetime) -> datetime:
    with start_operation_span("time.to_sql_timestamp"):
        result = value if value.tzinfo is None else value.astimezone(UTC).replace(tzinfo=None)
        _LOGGER.debug(
            "time_to_sql_timestamp_completed",
            extra={"action": "time.to_sql_timestamp", "outcome": "success"},
        )
        return result


def from_sql_timestamp(value: datetime | None) -> datetime | None:
    with start_operation_span("time.from_sql_timestamp"):
        if value is None:
            result = None
        elif value.tzinfo is not None:
            result = value.astimezone(UTC)
        else:
            result = value.replace(tzinfo=UTC)
        _LOGGER.debug(
            "time_from_sql_timestamp_completed",
            extra={"action": "time.from_sql_timestamp", "outcome": "success"},
        )
        return result
