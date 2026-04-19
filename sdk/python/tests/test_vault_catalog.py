from __future__ import annotations

import httpx


# ---- vault secrets ---------------------------------------------------------


async def test_vault_secrets_list(respx_mock, client):
    respx_mock.get("/v1/vault").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": [{"key": "k1"}]})
    )
    rows = await client.vault.secrets.list()
    assert len(rows) == 1


async def test_vault_secrets_get(respx_mock, client):
    respx_mock.get("/v1/vault/db_password").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"key": "db_password", "value": "***"}})
    )
    secret = await client.vault.secrets.get("db_password")
    assert secret["key"] == "db_password"


async def test_vault_secrets_create(respx_mock, client):
    route = respx_mock.post("/v1/vault").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"key": "new_key"}})
    )
    await client.vault.secrets.create(key="new_key", value="super_secret", description="test")
    assert b"super_secret" in route.calls[0].request.content


async def test_vault_secrets_rotate(respx_mock, client):
    respx_mock.post("/v1/vault/k/rotate").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"key": "k", "rotated_at": "t"}})
    )
    result = await client.vault.secrets.rotate("k", value="new")
    assert "rotated_at" in result


async def test_vault_secrets_delete(respx_mock, client):
    route = respx_mock.delete("/v1/vault/k").mock(return_value=httpx.Response(204))
    await client.vault.secrets.delete("k")
    assert route.called


# ---- vault configs ---------------------------------------------------------


async def test_vault_configs_crud(respx_mock, client):
    respx_mock.get("/v1/vault-configs").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": [{"id": "c1"}]})
    )
    assert len(await client.vault.configs.list()) == 1

    respx_mock.get("/v1/vault-configs/c1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "c1"}})
    )
    assert (await client.vault.configs.get("c1"))["id"] == "c1"

    respx_mock.post("/v1/vault-configs").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"id": "c2"}})
    )
    assert (await client.vault.configs.create({"key": "x"}))["id"] == "c2"

    respx_mock.patch("/v1/vault-configs/c1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "c1", "v": "new"}})
    )
    assert (await client.vault.configs.update("c1", {"v": "new"}))["v"] == "new"

    respx_mock.delete("/v1/vault-configs/c1").mock(return_value=httpx.Response(204))
    await client.vault.configs.delete("c1")


# ---- catalog ---------------------------------------------------------------


async def test_catalog_list_nodes(respx_mock, client):
    respx_mock.get("/v1/catalog/nodes").mock(
        return_value=httpx.Response(
            200,
            json={"ok": True, "data": [{"key": "iam.users.get", "kind": "control"}]},
        )
    )
    nodes = await client.catalog.list_nodes()
    assert nodes[0]["key"] == "iam.users.get"


async def test_catalog_list_nodes_with_filter(respx_mock, client):
    route = respx_mock.get("/v1/catalog/nodes").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": []})
    )
    await client.catalog.list_nodes(feature="iam", kind="effect")
    assert "feature=iam" in str(route.calls[0].request.url)
