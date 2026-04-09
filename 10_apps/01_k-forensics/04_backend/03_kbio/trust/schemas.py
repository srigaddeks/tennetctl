"""kbio trust schemas.

Pydantic v2 models for trusted-entity management.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TrustedEntityData(BaseModel):
    """A single trusted entity record."""

    id: str
    user_hash: str
    entity_type: str = Field(
        ...,
        description="One of: device, ip_address, location, network",
    )
    entity_value: str = Field(..., description="The concrete value being trusted")
    trust_reason: Optional[str] = None
    trusted_by: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None


class TrustProfileData(BaseModel):
    """Aggregated trust profile for a user, grouped by entity type."""

    user_hash: str
    trusted_devices: list[TrustedEntityData] = Field(default_factory=list)
    trusted_ips: list[TrustedEntityData] = Field(default_factory=list)
    trusted_locations: list[TrustedEntityData] = Field(default_factory=list)
    trusted_networks: list[TrustedEntityData] = Field(default_factory=list)


class CreateTrustedEntityRequest(BaseModel):
    """Request body for creating a new trusted entity."""

    user_hash: str = Field(..., description="Pseudonymous user identifier")
    entity_type: str = Field(
        ...,
        description="One of: device, ip_address, location, network",
    )
    entity_value: str = Field(..., description="The value to trust")
    trust_reason: str = Field(default="", description="Why this entity is being trusted")
    expires_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 expiry timestamp (null = never expires)",
    )


class PatchTrustedEntityRequest(BaseModel):
    """Request body for toggling a trusted entity's active status."""

    is_active: bool = Field(..., description="New active status")
