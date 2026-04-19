from __future__ import annotations

import httpx
import pytest


@pytest.mark.parametrize(
    "resource,path",
    [
        ("users", "/v1/users"),
        ("orgs", "/v1/orgs"),
        ("workspaces", "/v1/workspaces"),
        ("roles", "/v1/roles"),
        ("groups", "/v1/groups"),
    ],
)
async def test_iam_list(respx_mock, client, resource, path):
    respx_mock.get(path).mock(
        return_value=httpx.Response(200, json={"ok": True, "data": [{"id": "x"}]})
    )
    result = await getattr(client.iam, resource).list()
    assert len(result) == 1


async def test_iam_get(respx_mock, client):
    respx_mock.get("/v1/users/u1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "u1"}})
    )
    user = await client.iam.users.get("u1")
    assert user["id"] == "u1"


async def test_iam_list_forwards_filters(respx_mock, client):
    route = respx_mock.get("/v1/orgs").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": []})
    )
    await client.iam.orgs.list(status="active", limit=50)
    call = route.calls[0]
    assert "status=active" in str(call.request.url)
    assert "limit=50" in str(call.request.url)
