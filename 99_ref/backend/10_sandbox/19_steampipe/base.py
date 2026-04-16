"""
Query substrate abstraction layer.

A "query substrate" is any backend that can execute structured queries against
an external provider (GitHub, Azure, etc.) and return normalized results.

Steampipe is the default implementation, but this interface allows swapping to:
- Direct API collectors (custom Python drivers)
- Other SQL-over-cloud tools (CloudQuery, Powerpipe, etc.)
- Mock substrates for testing

Each substrate is registered by `provider_code` and selected at runtime by
the SubstrateRegistry. Connectors declare which substrate(s) they support
via `supports_steampipe` and `supports_custom_driver` on the provider definition.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class SubstrateType(StrEnum):
    STEAMPIPE = "steampipe"
    CUSTOM_DRIVER = "custom_driver"


@dataclass(frozen=True)
class ConnectionConfig:
    """Resolved connection configuration for a connector instance."""
    connector_instance_id: str
    provider_code: str
    provider_version_code: str | None
    # Non-credential config from connection_config JSONB
    config: dict[str, Any]
    # Decrypted credential values (never persisted, in-memory only)
    credentials: dict[str, str]


@dataclass
class CollectedAsset:
    """A single discovered asset with its properties."""
    external_id: str
    asset_type_code: str
    properties: dict[str, Any]
    parent_external_id: str | None = None
    parent_asset_type_code: str | None = None


@dataclass
class CollectionResult:
    """Result of a collection run."""
    assets: list[CollectedAsset] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    is_partial: bool = False
    next_cursor: str | None = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0 or self.is_partial


@dataclass
class ConnectionTestResult:
    """Result of testing a connector's connection."""
    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: int | None = None


@dataclass
class QueryResult:
    """Result of a substrate query."""
    rows: list[dict[str, Any]]
    row_count: int
    query_hash: str
    executed_at: datetime
    cached: bool = False
    substrate_type: SubstrateType = SubstrateType.CUSTOM_DRIVER

    @classmethod
    def compute_hash(cls, sql: str, connector_instance_id: str) -> str:
        payload = f"{connector_instance_id}:{sql}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class QuerySubstrate(ABC):
    """
    Abstract base class for all query substrate implementations.

    Implementations must handle their own credential resolution and connection
    lifecycle. They should never persist decrypted credentials to disk or logs.
    """

    substrate_type: SubstrateType

    @abstractmethod
    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        """Test whether the provided credentials can connect to the provider."""
        ...

    @abstractmethod
    async def collect_assets(
        self,
        config: ConnectionConfig,
        asset_types: list[str] | None = None,
        cursor: str | None = None,
    ) -> CollectionResult:
        """
        Discover and collect assets from the provider.

        Args:
            config: Resolved connection configuration with decrypted credentials
            asset_types: Optional list of asset type codes to collect. None = collect all.
            cursor: Resume cursor for pagination (from previous partial collection)

        Returns:
            CollectionResult with discovered assets and any errors
        """
        ...

    @abstractmethod
    async def execute_query(
        self,
        config: ConnectionConfig,
        sql: str,
    ) -> QueryResult:
        """
        Execute a SQL query against the provider via this substrate.

        Args:
            config: Resolved connection configuration with decrypted credentials
            sql: SQL query to execute (substrate-specific dialect)

        Returns:
            QueryResult with rows and metadata
        """
        ...

    def supports_provider(self, provider_code: str) -> bool:
        """Return True if this substrate supports the given provider."""
        return True  # override to restrict

    def supports_query(self) -> bool:
        """Return True if this substrate supports arbitrary SQL queries."""
        return False  # Steampipe supports, custom drivers may not
