from __future__ import annotations

import httpx


async def test_evaluate_posts_and_returns_result(respx_mock, client):
    route = respx_mock.post("/v1/evaluate").mock(
        return_value=httpx.Response(
            200,
            json={"ok": True, "data": {"value": True, "source": "rule", "matched_rule_id": "r1"}},
        )
    )
    result = await client.flags.evaluate("new-onboarding", entity="user:1")
    assert result == {"value": True, "source": "rule", "matched_rule_id": "r1"}
    body = route.calls[0].request.content
    assert b"new-onboarding" in body
    assert b"user:1" in body


async def test_evaluate_caches_within_ttl(respx_mock, client):
    respx_mock.post("/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"value": "A"}})
    )
    r1 = await client.flags.evaluate("flag", entity="u1")
    r2 = await client.flags.evaluate("flag", entity="u1")
    assert r1 == r2
    # Only one HTTP call despite two evaluations
    assert len(respx_mock.routes[0].calls) == 1


async def test_evaluate_bypasses_cache_for_different_entity(respx_mock, client):
    respx_mock.post("/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"value": "X"}})
    )
    await client.flags.evaluate("flag", entity="u1")
    await client.flags.evaluate("flag", entity="u2")
    assert len(respx_mock.routes[0].calls) == 2


async def test_evaluate_includes_context(respx_mock, client):
    route = respx_mock.post("/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"value": True}})
    )
    await client.flags.evaluate("flag", entity="u1", context={"country": "US"})
    body = route.calls[0].request.content
    assert b"country" in body and b"US" in body


async def test_invalidate_clears_cache(respx_mock, client):
    respx_mock.post("/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"value": "v"}})
    )
    await client.flags.evaluate("f", entity="u")
    client.flags.invalidate("f")
    await client.flags.evaluate("f", entity="u")
    assert len(respx_mock.routes[0].calls) == 2


async def test_evaluate_bulk(respx_mock, client):
    respx_mock.post("/v1/evaluate/bulk").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": [{"value": 1}, {"value": 2}]}
        )
    )
    results = await client.flags.evaluate_bulk(
        [{"key": "a", "entity": "u1"}, {"key": "b", "entity": "u1"}]
    )
    assert len(results) == 2
