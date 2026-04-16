"""
Azure Storage asset driver.

Collects assets from Azure Resource Manager API directly.
Supports:
- azure_storage_account: Storage accounts within a subscription
- azure_blob_container: Blob containers within storage accounts
- azure_storage_network_rule: Network rules for storage accounts

Auth: Service Principal (client_id + client_secret + tenant_id).
Uses OAuth2 client credentials flow to get an access token, then calls
the Azure Resource Manager REST API directly (no Azure SDK dependency).

Rate limits: Azure ARM is generally permissive at ~1200 req/hour baseline.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from importlib import import_module as _import_module
_base_mod = _import_module("backend.10_sandbox.18_drivers.base")
AssetDriver = _base_mod.AssetDriver
_sp_base = _import_module("backend.10_sandbox.19_steampipe.base")
CollectedAsset = _sp_base.CollectedAsset
CollectionResult = _sp_base.CollectionResult
ConnectionConfig = _sp_base.ConnectionConfig
ConnectionTestResult = _sp_base.ConnectionTestResult

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
_ARM_SCOPE = "https://management.azure.com/.default"
_ARM_BASE = "https://management.azure.com"
_ARM_API_VERSION = "2023-01-01"
_ARM_CONTAINERS_API_VERSION = "2023-01-01"


class AzureStorageDriver(AssetDriver):
    """Direct Azure Resource Manager driver for storage asset collection."""

    def supports_provider(self, provider_code: str) -> bool:
        return provider_code == "azure_storage"

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        import time
        start = time.monotonic()
        try:
            token = await self._get_access_token(config)
            subscription_id = config.config.get("subscription_id", "")
            if not subscription_id:
                return ConnectionTestResult(success=False, message="Missing subscription_id in connection config")

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Validate subscription access
                resp = await client.get(
                    f"{_ARM_BASE}/subscriptions/{subscription_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"api-version": "2022-12-01"},
                )
                latency_ms = int((time.monotonic() - start) * 1000)

                if resp.status_code == 200:
                    sub = resp.json()
                    return ConnectionTestResult(
                        success=True,
                        message=f"Connected to Azure subscription '{sub.get('displayName', subscription_id)}'",
                        details={
                            "subscription_id": subscription_id,
                            "subscription_name": sub.get("displayName"),
                            "state": sub.get("state"),
                        },
                        latency_ms=latency_ms,
                    )
                elif resp.status_code == 401:
                    return ConnectionTestResult(
                        success=False, message="Authentication failed — service principal credentials invalid",
                        latency_ms=latency_ms,
                    )
                elif resp.status_code == 403:
                    return ConnectionTestResult(
                        success=False, message="Access denied — service principal lacks subscription Reader role",
                        latency_ms=latency_ms,
                    )
                elif resp.status_code == 404:
                    return ConnectionTestResult(
                        success=False, message=f"Subscription '{subscription_id}' not found",
                        latency_ms=latency_ms,
                    )
                else:
                    return ConnectionTestResult(
                        success=False, message=f"Unexpected response: HTTP {resp.status_code}",
                        latency_ms=latency_ms,
                    )
        except TokenError as e:
            return ConnectionTestResult(success=False, message=f"Token error: {e}")
        except Exception as e:
            return ConnectionTestResult(success=False, message=f"Connection test failed: {e}")

    async def collect_assets(
        self,
        config: ConnectionConfig,
        asset_types: list[str] | None = None,
        cursor: str | None = None,
    ) -> CollectionResult:
        collect_all = asset_types is None
        should_collect = lambda t: collect_all or t in asset_types  # noqa: E731

        all_assets: list[CollectedAsset] = []
        errors: list[str] = []

        try:
            token = await self._get_access_token(config)
        except TokenError as e:
            return CollectionResult(assets=[], errors=[f"Authentication failed: {e}"])

        subscription_id = config.config.get("subscription_id", "")
        resource_group = config.config.get("resource_group")  # Optional filter

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Authorization": f"Bearer {token}"}

            # Collect storage accounts
            storage_accounts: list[dict[str, Any]] = []
            if should_collect("azure_storage_account"):
                try:
                    sa_assets, storage_accounts = await self._collect_storage_accounts(
                        client, headers, subscription_id, resource_group
                    )
                    all_assets.extend(sa_assets)
                except Exception as e:
                    errors.append(f"azure_storage_account: {e}")
                    logger.warning("azure_collect_storage_accounts_failed", extra={"error": str(e)})

            # Collect blob containers
            if should_collect("azure_blob_container") and storage_accounts:
                try:
                    container_assets = await self._collect_blob_containers(
                        client, headers, subscription_id, storage_accounts
                    )
                    all_assets.extend(container_assets)
                except Exception as e:
                    errors.append(f"azure_blob_container: {e}")
                    logger.warning("azure_collect_containers_failed", extra={"error": str(e)})

        return CollectionResult(
            assets=all_assets,
            errors=errors,
            is_partial=len(errors) > 0 and len(all_assets) > 0,
        )

    async def _get_access_token(self, config: ConnectionConfig) -> str:
        tenant_id = config.config.get("tenant_id", "")
        client_id = config.config.get("client_id", "")
        client_secret = config.credentials.get("client_secret", "")

        if not all([tenant_id, client_id, client_secret]):
            raise TokenError("Missing required credentials: tenant_id, client_id, or client_secret")

        token_url = _TOKEN_URL.format(tenant_id=tenant_id)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": _ARM_SCOPE,
            })
            if resp.status_code != 200:
                raise TokenError(f"Token request failed: HTTP {resp.status_code}")
            data = resp.json()
            access_token = data.get("access_token")
            if not access_token:
                raise TokenError("Token response missing access_token")
            return access_token

    async def _collect_storage_accounts(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        subscription_id: str,
        resource_group: str | None,
    ) -> tuple[list[CollectedAsset], list[dict[str, Any]]]:
        if resource_group:
            url = f"{_ARM_BASE}/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts"
        else:
            url = f"{_ARM_BASE}/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts"

        assets: list[CollectedAsset] = []
        raw_accounts: list[dict[str, Any]] = []

        next_link: str | None = url
        params: dict[str, str] = {"api-version": _ARM_API_VERSION}

        while next_link:
            resp = await client.get(next_link if "api-version" in next_link else next_link, headers=headers, params=params if "api-version" not in next_link else None)
            resp.raise_for_status()
            data = resp.json()
            accounts = data.get("value", [])
            next_link = data.get("nextLink")
            params = {}  # nextLink already has params

            for acc in accounts:
                raw_accounts.append(acc)
                props = acc.get("properties", {})
                sku = acc.get("sku", {})
                enc = props.get("encryption", {})
                services = enc.get("services", {})
                network_acls = props.get("networkAcls", {})
                tags = acc.get("tags") or {}

                flat_props: dict[str, str] = {
                    "name": str(acc.get("name", "")),
                    "location": str(acc.get("location", "")),
                    "resource_group": str(acc.get("id", "").split("/")[4] if acc.get("id") else ""),
                    "kind": str(acc.get("kind", "")),
                    "sku_name": str(sku.get("name", "")),
                    "sku_tier": str(sku.get("tier", "")),
                    "access_tier": str(props.get("accessTier", "")),
                    "enable_https_traffic_only": str(props.get("supportsHttpsTrafficOnly", True)),
                    "allow_blob_public_access": str(props.get("allowBlobPublicAccess", False)),
                    "minimum_tls_version": str(props.get("minimumTlsVersion", "")),
                    "is_hns_enabled": str(props.get("isHnsEnabled", False)),
                    "large_file_shares_state": str(props.get("largeFileSharesState", "")),
                    "blob_encryption_enabled": str(services.get("blob", {}).get("enabled", False)),
                    "file_encryption_enabled": str(services.get("file", {}).get("enabled", False)),
                    "network_acls_default_action": str(network_acls.get("defaultAction", "")),
                    "network_acls_bypass": str(network_acls.get("bypass", "")),
                    "creation_time": str(props.get("creationTime", "")),
                    "primary_location": str(props.get("primaryLocation", "")),
                    "provisioning_state": str(props.get("provisioningState", "")),
                }
                # Flatten tags
                for tag_key, tag_val in tags.items():
                    flat_props[f"tag_{tag_key}"] = str(tag_val)

                assets.append(CollectedAsset(
                    external_id=acc["id"],
                    asset_type_code="azure_storage_account",
                    properties=flat_props,
                ))

        return assets, raw_accounts

    async def _collect_blob_containers(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        subscription_id: str,
        storage_accounts: list[dict[str, Any]],
    ) -> list[CollectedAsset]:
        assets: list[CollectedAsset] = []
        for acc in storage_accounts:
            acc_name = acc.get("name", "")
            acc_id = acc.get("id", "")
            rg = acc_id.split("/")[4] if acc_id else ""
            url = (
                f"{_ARM_BASE}/subscriptions/{subscription_id}/resourceGroups/{rg}"
                f"/providers/Microsoft.Storage/storageAccounts/{acc_name}/blobServices/default/containers"
            )
            try:
                resp = await client.get(url, headers=headers, params={"api-version": _ARM_CONTAINERS_API_VERSION})
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for container in data.get("value", []):
                    props = container.get("properties", {})
                    assets.append(CollectedAsset(
                        external_id=container["id"],
                        asset_type_code="azure_blob_container",
                        properties={
                            "name": str(container.get("name", "")),
                            "storage_account_name": acc_name,
                            "resource_group": rg,
                            "public_access": str(props.get("publicAccess", "None")),
                            "default_encryption_scope": str(props.get("defaultEncryptionScope", "")),
                            "deny_encryption_scope_override": str(props.get("denyEncryptionScopeOverride", False)),
                            "has_immutability_policy": str(props.get("hasImmutabilityPolicy", False)),
                            "has_legal_hold": str(props.get("hasLegalHold", False)),
                            "deleted": str(props.get("deleted", False)),
                            "lease_status": str(props.get("leaseStatus", "")),
                            "lease_state": str(props.get("leaseState", "")),
                        },
                        parent_external_id=acc_id,
                        parent_asset_type_code="azure_storage_account",
                    ))
            except Exception as e:
                logger.debug("azure_collect_containers_failed_for_account", extra={"account": acc_name, "error": str(e)})
        return assets


class TokenError(Exception):
    """Raised when OAuth token acquisition fails."""
