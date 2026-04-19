from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class VaultSecrets:
    """Vault secrets — get/list/create/rotate/delete.

    The SDK never caches plaintext. `get_secret` is a hot-path call; the
    backend's own 60s SWR cache in VaultClient handles the perf concern.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request("GET", "/v1/vault", params=params or None)
        return data if isinstance(data, list) else list(data or [])

    async def get(self, key: str) -> dict:
        """Retrieve a secret. Returns the envelope including the plaintext
        value — callers must handle the value carefully and never log it."""
        return await self._t.request("GET", f"/v1/vault/{key}")

    async def create(
        self,
        *,
        key: str,
        value: str,
        description: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {"key": key, "value": value}
        if description is not None:
            body["description"] = description
        return await self._t.request("POST", "/v1/vault", json=body)

    async def rotate(self, key: str, *, value: str) -> dict:
        return await self._t.request(
            "POST", f"/v1/vault/{key}/rotate", json={"value": value}
        )

    async def delete(self, key: str) -> None:
        await self._t.request("DELETE", f"/v1/vault/{key}")


class VaultConfigs:
    """Vault configs — non-secret, operator-visible configuration keys."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request("GET", "/v1/vault-configs", params=params or None)
        return data if isinstance(data, list) else list(data or [])

    async def get(self, config_id: str) -> dict:
        return await self._t.request("GET", f"/v1/vault-configs/{config_id}")

    async def create(self, body: dict) -> dict:
        return await self._t.request("POST", "/v1/vault-configs", json=body)

    async def update(self, config_id: str, patch: dict) -> dict:
        return await self._t.request(
            "PATCH", f"/v1/vault-configs/{config_id}", json=patch
        )

    async def delete(self, config_id: str) -> None:
        await self._t.request("DELETE", f"/v1/vault-configs/{config_id}")


class Vault:
    def __init__(self, transport: Transport) -> None:
        self.secrets = VaultSecrets(transport)
        self.configs = VaultConfigs(transport)
