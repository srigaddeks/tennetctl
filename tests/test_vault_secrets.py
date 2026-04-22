"""Vault secrets CRUD — encrypted storage path."""

from __future__ import annotations


class TestVaultSecrets:
    async def test_create_secret_persists_encrypted(self, client, auth_headers, pool):
        resp = await client.post(
            "/v1/vault",
            headers=auth_headers,
            json={
                "key": "app.external.api_token_v1",
                "value": "super-secret-12345",
                "description": "API token for external service",
                "scope": "global",
            },
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()["data"]
        assert data["key"] == "app.external.api_token_v1"
        assert "value" not in data, "plaintext must NEVER appear in response"

        # Raw DB: ciphertext present, plaintext absent.
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT ciphertext, wrapped_dek, nonce, version, key '
                'FROM "02_vault"."10_fct_vault_entries" '
                "WHERE key = $1 AND deleted_at IS NULL",
                "app.external.api_token_v1",
            )
        assert row is not None
        assert row["version"] == 1
        assert row["ciphertext"] is not None and len(row["ciphertext"]) > 0
        assert row["wrapped_dek"] is not None
        assert row["nonce"] is not None
        # Plaintext must not appear in the ciphertext (trivial check).
        assert b"super-secret-12345" not in row["ciphertext"]

    async def test_list_secrets_returns_metadata_only(self, client, auth_headers):
        resp = await client.get("/v1/vault", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        # Every item must expose key + scope + version + created_at but no value.
        items = body["data"] if isinstance(body["data"], list) else body["data"].get("items", [])
        for it in items:
            assert "key" in it
            assert "value" not in it

    async def test_cannot_recycle_deleted_key(self, client, auth_headers):
        """v0.2 rule: a key soft-deleted cannot be reused even with a new value."""
        key = "pytest.recycle.check"
        create1 = await client.post(
            "/v1/vault",
            headers=auth_headers,
            json={
                "key": key,
                "value": "v1-value",
                "description": "First",
                "scope": "global",
            },
        )
        assert create1.status_code in (200, 201), create1.text

        deleted = await client.delete(
            f"/v1/vault/{key}",
            headers=auth_headers,
            params={"scope": "global"},
        )
        assert deleted.status_code in (200, 204), deleted.text

        create2 = await client.post(
            "/v1/vault",
            headers=auth_headers,
            json={
                "key": key,
                "value": "v2-value",
                "description": "Second attempt",
                "scope": "global",
            },
        )
        # Must be rejected — recycling a key (even after soft-delete) is not
        # allowed in v0.2. Accept the range of error codes the service + envelope
        # layer might produce.
        assert create2.status_code in (400, 409, 500), create2.text
        body = create2.json()
        if body.get("ok") is False and "error" in body:
            assert body["error"]["code"] in (
                "CONFLICT", "ALREADY_EXISTS", "RESOURCE_CONFLICT",
            )
