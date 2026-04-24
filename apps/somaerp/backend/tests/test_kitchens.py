"""Real-Postgres tests for /v1/somaerp/geography/kitchens.

Covers CRUD + the status state machine (active<->paused, *->decommissioned
terminal) + audit key routing (status change vs. non-status change) + FK
validation against fct_locations.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


# ── Helpers ──────────────────────────────────────────────────────────────

async def _create_location(client: AsyncClient, headers: dict) -> dict:
    r = await client.post(
        "/v1/somaerp/geography/locations",
        json={
            "region_id": 1,
            "name": "Hyderabad",
            "slug": "hyderabad",
            "timezone": "Asia/Kolkata",
            "properties": {},
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


def _kitchen_payload(location_id: str, slug: str = "kphb-home") -> dict:
    return {
        "location_id": location_id,
        "name": "KPHB Home Kitchen",
        "slug": slug,
        "kitchen_type": "home",
        "address_jsonb": {"line": "KPHB", "pincode": "500072"},
        "status": "active",
        "properties": {},
    }


async def _create_kitchen(
    client: AsyncClient, headers: dict, *, location_id: str,
    slug: str = "kphb-home",
) -> dict:
    r = await client.post(
        "/v1/somaerp/geography/kitchens",
        json=_kitchen_payload(location_id, slug=slug),
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ── CRUD + audit ─────────────────────────────────────────────────────────

async def test_create_kitchen(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    stub_tennetctl.audit_calls.clear()

    r = await client.post(
        "/v1/somaerp/geography/kitchens",
        json=_kitchen_payload(loc["id"]),
        headers=auth_headers_a,
    )
    assert r.status_code == 201, r.text
    kitchen = r.json()["data"]
    assert kitchen["name"] == "KPHB Home Kitchen"
    assert kitchen["kitchen_type"] == "home"
    assert kitchen["status"] == "active"
    assert kitchen["location_id"] == loc["id"]

    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.kitchens.created"
    )


async def test_list_kitchens_tenant_scoped(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    loc_a = await _create_location(client, auth_headers_a)
    loc_b = await _create_location(client, auth_headers_b)
    await _create_kitchen(client, auth_headers_a, location_id=loc_a["id"])
    await _create_kitchen(
        client, auth_headers_b, location_id=loc_b["id"], slug="bom-home",
    )

    r_a = await client.get(
        "/v1/somaerp/geography/kitchens", headers=auth_headers_a,
    )
    assert r_a.status_code == 200
    data_a = r_a.json()["data"]
    assert len(data_a) == 1
    assert data_a[0]["location_id"] == loc_a["id"]


async def test_get_kitchen_cross_tenant_404(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    loc_b = await _create_location(client, auth_headers_b)
    kitchen = await _create_kitchen(
        client, auth_headers_b, location_id=loc_b["id"], slug="bom-home",
    )
    r = await client.get(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


async def test_soft_delete_kitchen(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    stub_tennetctl.audit_calls.clear()
    r = await client.delete(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 204
    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.kitchens.deleted"
    )


# ── State machine ─────────────────────────────────────────────────────────

async def test_status_state_machine_active_to_paused_ok(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "paused"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["status"] == "paused"


async def test_status_state_machine_paused_to_active_ok(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "paused"},
        headers=auth_headers_a,
    )
    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "active"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["status"] == "active"


async def test_status_state_machine_active_to_decommissioned_ok(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "decommissioned"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["status"] == "decommissioned"


async def test_status_state_machine_decommissioned_to_active_raises_422(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "decommissioned"},
        headers=auth_headers_a,
    )
    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "active"},
        headers=auth_headers_a,
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "ILLEGAL_STATUS_TRANSITION"


# ── Audit key routing ────────────────────────────────────────────────────

async def test_patch_status_emits_status_changed_not_updated(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    stub_tennetctl.audit_calls.clear()

    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "paused"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200

    last = stub_tennetctl.audit_calls[-1]
    assert last["event_key"] == "somaerp.geography.kitchens.status_changed"
    # .updated must NOT fire for a pure status change.
    assert all(
        c["event_key"] != "somaerp.geography.kitchens.updated"
        for c in stub_tennetctl.audit_calls
    )


async def test_patch_name_emits_updated_not_status_changed(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    stub_tennetctl.audit_calls.clear()

    r = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"name": "KPHB Home v2"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200

    last = stub_tennetctl.audit_calls[-1]
    assert last["event_key"] == "somaerp.geography.kitchens.updated"


# ── FK / validation ─────────────────────────────────────────────────────

async def test_create_kitchen_with_bogus_location_returns_422(
    client: AsyncClient, auth_headers_a: dict, make_uuid,
) -> None:
    bogus_location_id = make_uuid()
    r = await client.post(
        "/v1/somaerp/geography/kitchens",
        json=_kitchen_payload(bogus_location_id),
        headers=auth_headers_a,
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "INVALID_LOCATION"


async def test_list_kitchens_filter_by_status(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    k1 = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"], slug="kitchen-1",
    )
    await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"], slug="kitchen-2",
    )
    await client.patch(
        f"/v1/somaerp/geography/kitchens/{k1['id']}",
        json={"status": "paused"},
        headers=auth_headers_a,
    )

    r = await client.get(
        "/v1/somaerp/geography/kitchens?status=active",
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["slug"] == "kitchen-2"
