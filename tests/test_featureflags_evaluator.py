"""Heavy integration tests for the evaluator — scope precedence, overrides, rules, rollout, defaults."""
from __future__ import annotations

import os
from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_FLAG_PREFIX = "itest_ffe_"
_ORG_SLUGS = ("itest-ffe-org-a",)
_APP_CODES = ("itest_ffe_app_a",)


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        flag_rows = await conn.fetch(
            'SELECT id FROM "09_featureflags"."10_fct_flags" WHERE flag_key LIKE $1',
            f"{_FLAG_PREFIX}%",
        )
        flag_ids = [r["id"] for r in flag_rows]
        if flag_ids:
            await conn.execute(
                'DELETE FROM "09_featureflags"."21_fct_overrides" WHERE flag_id = ANY($1::text[])',
                flag_ids,
            )
            await conn.execute(
                'DELETE FROM "09_featureflags"."20_fct_rules" WHERE flag_id = ANY($1::text[])',
                flag_ids,
            )
            await conn.execute(
                'DELETE FROM "09_featureflags"."11_fct_flag_states" WHERE flag_id = ANY($1::text[])',
                flag_ids,
            )
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE event_key LIKE 'featureflags.%' AND metadata->>'flag_id' = ANY($1::text[])",
                flag_ids,
            )
            await conn.execute(
                'DELETE FROM "09_featureflags"."10_fct_flags" WHERE id = ANY($1::text[])',
                flag_ids,
            )

        app_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 6 AND d.code = 'code' AND a.key_text = ANY($1::text[])
            """,
            list(_APP_CODES),
        )
        app_ids = [r["id"] for r in app_rows]
        if app_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE metadata->>'application_id' = ANY($1::text[])",
                app_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=6 AND entity_id = ANY($1::text[])',
                app_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."15_fct_applications" WHERE id = ANY($1::text[])',
                app_ids,
            )

        org_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_ORG_SLUGS),
        )
        org_ids = [r["id"] for r in org_rows]
        if org_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE metadata->>'org_id' = ANY($1::text[])",
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=1 AND entity_id = ANY($1::text[])',
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."10_fct_orgs" WHERE id = ANY($1::text[])',
                org_ids,
            )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


async def _mk_flag(client: AsyncClient, **body: Any) -> dict:
    r = await client.post("/v1/flags", json=body)
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _toggle_env(client: AsyncClient, flag_id: str, env: str, enabled: bool) -> None:
    r = await client.get(f"/v1/flag-states?flag_id={flag_id}")
    st = next(s for s in r.json()["data"] if s["environment"] == env)
    r = await client.patch(
        f"/v1/flag-states/{st['id']}",
        json={"is_enabled": enabled},
    )
    assert r.status_code == 200


async def _evaluate(client: AsyncClient, flag_key: str, environment: str, **context: Any) -> dict:
    r = await client.post(
        "/v1/evaluate",
        json={"flag_key": flag_key, "environment": environment, "context": context},
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.mark.asyncio
async def test_flag_not_found_returns_null(live_app) -> None:
    client, _pool = live_app
    out = await _evaluate(client, f"{_FLAG_PREFIX}never_defined", "prod")
    assert out["value"] is None
    assert out["reason"] == "flag_not_found"


@pytest.mark.asyncio
async def test_flag_disabled_in_env_returns_default(live_app) -> None:
    client, _pool = live_app
    flag = await _mk_flag(
        client,
        scope="global",
        flag_key=f"{_FLAG_PREFIX}default_off",
        value_type="boolean",
        default_value=False,
    )
    # Leave states disabled (default after create)
    out = await _evaluate(client, flag["flag_key"], "prod")
    assert out["value"] is False
    assert out["reason"] == "flag_disabled_in_env"


@pytest.mark.asyncio
async def test_scope_precedence_application_over_org_over_global(live_app) -> None:
    client, _pool = live_app
    # Create org + app
    org = (await client.post("/v1/orgs", json={"slug": "itest-ffe-org-a", "display_name": "X"})).json()["data"]
    app = (await client.post(
        "/v1/applications",
        json={"org_id": org["id"], "code": "itest_ffe_app_a", "label": "A"},
    )).json()["data"]

    key = f"{_FLAG_PREFIX}scope_priority"
    g = await _mk_flag(client, scope="global", flag_key=key, value_type="string", default_value="g_default")
    o = await _mk_flag(client, scope="org", org_id=org["id"], flag_key=key, value_type="string", default_value="o_default")
    a = await _mk_flag(client, scope="application", org_id=org["id"], application_id=app["id"], flag_key=key, value_type="string", default_value="a_default")

    # Enable all three in prod, set env defaults
    for flag in (g, o, a):
        await _toggle_env(client, flag["id"], "prod", True)

    # No context → global only
    out = await _evaluate(client, key, "prod")
    assert out["flag_id"] == g["id"]
    assert out["flag_scope"] == "global"

    # Org context → org wins over global
    out = await _evaluate(client, key, "prod", org_id=org["id"])
    assert out["flag_id"] == o["id"]

    # App context (with org) → app wins over org
    out = await _evaluate(client, key, "prod", org_id=org["id"], application_id=app["id"])
    assert out["flag_id"] == a["id"]


@pytest.mark.asyncio
async def test_override_beats_rule(live_app) -> None:
    client, _pool = live_app
    flag = await _mk_flag(
        client,
        scope="global",
        flag_key=f"{_FLAG_PREFIX}override_vs_rule",
        value_type="boolean",
        default_value=False,
    )
    await _toggle_env(client, flag["id"], "prod", True)

    # Add a rule that fires for everyone with rollout 100 → value=true
    r = await client.post(
        "/v1/flag-rules",
        json={
            "flag_id": flag["id"],
            "environment": "prod",
            "priority": 0,
            "conditions": {"op": "true"},
            "value": True,
            "rollout_percentage": 100,
        },
    )
    assert r.status_code == 201

    # User override → false (overrides beat rules)
    r = await client.post(
        "/v1/flag-overrides",
        json={
            "flag_id": flag["id"],
            "environment": "prod",
            "entity_type": "user",
            "entity_id": "00000000-0000-0000-0000-0000000000aa",
            "value": False,
            "reason": "test",
        },
    )
    assert r.status_code == 201

    out = await _evaluate(
        client, flag["flag_key"], "prod",
        user_id="00000000-0000-0000-0000-0000000000aa",
    )
    assert out["value"] is False
    assert out["reason"] == "user_override"

    # Different user → rule fires → true
    out = await _evaluate(
        client, flag["flag_key"], "prod",
        user_id="00000000-0000-0000-0000-0000000000bb",
    )
    assert out["value"] is True
    assert out["reason"] == "rule_match"


@pytest.mark.asyncio
async def test_rule_condition_eq(live_app) -> None:
    client, _pool = live_app
    flag = await _mk_flag(
        client,
        scope="global",
        flag_key=f"{_FLAG_PREFIX}cond_eq",
        value_type="string",
        default_value="default",
    )
    await _toggle_env(client, flag["id"], "prod", True)

    await client.post(
        "/v1/flag-rules",
        json={
            "flag_id": flag["id"], "environment": "prod", "priority": 0,
            "conditions": {"op": "eq", "attr": "country", "value": "US"},
            "value": "us_variant", "rollout_percentage": 100,
        },
    )

    out = await _evaluate(
        client, flag["flag_key"], "prod",
        user_id="00000000-0000-0000-0000-000000000001",
        attrs={"country": "US"},
    )
    assert out["value"] == "us_variant"
    assert out["reason"] == "rule_match"

    out = await _evaluate(
        client, flag["flag_key"], "prod",
        user_id="00000000-0000-0000-0000-000000000002",
        attrs={"country": "UK"},
    )
    # No rule match → default_flag
    assert out["value"] == "default"
    assert out["reason"] == "default_flag"


@pytest.mark.asyncio
async def test_rule_rollout_determinism(live_app) -> None:
    client, _pool = live_app
    flag = await _mk_flag(
        client,
        scope="global",
        flag_key=f"{_FLAG_PREFIX}rollout_det",
        value_type="boolean",
        default_value=False,
    )
    await _toggle_env(client, flag["id"], "prod", True)

    # 50% rollout, condition always true
    await client.post(
        "/v1/flag-rules",
        json={
            "flag_id": flag["id"], "environment": "prod", "priority": 0,
            "conditions": {"op": "true"}, "value": True, "rollout_percentage": 50,
        },
    )

    # Same user_id → same answer across repeated calls
    user = "00000000-0000-0000-0000-0000000000cc"
    first = await _evaluate(client, flag["flag_key"], "prod", user_id=user)
    for _ in range(3):
        again = await _evaluate(client, flag["flag_key"], "prod", user_id=user)
        assert again["value"] == first["value"]
        assert again["reason"] == first["reason"]

    # Across ~200 synthetic users, we should see a spread of true/false
    trues = 0
    falses = 0
    for i in range(200):
        synth_user = f"00000000-0000-0000-0000-{i:012d}"
        res = await _evaluate(client, flag["flag_key"], "prod", user_id=synth_user)
        if res["value"] is True:
            trues += 1
        else:
            falses += 1
    # We expect roughly 50/50; allow wide bands for 200 samples
    assert 60 <= trues <= 140, f"distribution off: trues={trues} falses={falses}"


@pytest.mark.asyncio
async def test_evaluator_via_run_node(live_app) -> None:
    client, pool = live_app
    flag = await _mk_flag(
        client,
        scope="global",
        flag_key=f"{_FLAG_PREFIX}run_node",
        value_type="boolean",
        default_value=True,
    )
    await _toggle_env(client, flag["id"], "prod", True)
    # No rules, no overrides → reads flag default (true) with env_default=null fall-through

    ctx_base = _ctx_mod.NodeContext(
        audit_category="system", trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        result = await _catalog.run_node(
            pool, "featureflags.evaluations.resolve", ctx,
            {"flag_key": flag["flag_key"], "environment": "prod", "context": {}},
        )
    assert result["value"] is True
    assert result["reason"] == "default_flag"
