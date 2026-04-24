"""Real-Postgres tests for /v1/somaerp/geography/service-zones.

Covers CRUD + the cross-layer "active-kitchen required" guard on create
(decommissioned kitchen -> 409 KITCHEN_NOT_ACTIVE; bogus kitchen -> 422
INVALID_KITCHEN) + audit emission.
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


async def _create_kitchen(
    client: AsyncClient, headers: dict, *, location_id: str,
    slug: str = "kphb-home",
) -> dict:
    r = await client.post(
        "/v1/somaerp/geography/kitchens",
        json={
            "location_id": location_id,
            "name": "KPHB Home Kitchen",
            "slug": slug,
            "kitchen_type": "home",
            "address_jsonb": {},
            "status": "active",
            "properties": {},
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


def _zone_payload(kitchen_id: str, name: str = "KPHB Cluster 1") -> dict:
    return {
        "kitchen_id": kitchen_id,
        "name": name,
        "polygon_jsonb": {"pincodes": ["500072", "500085"]},
        "status": "active",
        "properties": {},
    }


async def _create_zone(
    client: AsyncClient, headers: dict, *, kitchen_id: str,
    name: str = "KPHB Cluster 1",
) -> dict:
    r = await client.post(
        "/v1/somaerp/geography/service-zones",
        json=_zone_payload(kitchen_id, name=name),
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ── CRUD + audit ─────────────────────────────────────────────────────────

async def test_create_service_zone(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    stub_tennetctl.audit_calls.clear()

    r = await client.post(
        "/v1/somaerp/geography/service-zones",
        json=_zone_payload(kitchen["id"]),
        headers=auth_headers_a,
    )
    assert r.status_code == 201, r.text
    zone = r.json()["data"]
    assert zone["kitchen_id"] == kitchen["id"]
    assert zone["name"] == "KPHB Cluster 1"
    assert zone["status"] == "active"

    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.service_zones.created"
    )


async def test_list_service_zones_tenant_scoped(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    loc_a = await _create_location(client, auth_headers_a)
    loc_b = await _create_location(client, auth_headers_b)
    k_a = await _create_kitchen(client, auth_headers_a, location_id=loc_a["id"])
    k_b = await _create_kitchen(
        client, auth_headers_b, location_id=loc_b["id"], slug="bom-home",
    )
    await _create_zone(client, auth_headers_a, kitchen_id=k_a["id"])
    await _create_zone(
        client, auth_headers_b, kitchen_id=k_b["id"], name="BOM Zone",
    )

    r = await client.get(
        "/v1/somaerp/geography/service-zones", headers=auth_headers_a,
    )
    assert r.status_code == 200
    zones = r.json()["data"]
    assert len(zones) == 1
    assert zones[0]["kitchen_id"] == k_a["id"]


async def test_get_zone_cross_tenant_404(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    loc_b = await _create_location(client, auth_headers_b)
    k_b = await _create_kitchen(
        client, auth_headers_b, location_id=loc_b["id"], slug="bom-home",
    )
    zone = await _create_zone(client, auth_headers_b, kitchen_id=k_b["id"])

    r = await client.get(
        f"/v1/somaerp/geography/service-zones/{zone['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


async def test_update_zone_emits_updated_audit(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    k = await _create_kitchen(client, auth_headers_a, location_id=loc["id"])
    zone = await _create_zone(client, auth_headers_a, kitchen_id=k["id"])
    stub_tennetctl.audit_calls.clear()

    r = await client.patch(
        f"/v1/somaerp/geography/service-zones/{zone['id']}",
        json={"name": "KPHB Cluster 1 (v2)"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "KPHB Cluster 1 (v2)"
    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.service_zones.updated"
    )


async def test_soft_delete_zone_returns_204(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    k = await _create_kitchen(client, auth_headers_a, location_id=loc["id"])
    zone = await _create_zone(client, auth_headers_a, kitchen_id=k["id"])
    stub_tennetctl.audit_calls.clear()

    r = await client.delete(
        f"/v1/somaerp/geography/service-zones/{zone['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 204
    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.service_zones.deleted"
    )


# ── Active-kitchen guard ─────────────────────────────────────────────────

async def test_zone_creation_on_decommissioned_kitchen_returns_409(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    kitchen = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"],
    )
    # Decommission the kitchen.
    r_patch = await client.patch(
        f"/v1/somaerp/geography/kitchens/{kitchen['id']}",
        json={"status": "decommissioned"},
        headers=auth_headers_a,
    )
    assert r_patch.status_code == 200

    # Creating a zone now must be rejected with 409 KITCHEN_NOT_ACTIVE.
    r = await client.post(
        "/v1/somaerp/geography/service-zones",
        json=_zone_payload(kitchen["id"]),
        headers=auth_headers_a,
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "KITCHEN_NOT_ACTIVE"


async def test_zone_creation_on_nonexistent_kitchen_returns_422(
    client: AsyncClient, auth_headers_a: dict, make_uuid,
) -> None:
    bogus_kitchen = make_uuid()
    r = await client.post(
        "/v1/somaerp/geography/service-zones",
        json=_zone_payload(bogus_kitchen),
        headers=auth_headers_a,
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "INVALID_KITCHEN"


async def test_zone_filter_by_kitchen_id(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    k1 = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"], slug="kitchen-1",
    )
    k2 = await _create_kitchen(
        client, auth_headers_a, location_id=loc["id"], slug="kitchen-2",
    )
    await _create_zone(client, auth_headers_a, kitchen_id=k1["id"], name="Zone A")
    await _create_zone(client, auth_headers_a, kitchen_id=k2["id"], name="Zone B")

    r = await client.get(
        f"/v1/somaerp/geography/service-zones?kitchen_id={k1['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    zones = r.json()["data"]
    assert len(zones) == 1
    assert zones[0]["name"] == "Zone A"
