from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderConfigSchemaField:
    key: str
    label: str
    type: str
    required: bool
    credential: bool
    placeholder: str | None
    hint: str | None
    validation: str | None
    default: str | None
    order: int


@dataclass(frozen=True)
class ProviderDefinition:
    id: str
    code: str
    name: str
    driver_module: str
    default_auth_method: str
    supports_log_collection: bool
    supports_steampipe: bool
    supports_custom_driver: bool
    steampipe_plugin: str | None
    rate_limit_rpm: int
    config_schema: dict
    is_active: bool
    is_coming_soon: bool
    created_at: str
    updated_at: str

    def effective_schema(
        self, version_override: dict | None = None
    ) -> list[ProviderConfigSchemaField]:
        base_fields: dict[str, dict] = {}
        for f in self.config_schema.get("fields", []):
            base_fields[f["key"]] = f

        if version_override:
            for f in version_override.get("fields", []):
                base_fields[f["key"]] = f

        result: list[ProviderConfigSchemaField] = []
        for f in base_fields.values():
            result.append(
                ProviderConfigSchemaField(
                    key=f["key"],
                    label=f.get("label", f["key"]),
                    type=f.get("type", "string"),
                    required=f.get("required", False),
                    credential=f.get("credential", False),
                    placeholder=f.get("placeholder"),
                    hint=f.get("hint"),
                    validation=f.get("validation"),
                    default=f.get("default"),
                    order=f.get("order", 0),
                )
            )
        result.sort(key=lambda x: (x.order, x.key))
        return result


@dataclass(frozen=True)
class ProviderVersion:
    id: str
    provider_code: str
    version_code: str
    name: str
    config_schema_override: dict | None
    is_active: bool
    is_default: bool
    created_at: str


@dataclass(frozen=True)
class ProviderDefinitionProperty:
    provider_code: str
    meta_key: str
    meta_value: str
