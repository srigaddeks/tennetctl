"""Real-Postgres tests for /v1/somaerp/geography/locations + /regions.

Exercises create/list/get/update/soft-delete plus tenant isolation, audit
emission, and unique-slug-per-tenant semantics (slug reusable after
soft-delete).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


# ── Regions (read-only, no tenant scoping required by endpoint) ──────────

async def test_list_regions_returns_seeded(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    r = await client.get(
        "/v1/somaerp/geography/regions", headers=auth_headers_a,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    regions = body["data"]
    assert isinstance(regions, list)
    codes = [row["code"] for row in regions]
    assert "IN-TG" in codes
    in_tg = next(r for r in regions if r["code"] == "IN-TG")
    assert in_tg["country_code"] == "IN"
    assert in_tg["state_name"] == "Telangana"
    assert in_tg["regulatory_body"] == "FSSAI"
    assert in_tg["default_currency_code"] == "INR"
    assert in_tg["default_timezone"] == "Asia/Kolkata"


# ── Helpers ──────────────────────────────────────────────────────────────

def _loc_payload(slug: str = "hyderabad", name: str = "Hyderabad") -> dict:
    return {
        "region_id": 1,
        "name": name,
        "slug": slug,
        "timezone": "Asia/Kolkata",
        "properties": {"pilot": True},
    }


async def _create_location(
    client: AsyncClient, headers: dict, *, slug: str = "hyderabad",
) -> dict:
    r = await client.post(
        "/v1/somaerp/geography/locations",
        json=_loc_payload(slug=slug),
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]


# ── CRUD + audit ─────────────────────────────────────────────────────────

async def test_create_location(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    r = await client.post(
        "/v1/somaerp/geography/locations",
        json=_loc_payload(),
        headers=auth_headers_a,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ok"] is True
    loc = body["data"]
    assert loc["name"] == "Hyderabad"
    assert loc["slug"] == "hyderabad"
    assert loc["region_id"] == 1
    assert loc["region_code"] == "IN-TG"
    assert loc["timezone"] == "Asia/Kolkata"
    # Audit emitted with the right key + tenant scope.
    assert len(stub_tennetctl.audit_calls) == 1
    call = stub_tennetctl.audit_calls[-1]
    assert call["event_key"] == "somaerp.geography.locations.created"
    assert call["scope"]["workspace_id"] == auth_headers_a["X-Test-Workspace-Id"]
    assert call["scope"]["user_id"] == auth_headers_a["X-Test-User-Id"]


async def test_list_locations_for_tenant_a_excludes_tenant_b_data(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    await _create_location(client, auth_headers_a, slug="hyderabad")
    await _create_location(client, auth_headers_b, slug="mumbai")

    # Tenant A sees only its row.
    r_a = await client.get(
        "/v1/somaerp/geography/locations", headers=auth_headers_a,
    )
    assert r_a.status_code == 200, r_a.text
    data_a = r_a.json()["data"]
    assert len(data_a) == 1
    assert data_a[0]["slug"] == "hyderabad"

    # Tenant B sees only its row.
    r_b = await client.get(
        "/v1/somaerp/geography/locations", headers=auth_headers_b,
    )
    assert r_b.status_code == 200, r_b.text
    data_b = r_b.json()["data"]
    assert len(data_b) == 1
    assert data_b[0]["slug"] == "mumbai"


async def test_get_location_cross_tenant_returns_404(
    client: AsyncClient, auth_headers_a: dict, auth_headers_b: dict,
) -> None:
    loc = await _create_location(client, auth_headers_b, slug="mumbai")
    r = await client.get(
        f"/v1/somaerp/geography/locations/{loc['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 404, r.text
    body = r.json()
    assert body["ok"] is False
    # No-leak rule: 404 not 403.
    assert body["error"]["code"] == "NOT_FOUND"


async def test_update_location_emits_updated_audit(
    client: AsyncClient, auth_headers_a: dict, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    # Clear create audit for a cleaner tail check.
    stub_tennetctl.audit_calls.clear()

    r = await client.patch(
        f"/v1/somaerp/geography/locations/{loc['id']}",
        json={"name": "Hyderabad (KPHB)"},
        headers=auth_headers_a,
    )
    assert r.status_code == 200, r.text
    updated = r.json()["data"]
    assert updated["name"] == "Hyderabad (KPHB)"

    assert len(stub_tennetctl.audit_calls) == 1
    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.locations.updated"
    )


async def test_soft_delete_location_returns_204_and_sets_deleted_at(
    client: AsyncClient, auth_headers_a: dict, test_pool, stub_tennetctl,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    stub_tennetctl.audit_calls.clear()

    r = await client.delete(
        f"/v1/somaerp/geography/locations/{loc['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 204, r.text

    # Verify deleted_at is set in the DB.
    async with test_pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT deleted_at FROM "11_somaerp".fct_locations WHERE id = $1',
            loc["id"],
        )
    assert row is not None
    assert row["deleted_at"] is not None

    assert (
        stub_tennetctl.audit_calls[-1]["event_key"]
        == "somaerp.geography.locations.deleted"
    )


async def test_list_excludes_soft_deleted_by_default(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    await client.delete(
        f"/v1/somaerp/geography/locations/{loc['id']}",
        headers=auth_headers_a,
    )

    r = await client.get(
        "/v1/somaerp/geography/locations", headers=auth_headers_a,
    )
    assert r.status_code == 200
    assert r.json()["data"] == []

    # include_deleted=true surfaces the row again.
    r_all = await client.get(
        "/v1/somaerp/geography/locations?include_deleted=true",
        headers=auth_headers_a,
    )
    assert r_all.status_code == 200
    data = r_all.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == loc["id"]
    assert data[0]["deleted_at"] is not None


async def test_unique_slug_reusable_after_soft_delete(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    first = await _create_location(client, auth_headers_a, slug="hyderabad")

    # Creating a second "hyderabad" while the first is active fails.
    r_dup = await client.post(
        "/v1/somaerp/geography/locations",
        json=_loc_payload(slug="hyderabad"),
        headers=auth_headers_a,
    )
    assert r_dup.status_code >= 400

    # Soft-delete the first.
    r_del = await client.delete(
        f"/v1/somaerp/geography/locations/{first['id']}",
        headers=auth_headers_a,
    )
    assert r_del.status_code == 204

    # Now the slug can be reused for a fresh row.
    r_reuse = await client.post(
        "/v1/somaerp/geography/locations",
        json=_loc_payload(slug="hyderabad", name="Hyderabad Reborn"),
        headers=auth_headers_a,
    )
    assert r_reuse.status_code == 201, r_reuse.text
    assert r_reuse.json()["data"]["slug"] == "hyderabad"
    assert r_reuse.json()["data"]["name"] == "Hyderabad Reborn"


async def test_get_location_returns_envelope(
    client: AsyncClient, auth_headers_a: dict,
) -> None:
    loc = await _create_location(client, auth_headers_a)
    r = await client.get(
        f"/v1/somaerp/geography/locations/{loc['id']}",
        headers=auth_headers_a,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["id"] == loc["id"]
    assert body["data"]["region_code"] == "IN-TG"
