"""
Integration tests for notify.subscriptions CRUD + delivery creation + worker fan-out.

Uses a distinct org ID (3333 middle) to avoid collisions with other notify tests.
Function-scoped live_app fixture to avoid asyncpg cross-loop issues.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_sub_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.05_subscriptions.service"
)
_worker: Any = import_module("backend.02_features.06_notify.worker")
_core_id: Any = import_module("backend.01_core.id")
_outbox_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.repository"
)

_ORG_ID     = "019e0000-3333-7000-0000-000000000001"
_WS_ID      = "019e0000-3333-7000-0000-000000000002"
_USER_ID    = "019e0000-3333-7000-0000-000000000003"
_SESSION_ID = "019e0000-3333-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Deliveries FK → subscriptions. Subscriptions FK → templates.
        # Cascade won't cover subscriptions automatically, so delete deliveries first.
        await conn.execute(
            'DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."14_fct_notify_subscriptions" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = $1',
            _ORG_ID,
        )
        # Audit outbox: don't delete real outbox rows (they are global); just audit events
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE actor_user_id = $1',
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

async def _create_group(client: Any, key: str, category_id: int = 1) -> dict:
    r = await client.post("/v1/notify/template-groups", json={
        "org_id": _ORG_ID, "key": key, "label": "Test Group", "category_id": category_id,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_template(
    client: Any,
    group_id: str,
    key: str,
    subject: str = "Test subject",
) -> dict:
    r = await client.post("/v1/notify/templates", json={
        "org_id": _ORG_ID, "key": key, "group_id": group_id,
        "subject": subject,
        "bodies": [{"channel_id": 1, "body_html": "<p>Hello</p>", "body_text": "Hello"}],
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _create_subscription(
    client: Any,
    template_id: str,
    event_key_pattern: str = "iam.users.created",
    channel_id: int = 1,
    name: str = "Test Subscription",
) -> dict:
    r = await client.post("/v1/notify/subscriptions", json={
        "org_id": _ORG_ID,
        "name": name,
        "event_key_pattern": event_key_pattern,
        "template_id": template_id,
        "channel_id": channel_id,
    })
    assert r.status_code == 201, r.text
    return r.json()["data"]


async def _insert_audit_event(pool: Any, event_key: str = "iam.users.created") -> dict:
    """Insert a synthetic audit event + outbox row and return the outbox entry."""
    event_id = _core_id.uuid7()
    async with pool.acquire() as conn:
        # Insert audit event
        await conn.execute(
            """
            INSERT INTO "04_audit"."60_evt_audit"
                (id, event_key, audit_category, actor_user_id, actor_session_id,
                 org_id, workspace_id, trace_id, span_id,
                 outcome, metadata)
            VALUES ($1, $2, 'system', $3, $4, $5, $6, $7, $8, 'success', '{}')
            """,
            event_id, event_key, _USER_ID, _SESSION_ID,
            _ORG_ID, _WS_ID, _core_id.uuid7(), _core_id.uuid7(),
        )
        # The trigger will insert into the outbox and NOTIFY automatically.
        # Fetch the outbox row for the cursor.
        outbox_row = await conn.fetchrow(
            'SELECT id AS outbox_id, event_id FROM "04_audit"."61_evt_audit_outbox" WHERE event_id = $1',
            event_id,
        )
    return dict(outbox_row)


# ─── Pattern matching tests (pure Python — no DB) ─────────────────────────────

@pytest.mark.asyncio
async def test_pattern_exact_match():
    assert _sub_service.matches_pattern("iam.users.created", "iam.users.created") is True


@pytest.mark.asyncio
async def test_pattern_no_match():
    assert _sub_service.matches_pattern("iam.users.deleted", "iam.users.created") is False


@pytest.mark.asyncio
async def test_pattern_suffix_wildcard():
    assert _sub_service.matches_pattern("iam.users.created", "iam.users.*") is True
    assert _sub_service.matches_pattern("iam.users.updated", "iam.users.*") is True
    assert _sub_service.matches_pattern("iam.orgs.created", "iam.users.*") is False


@pytest.mark.asyncio
async def test_pattern_deep_wildcard():
    assert _sub_service.matches_pattern("iam.users.created", "iam.*") is True
    assert _sub_service.matches_pattern("iam.orgs.deleted", "iam.*") is True
    assert _sub_service.matches_pattern("audit.events.emitted", "iam.*") is False


@pytest.mark.asyncio
async def test_pattern_global_wildcard():
    assert _sub_service.matches_pattern("anything.goes.here", "*") is True
    assert _sub_service.matches_pattern("iam.users.created", "*") is True


# ─── Subscription CRUD tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_subscription(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-create")
    tmpl = await _create_template(client, grp["id"], "t-sub-create")

    sub = await _create_subscription(client, tmpl["id"])

    assert sub["id"]
    assert sub["org_id"] == _ORG_ID
    assert sub["event_key_pattern"] == "iam.users.created"
    assert sub["channel_code"] == "email"
    assert sub["is_active"] is True


@pytest.mark.asyncio
async def test_list_subscriptions_empty(live_app):
    client, _ = live_app
    r = await client.get(f"/v1/notify/subscriptions?org_id={_ORG_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_subscriptions_returns_created(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-list")
    tmpl = await _create_template(client, grp["id"], "t-sub-list")
    await _create_subscription(client, tmpl["id"], name="Sub 1")
    await _create_subscription(client, tmpl["id"], name="Sub 2", event_key_pattern="iam.*")

    r = await client.get(f"/v1/notify/subscriptions?org_id={_ORG_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_get_subscription(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-get")
    tmpl = await _create_template(client, grp["id"], "t-sub-get")
    sub = await _create_subscription(client, tmpl["id"])

    r = await client.get(f"/v1/notify/subscriptions/{sub['id']}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == sub["id"]


@pytest.mark.asyncio
async def test_update_subscription_name(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-upd")
    tmpl = await _create_template(client, grp["id"], "t-sub-upd")
    sub = await _create_subscription(client, tmpl["id"])

    r = await client.patch(f"/v1/notify/subscriptions/{sub['id']}", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_subscription(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-del")
    tmpl = await _create_template(client, grp["id"], "t-sub-del")
    sub = await _create_subscription(client, tmpl["id"])

    r = await client.delete(f"/v1/notify/subscriptions/{sub['id']}")
    assert r.status_code == 204

    r2 = await client.get(f"/v1/notify/subscriptions/{sub['id']}")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_subscription_invalid_pattern(live_app):
    client, _ = live_app
    grp = await _create_group(client, "g-sub-pat")
    tmpl = await _create_template(client, grp["id"], "t-sub-pat")
    r = await client.post("/v1/notify/subscriptions", json={
        "org_id": _ORG_ID,
        "name": "Bad Pattern",
        "event_key_pattern": "has spaces in it",
        "template_id": tmpl["id"],
        "channel_id": 1,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_subscription_missing_required(live_app):
    client, _ = live_app
    r = await client.post("/v1/notify/subscriptions", json={
        "org_id": _ORG_ID,
        "name": "No Pattern",
        # missing event_key_pattern, template_id, channel_id
    })
    assert r.status_code == 422


# ─── Worker + delivery creation tests ────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_creates_delivery_on_matching_event(live_app):
    """Matching audit event → subscription matched → delivery row created."""
    client, pool = live_app
    grp = await _create_group(client, "g-wkr-match")
    tmpl = await _create_template(client, grp["id"], "t-wkr-match")
    await _create_subscription(client, tmpl["id"], event_key_pattern="iam.users.created")

    # Get cursor before inserting event
    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "iam.users.created")

    new_cursor = await _worker.process_audit_events(pool, start_cursor)
    assert new_cursor > start_cursor

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT * FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
    assert len(rows) == 1
    assert rows[0]["recipient_user_id"] == _USER_ID
    assert rows[0]["channel_id"] == 1  # email


@pytest.mark.asyncio
async def test_worker_no_delivery_different_org(live_app):
    """Subscription for org A does not create delivery for org B event."""
    client, pool = live_app
    grp = await _create_group(client, "g-wkr-org")
    tmpl = await _create_template(client, grp["id"], "t-wkr-org")
    await _create_subscription(client, tmpl["id"])  # org = _ORG_ID

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    # Insert event for a DIFFERENT org (not _ORG_ID)
    other_org = "019e0000-9999-7000-0000-000000000001"
    event_id = _core_id.uuid7()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO "04_audit"."60_evt_audit"
                (id, event_key, audit_category, actor_user_id, actor_session_id,
                 org_id, workspace_id, trace_id, span_id, outcome, metadata)
            VALUES ($1, 'iam.users.created', 'system', $2, $3, $4, $5, $6, $7, 'success', '{}')
            """,
            event_id, _USER_ID, _SESSION_ID,
            other_org, _WS_ID, _core_id.uuid7(), _core_id.uuid7(),
        )

    await _worker.process_audit_events(pool, start_cursor)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT * FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_worker_no_delivery_pattern_mismatch(live_app):
    """Subscription pattern 'iam.users.*' does not match 'audit.events.emitted'."""
    client, pool = live_app
    grp = await _create_group(client, "g-wkr-mism")
    tmpl = await _create_template(client, grp["id"], "t-wkr-mism")
    await _create_subscription(client, tmpl["id"], event_key_pattern="iam.users.*")

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "audit.events.emitted")  # does NOT match iam.users.*
    await _worker.process_audit_events(pool, start_cursor)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT * FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_worker_critical_fanout(live_app):
    """Critical template group → 3 deliveries (email + webpush + in_app) for one event."""
    client, pool = live_app
    # category_id=2 = critical
    grp = await _create_group(client, "g-wkr-crit", category_id=2)
    tmpl = await _create_template(client, grp["id"], "t-wkr-crit")
    await _create_subscription(client, tmpl["id"], channel_id=1)  # email-only sub

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "iam.users.created")
    await _worker.process_audit_events(pool, start_cursor)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT channel_id FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1 ORDER BY channel_id',
            _ORG_ID,
        )
    channel_ids = [r["channel_id"] for r in rows]
    assert sorted(channel_ids) == [1, 2, 3], f"Expected [1,2,3] got {channel_ids}"


