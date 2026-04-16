"""
Driver base class for direct API collectors.

Drivers are the primary asset collection mechanism. Each driver is a Python
class that directly calls a provider's API (REST, SDK, etc.) to discover assets
and ingest logs. Drivers do NOT depend on Steampipe — they are the "custom_driver"
substrate that runs without any external tool.

The driver pattern separates concerns clearly:
- Drivers handle: API calls, pagination, rate limiting, error handling
- The collection engine handles: DB writes, snapshots, audit events, health tracking
- The substrate registry decides: which backend (driver vs steampipe) to use

Drivers reuse the same ConnectionConfig and CollectedAsset types from the
substrate layer to maintain a consistent interface regardless of collection method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

_steampipe_base = __import__("importlib").import_module("backend.10_sandbox.19_steampipe.base")
CollectedAsset = _steampipe_base.CollectedAsset
CollectionResult = _steampipe_base.CollectionResult
ConnectionConfig = _steampipe_base.ConnectionConfig
ConnectionTestResult = _steampipe_base.ConnectionTestResult
QueryResult = _steampipe_base.QueryResult
QuerySubstrate = _steampipe_base.QuerySubstrate
SubstrateType = _steampipe_base.SubstrateType

__all__ = [
    "AssetDriver",
    "CollectedAsset",
    "CollectionResult",
    "ConnectionConfig",
    "ConnectionTestResult",
    "QueryResult",
]


class AssetDriver(QuerySubstrate, ABC):
    """
    Base class for direct API asset drivers.

    Drivers are concrete QuerySubstrate implementations that collect assets
    by calling provider APIs directly (no Steampipe involved). They are:
    - Fast (no subprocess overhead)
    - Reliable (no Steampipe plugin version mismatches)
    - Preferred for scheduled collection runs
    - Optional for ad-hoc SQL queries (most drivers don't support SQL)

    Steampipe can be used alongside drivers for ad-hoc queries, while drivers
    handle regular scheduled collection.
    """

    substrate_type = SubstrateType.CUSTOM_DRIVER

    @abstractmethod
    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        ...

    @abstractmethod
    async def collect_assets(
        self,
        config: ConnectionConfig,
        asset_types: list[str] | None = None,
        cursor: str | None = None,
    ) -> CollectionResult:
        ...

    async def execute_query(self, config: ConnectionConfig, sql: str) -> QueryResult:
        """
        Drivers do not support SQL queries by default.
        Override this method in drivers that support structured queries.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support SQL query execution. "
            "Use the Steampipe substrate for ad-hoc queries."
        )

    def supports_query(self) -> bool:
        return False
