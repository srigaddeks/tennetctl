"""iam.saml_sso — Pydantic v2 schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class SamlProviderCreate(BaseModel):
    idp_entity_id: str
    sso_url: str
    x509_cert: str
    sp_entity_id: str
    enabled: bool = True

    @field_validator("x509_cert")
    @classmethod
    def strip_pem_headers(cls, v: str) -> str:
        lines = [
            line for line in v.strip().splitlines()
            if not line.startswith("-----")
        ]
        return "".join(lines)


class SamlProviderRow(BaseModel):
    id: str
    org_id: str
    org_slug: str
    idp_entity_id: str
    sso_url: str
    x509_cert: str
    sp_entity_id: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}
