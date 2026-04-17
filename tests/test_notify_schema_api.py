"""
Integration tests for notify.smtp_configs, notify.template_groups, notify.templates.

Each test is self-contained: creates its own data, asserts, and the fixture
tears down all notify rows for the test org after each test.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID = "019e0000-1111-7000-0000-000000000001"
_WS_ID  = "019e0000-1111-7000-0000-000000000002"
_USER_ID = "019e0000-1111-7000-0000-000000000003"
_SESSION_ID = "019e0000-1111-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM \"06_notify\".\"12_fct_notify_templates\" WHERE org_id = $1",
            _ORG_ID,
        )
        await conn.execute(
            "DELETE FROM \"06_notify\".\"11_fct_notify_template_groups\" WHERE org_id = $1",
            _ORG_ID,
        )
        await conn.execute(
            "DELETE FROM \"06_notify\".\"10_fct_notify_smtp_configs\" WHERE org_id = $1",
            _ORG_ID,
        )
        await conn.execute(
            "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE actor_user_id = $1",
            _USER_ID,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
                headers=_HDR,
            ) as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _create_smtp(client: Any, key: str = "smtp-key") -> dict:
    r = await client.post("/v1/notify/smtp-configs", json={
        "org_id": _ORG_ID, "key": key, "label": "Test SMTP",
        "host": "smtp.example.com", "port": 587, "tls": True,
        "username": "noreply@example.com",
        "auth_vault_key": f"notify.smtp.{key}.password",
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_group(client: Any, key: str = "test-group", category_id: int = 1) -> dict:
    r = await client.post("/v1/notify/template-groups", json={
        "org_id": _ORG_ID, "key": key, "label": "Test Group", "category_id": category_id,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_template(client: Any, group_id: str, key: str = "test-tmpl", bodies: list | None = None) -> dict:
    body: dict = {
        "org_id": _ORG_ID, "key": key, "group_id": group_id,
        "subject": "Hello {{ name }}!", "priority_id": 2,
    }
    if bodies:
        body["bodies"] = bodies
    r = await client.post("/v1/notify/templates", json=body)
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ─── SMTP Configs ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_smtp_config(live_app):
    client, _ = live_app
    d = await _create_smtp(client, "transactional")
    assert d["key"] == "transactional"
    assert d["host"] == "smtp.example.com"
    assert d["tls"] is True
    assert d["org_id"] == _ORG_ID


@pytest.mark.asyncio
async def test_list_smtp_configs(live_app):
    client, _ = live_app
    await _create_smtp(client, "config-a")
    await _create_smtp(client, "config-b")
    r = await client.get(f"/v1/notify/smtp-configs?org_id={_ORG_ID}")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["total"] == 2
    keys = {c["key"] for c in d["items"]}
    assert keys == {"config-a", "config-b"}


@pytest.mark.asyncio
async def test_get_smtp_config(live_app):
    client, _ = live_app
    created = await _create_smtp(client, "get-me")
    r = await client.get(f"/v1/notify/smtp-configs/{created['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == created["id"]


@pytest.mark.asyncio
async def test_update_smtp_config(live_app):
    client, _ = live_app
    created = await _create_smtp(client, "update-me")
    r = await client.patch(f"/v1/notify/smtp-configs/{created['id']}", json={"label": "New Label"})
    assert r.status_code == 200
    assert r.json()["data"]["label"] == "New Label"


@pytest.mark.asyncio
async def test_soft_delete_smtp_config(live_app):
    client, _ = live_app
    created = await _create_smtp(client, "delete-me")
    r = await client.delete(f"/v1/notify/smtp-configs/{created['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/v1/notify/smtp-configs/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_smtp_config_not_found(live_app):
    client, _ = live_app
    r = await client.get("/v1/notify/smtp-configs/no-such-id")
    assert r.status_code == 404


# ─── Template Groups ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_template_group_transactional(live_app):
    client, _ = live_app
    d = await _create_group(client, "tx-group", category_id=1)
    assert d["key"] == "tx-group"
    assert d["category_code"] == "transactional"
    assert d["smtp_config_id"] is None


@pytest.mark.asyncio
async def test_create_template_group_critical(live_app):
    client, _ = live_app
    d = await _create_group(client, "crit-group", category_id=2)
    assert d["category_code"] == "critical"


@pytest.mark.asyncio
async def test_list_template_groups(live_app):
    client, _ = live_app
    await _create_group(client, "grp-one", 1)
    await _create_group(client, "grp-two", 3)
    r = await client.get(f"/v1/notify/template-groups?org_id={_ORG_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_get_template_group(live_app):
    client, _ = live_app
    created = await _create_group(client, "get-grp")
    r = await client.get(f"/v1/notify/template-groups/{created['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == created["id"]


@pytest.mark.asyncio
async def test_update_template_group(live_app):
    client, _ = live_app
    created = await _create_group(client, "upd-grp")
    r = await client.patch(f"/v1/notify/template-groups/{created['id']}", json={"label": "Renamed"})
    assert r.status_code == 200
    assert r.json()["data"]["label"] == "Renamed"


@pytest.mark.asyncio
async def test_soft_delete_template_group(live_app):
    client, _ = live_app
    created = await _create_group(client, "del-grp")
    r = await client.delete(f"/v1/notify/template-groups/{created['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/v1/notify/template-groups/{created['id']}")
    assert r2.status_code == 404


# ─── Templates ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_template_no_bodies(live_app):
    client, _ = live_app
    group = await _create_group(client, "g1")
    d = await _create_template(client, group["id"], "tmpl-no-body")
    assert d["key"] == "tmpl-no-body"
    assert d["bodies"] == []


@pytest.mark.asyncio
async def test_create_template_with_bodies(live_app):
    client, _ = live_app
    group = await _create_group(client, "g2")
    d = await _create_template(client, group["id"], "tmpl-with-body", bodies=[{
        "channel_id": 1,
        "body_html": "<p>Click <a href='{{ reset_url }}'>here</a></p>",
        "body_text": "Click here: {{ reset_url }}",
        "preheader": "Reset your password",
    }])
    assert len(d["bodies"]) == 1
    assert d["bodies"][0]["channel_id"] == 1


@pytest.mark.asyncio
async def test_list_templates(live_app):
    client, _ = live_app
    group = await _create_group(client, "g3")
    await _create_template(client, group["id"], "tmpl-a")
    await _create_template(client, group["id"], "tmpl-b")
    r = await client.get(f"/v1/notify/templates?org_id={_ORG_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_get_template(live_app):
    client, _ = live_app
    group = await _create_group(client, "g4")
    created = await _create_template(client, group["id"], "get-me-tmpl")
    r = await client.get(f"/v1/notify/templates/{created['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == created["id"]


@pytest.mark.asyncio
async def test_update_template(live_app):
    client, _ = live_app
    group = await _create_group(client, "g5")
    created = await _create_template(client, group["id"], "upd-me-tmpl")
    r = await client.patch(f"/v1/notify/templates/{created['id']}", json={"subject": "Updated {{ name }}"})
    assert r.status_code == 200
    assert "Updated" in r.json()["data"]["subject"]


@pytest.mark.asyncio
async def test_upsert_bodies_multi_channel(live_app):
    client, _ = live_app
    group = await _create_group(client, "g6")
    created = await _create_template(client, group["id"], "bodies-tmpl")
    r = await client.put(f"/v1/notify/templates/{created['id']}/bodies", json={"bodies": [
        {"channel_id": 1, "body_html": "<p>Hi {{ name }}</p>", "body_text": "Hi {{ name }}"},
        {"channel_id": 3, "body_html": "Welcome {{ name }}", "body_text": "Welcome {{ name }}"},
    ]})
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["bodies"]) == 2
    assert {b["channel_id"] for b in d["bodies"]} == {1, 3}


@pytest.mark.asyncio
async def test_upsert_bodies_idempotent(live_app):
    """Upserting same channel twice overwrites body content."""
    client, _ = live_app
    group = await _create_group(client, "g7")
    created = await _create_template(client, group["id"], "idem-tmpl")
    # First upsert
    await client.put(f"/v1/notify/templates/{created['id']}/bodies", json={"bodies": [
        {"channel_id": 1, "body_html": "<p>First</p>", "body_text": "First"},
    ]})
    # Second upsert — should overwrite
    r = await client.put(f"/v1/notify/templates/{created['id']}/bodies", json={"bodies": [
        {"channel_id": 1, "body_html": "<p>Second {{ name }}</p>", "body_text": "Second {{ name }}"},
    ]})
    assert r.status_code == 200
    body = next(b for b in r.json()["data"]["bodies"] if b["channel_id"] == 1)
    assert "Second" in body["body_html"]
    assert "First" not in body["body_html"]


@pytest.mark.asyncio
async def test_soft_delete_template(live_app):
    client, _ = live_app
    group = await _create_group(client, "g8")
    created = await _create_template(client, group["id"], "del-me-tmpl")
    r = await client.delete(f"/v1/notify/templates/{created['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/v1/notify/templates/{created['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_template_not_found(live_app):
    client, _ = live_app
    r = await client.get("/v1/notify/templates/no-such-id")
    assert r.status_code == 404


# ─── notify.templates.render node ─────────────────────────────────────────────

def _make_ctx(pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        org_id=_ORG_ID,
        workspace_id=_WS_ID,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="system",
        extras={"pool": pool},
    )


@pytest.mark.asyncio
async def test_render_with_static_variables(live_app):
    """Render email body with Jinja2 variable substitution; static subject passes through."""
    client, pool = live_app
    group = await _create_group(client, "render-grp")
    # Use a static subject (no Jinja2 vars) so StrictUndefined doesn't fire on it
    r = await client.post("/v1/notify/templates", json={
        "org_id": _ORG_ID, "key": "reset-tmpl", "group_id": group["id"],
        "subject": "Reset your password",
        "bodies": [{
            "channel_id": 1,
            "body_html": "<p>Click <a href='{{ reset_url }}'>here</a></p>",
            "body_text": "Click here: {{ reset_url }}",
        }],
    })
    assert r.status_code == 201

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = ctx.__class__(**{**ctx.__dict__, "conn": conn})
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "reset-tmpl",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {"reset_url": "https://example.com/reset/abc123"},
            },
        )
    assert "abc123" in result["rendered_html"]
    assert "abc123" in result["rendered_text"]
    assert result["rendered_subject"] == "Reset your password"


@pytest.mark.asyncio
async def test_render_subject_interpolation(live_app):
    """Subject is also Jinja2 — variables are applied."""
    client, pool = live_app
    group = await _create_group(client, "subj-grp")
    r = await client.post("/v1/notify/templates", json={
        "org_id": _ORG_ID, "key": "subj-tmpl", "group_id": group["id"],
        "subject": "Welcome, {{ name }}!",
        "bodies": [{"channel_id": 1, "body_html": "<p>Hi</p>", "body_text": "Hi"}],
    })
    assert r.status_code == 201

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = ctx.__class__(**{**ctx.__dict__, "conn": conn})
        result = await _catalog.run_node(
            pool, "notify.templates.render", ctx2,
            {
                "template_key": "subj-tmpl",
                "org_id": _ORG_ID,
                "channel": "email",
                "variables": {"name": "Alice"},
            },
        )
    assert result["rendered_subject"] == "Welcome, Alice!"


@pytest.mark.asyncio
async def test_render_missing_variable_raises(live_app):
    """StrictUndefined raises UndefinedError when required variable absent."""
    import jinja2
    client, pool = live_app
    group = await _create_group(client, "strict-grp")
    await _create_template(client, group["id"], "strict-tmpl", bodies=[{
        "channel_id": 1,
        "body_html": "<p>{{ required_var }}</p>",
        "body_text": "{{ required_var }}",
    }])

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = ctx.__class__(**{**ctx.__dict__, "conn": conn})
        with pytest.raises(jinja2.UndefinedError):
            await _catalog.run_node(
                pool, "notify.templates.render", ctx2,
                {
                    "template_key": "strict-tmpl",
                    "org_id": _ORG_ID,
                    "channel": "email",
                    "variables": {},
                },
            )


@pytest.mark.asyncio
async def test_render_missing_template_raises(live_app):
    """ValueError raised when template key not found."""
    _, pool = live_app
    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = ctx.__class__(**{**ctx.__dict__, "conn": conn})
        with pytest.raises(ValueError, match="not found"):
            await _catalog.run_node(
                pool, "notify.templates.render", ctx2,
                {
                    "template_key": "completely-nonexistent",
                    "org_id": _ORG_ID,
                    "channel": "email",
                    "variables": {},
                },
            )


@pytest.mark.asyncio
async def test_render_missing_channel_body_raises(live_app):
    """ValueError raised when template has no body for the requested channel."""
    client, pool = live_app
    group = await _create_group(client, "chan-grp")
    await _create_template(client, group["id"], "email-only-tmpl", bodies=[{
        "channel_id": 1,  # email only
        "body_html": "<p>Email only</p>",
        "body_text": "Email only",
    }])

    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        ctx2 = ctx.__class__(**{**ctx.__dict__, "conn": conn})
        with pytest.raises(ValueError, match="no body"):
            await _catalog.run_node(
                pool, "notify.templates.render", ctx2,
                {
                    "template_key": "email-only-tmpl",
                    "org_id": _ORG_ID,
                    "channel": "webpush",  # no webpush body
                    "variables": {},
                },
            )