@pytest.mark.asyncio
async def test_worker_delivery_stores_resolved_variables(live_app):
    """Delivery row stores resolved_variables snapshot from variable registry."""
    client, pool = live_app
    grp = await _create_group(client, "g-wkr-vars")
    tmpl = await _create_template(client, grp["id"], "t-wkr-vars")
    # Register a static variable
    await client.post(f"/v1/notify/templates/{tmpl['id']}/variables", json={
        "name": "brand", "var_type": "static", "static_value": "ACME Corp",
    })
    await _create_subscription(client, tmpl["id"])

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "iam.users.created")
    await _worker.process_audit_events(pool, start_cursor)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT resolved_variables FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
    assert row["resolved_variables"]["brand"] == "ACME Corp"


# ─── Delivery API tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delivery_list_empty(live_app):
    client, _ = live_app
    r = await client.get(f"/v1/notify/deliveries?org_id={_ORG_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_delivery_list_after_worker(live_app):
    """Worker creates deliveries → list returns them."""
    client, pool = live_app
    grp = await _create_group(client, "g-dlv-list")
    tmpl = await _create_template(client, grp["id"], "t-dlv-list")
    await _create_subscription(client, tmpl["id"])

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "iam.users.created")
    await _worker.process_audit_events(pool, start_cursor)

    r = await client.get(f"/v1/notify/deliveries?org_id={_ORG_ID}&status=queued")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["status_code"] == "queued"


@pytest.mark.asyncio
async def test_delivery_get_one(live_app):
    """GET /v1/notify/deliveries/{id} returns the delivery."""
    client, pool = live_app
    grp = await _create_group(client, "g-dlv-get")
    tmpl = await _create_template(client, grp["id"], "t-dlv-get")
    await _create_subscription(client, tmpl["id"])

    async with pool.acquire() as conn:
        start_cursor = await _outbox_repo.latest_outbox_id(conn)

    await _insert_audit_event(pool, "iam.users.created")
    await _worker.process_audit_events(pool, start_cursor)

    # Get the first delivery ID
    r_list = await client.get(f"/v1/notify/deliveries?org_id={_ORG_ID}")
    delivery_id = r_list.json()["data"]["items"][0]["id"]

    r = await client.get(f"/v1/notify/deliveries/{delivery_id}")
    assert r.status_code == 200
    assert r.json()["data"]["id"] == delivery_id
    assert r.json()["data"]["channel_code"] == "email"
