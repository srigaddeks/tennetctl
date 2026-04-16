from __future__ import annotations

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger


class ClickHouseClient:
    """Async ClickHouse client for sandbox live log storage."""

    def __init__(self, url: str, database: str) -> None:
        self._url = url
        self._database = database
        self._logger = get_logger("backend.sandbox.clickhouse")
        self._session = None

    async def open(self) -> None:
        self._logger.info(
            "clickhouse_client_opened",
            extra={"action": "clickhouse.open", "outcome": "success", "database": self._database},
        )

    async def close(self) -> None:
        self._session = None
        self._logger.info(
            "clickhouse_client_closed",
            extra={"action": "clickhouse.close", "outcome": "success"},
        )

    async def insert_live_log(self, entry: dict) -> None:
        raise NotImplementedError("ClickHouse insert_live_log not yet implemented")

    async def insert_signal_result(self, entry: dict) -> None:
        raise NotImplementedError("ClickHouse insert_signal_result not yet implemented")

    async def insert_threat_evaluation(self, entry: dict) -> None:
        raise NotImplementedError("ClickHouse insert_threat_evaluation not yet implemented")

    async def query_live_logs(self, session_id: str, after_sequence: int, limit: int) -> list[dict]:
        raise NotImplementedError("ClickHouse query_live_logs not yet implemented")

    async def query_signal_history(self, signal_code: str, days: int, limit: int) -> list[dict]:
        raise NotImplementedError("ClickHouse query_signal_history not yet implemented")

    async def prune_old_data(self, log_retention_days: int, result_retention_days: int) -> dict:
        raise NotImplementedError("ClickHouse prune_old_data not yet implemented")


class NullClickHouseClient:
    """No-op fallback when SANDBOX_CLICKHOUSE_URL is not set."""

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def insert_live_log(self, entry: dict) -> None:
        pass

    async def insert_signal_result(self, entry: dict) -> None:
        pass

    async def insert_threat_evaluation(self, entry: dict) -> None:
        pass

    async def query_live_logs(self, *args, **kwargs) -> list[dict]:
        return []

    async def query_signal_history(self, *args, **kwargs) -> list[dict]:
        return []

    async def prune_old_data(self, *args, **kwargs) -> dict:
        return {"pruned": 0}
