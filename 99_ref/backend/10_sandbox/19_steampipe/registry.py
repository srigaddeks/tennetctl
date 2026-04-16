"""
Substrate registry — maps provider codes to their preferred substrate implementations.

Usage:
    registry = SubstrateRegistry()
    registry.register(SubstrateType.STEAMPIPE, SteampipeSubstrate(settings))
    registry.register(SubstrateType.CUSTOM_DRIVER, CustomDriverSubstrate(settings))

    substrate = registry.get_for_provider("github", prefer=SubstrateType.STEAMPIPE)
    result = await substrate.test_connection(config)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from importlib import import_module as _im
_sp_base = _im("backend.10_sandbox.19_steampipe.base")
QuerySubstrate = _sp_base.QuerySubstrate
SubstrateType = _sp_base.SubstrateType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SubstrateRegistry:
    """
    Registry of available query substrate backends.

    Each substrate type can have one implementation registered. Callers request
    a substrate by provider code and optionally preferred type. Falls back to
    any available substrate if the preferred type is not registered.
    """

    def __init__(self) -> None:
        self._substrates: dict[SubstrateType, QuerySubstrate] = {}

    def register(self, substrate_type: SubstrateType, substrate: QuerySubstrate) -> None:
        """Register a substrate implementation."""
        self._substrates[substrate_type] = substrate
        logger.info("substrate_registered", extra={"substrate_type": substrate_type})

    def get(self, substrate_type: SubstrateType) -> QuerySubstrate | None:
        """Get a substrate by type."""
        return self._substrates.get(substrate_type)

    def get_for_provider(
        self,
        provider_code: str,
        prefer: SubstrateType | None = None,
    ) -> QuerySubstrate | None:
        """
        Get the best available substrate for a provider.

        Priority:
        1. Preferred type (if specified and registered)
        2. Any registered substrate that supports the provider
        3. None (caller must handle missing substrate)
        """
        if prefer is not None:
            substrate = self._substrates.get(prefer)
            if substrate and substrate.supports_provider(provider_code):
                return substrate

        # Fallback: any registered substrate that supports this provider
        for substrate in self._substrates.values():
            if substrate.supports_provider(provider_code):
                return substrate

        return None

    def available_types(self) -> list[SubstrateType]:
        return list(self._substrates.keys())


# Application-level singleton (populated during app lifespan)
_registry: SubstrateRegistry | None = None


def get_registry() -> SubstrateRegistry:
    global _registry
    if _registry is None:
        _registry = SubstrateRegistry()
    return _registry


def reset_registry() -> None:
    """Reset for testing."""
    global _registry
    _registry = None
