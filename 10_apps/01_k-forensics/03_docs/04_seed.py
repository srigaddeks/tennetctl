#!/usr/bin/env python3
"""K-Forensics idempotent seeder for tennetctl.

Usage:
  python 03_docs/04_seed.py \\
    --api-url http://localhost:58000 \\
    --admin-username admin \\
    --admin-password ChangeMe123! \\
    [--org-code default]

Requires Python 3.11+. No third-party deps — stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SEED_DIR = Path(__file__).parent / "03_seed"

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _req(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict]:
    """Execute an HTTP request and return (status_code, parsed_json).

    Raises SystemExit on non-2xx, non-409 responses.
    """
    data = json.dumps(body).encode() if body is not None else None
    headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw.decode(errors="replace")}
        if exc.code == 409:
            return 409, payload
        print(f"\nERROR: {method} {url} => HTTP {exc.code}")
        print(f"  Response: {json.dumps(payload, indent=2)}")
        sys.exit(1)


def get(url: str, token: str) -> dict:
    _, data = _req("GET", url, token=token)
    return data


def post(url: str, token: str, body: dict) -> tuple[int, dict]:
    return _req("POST", url, token=token, body=body)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def login(api_url: str, username: str, password: str) -> str:
    print(f"[auth] Logging in as {username} ...")
    status, resp = _req("POST", f"{api_url}/v1/sessions", body={"username": username, "password": password})
    if status not in (200, 201):
        print(f"ERROR: Login failed (HTTP {status}): {resp}")
        sys.exit(1)
    token = resp.get("data", {}).get("access_token") or resp.get("access_token")
    if not token:
        print(f"ERROR: No access_token in login response: {resp}")
        sys.exit(1)
    print(f"[auth] OK — token obtained")
    return token


# ---------------------------------------------------------------------------
# Org resolution
# ---------------------------------------------------------------------------


def resolve_org_id(api_url: str, token: str, org_code: str | None) -> str:
    print(f"[orgs] Resolving org (code={org_code or 'first'}) ...")
    resp = get(f"{api_url}/v1/orgs?limit=50", token)
    items = resp.get("data", {}).get("items") or resp.get("items") or []
    if not items:
        print("ERROR: No orgs found. Run tennetctl setup wizard first.")
        sys.exit(1)
    if org_code:
        for org in items:
            if org.get("code") == org_code:
                print(f"[orgs] Found org '{org_code}' => {org['id']}")
                return org["id"]
        print(f"ERROR: No org with code '{org_code}'. Available: {[o.get('code') for o in items]}")
        sys.exit(1)
    org = items[0]
    print(f"[orgs] Using first org: code={org.get('code')} id={org['id']}")
    return org["id"]


# ---------------------------------------------------------------------------
# Category cache
# ---------------------------------------------------------------------------

_category_cache: dict[str, dict[str, int]] = {}


def get_category_id(api_url: str, token: str, category_type: str, category_code: str) -> int:
    """Return the integer ID for a category_type + code pair.

    GET /v1/categories?category_type=<type> returns items with {id, code, ...}.
    Results are cached per category_type.
    """
    if category_type not in _category_cache:
        resp = get(f"{api_url}/v1/categories?category_type={urllib.parse.quote(category_type)}", token)
        items = resp.get("data", {}).get("items") or resp.get("items") or []
        _category_cache[category_type] = {item["code"]: item["id"] for item in items}

    mapping = _category_cache[category_type]
    if category_code not in mapping:
        print(f"ERROR: category_type='{category_type}' code='{category_code}' not found.")
        print(f"  Available codes: {list(mapping.keys())}")
        sys.exit(1)
    return mapping[category_code]


# ---------------------------------------------------------------------------
# Summary tracking
# ---------------------------------------------------------------------------

_summary: list[tuple[str, str, str]] = []


def _record(entity: str, key: str, outcome: str) -> None:
    _summary.append((entity, key, outcome))
    marker = "+" if outcome == "CREATED" else ("~" if outcome == "EXISTS" else outcome)
    print(f"  [{marker}] {entity:12s} {key}")


# ---------------------------------------------------------------------------
# Step 1 — Upsert application
# ---------------------------------------------------------------------------


def upsert_application(api_url: str, token: str) -> str:
    """Create the k-forensics application. Returns its ID."""
    print("\n[application] Upserting k-forensics application ...")
    spec = json.loads((SEED_DIR / "01_application.json").read_text())

    # Check existence
    resp = get(f"{api_url}/v1/applications?limit=200", token)
    items = resp.get("data", {}).get("items") or resp.get("items") or []
    for item in items:
        if item.get("code") == spec["code"]:
            _record("application", spec["code"], "EXISTS")
            return item["id"]

    # Create
    category_id = get_category_id(api_url, token, "application", spec.pop("category_code"))
    spec["category_id"] = category_id

    status, resp = post(f"{api_url}/v1/applications", token, spec)
    if status == 409:
        # Race: fetch again
        resp2 = get(f"{api_url}/v1/applications?limit=200", token)
        items2 = resp2.get("data", {}).get("items") or resp2.get("items") or []
        for item in items2:
            if item.get("code") == "k-forensics":
                _record("application", "k-forensics", "EXISTS")
                return item["id"]
    app_id = (resp.get("data") or resp).get("id")
    if not app_id:
        print(f"[error] Application create returned no id. Response: {resp}", flush=True)
        raise SystemExit(1)
    _record("application", "k-forensics", "CREATED")
    return str(app_id)


# ---------------------------------------------------------------------------
# Step 2 — Upsert products
# ---------------------------------------------------------------------------


def upsert_products(api_url: str, token: str) -> dict[str, str]:
    """Create products. Returns {code: id} map."""
    print("\n[products] Upserting products ...")
    specs = json.loads((SEED_DIR / "02_products.json").read_text())

    resp = get(f"{api_url}/v1/products?limit=200", token)
    existing_items = resp.get("data", {}).get("items") or resp.get("items") or []
    existing = {item["code"]: item["id"] for item in existing_items}

    product_ids: dict[str, str] = {}
    for spec in specs:
        code = spec["code"]
        if code in existing:
            _record("product", code, "EXISTS")
            product_ids[code] = existing[code]
            continue

        category_id = get_category_id(api_url, token, "product", spec.pop("category_code"))
        spec["category_id"] = category_id

        status, resp2 = post(f"{api_url}/v1/products", token, spec)
        if status == 409:
            # Re-fetch
            resp3 = get(f"{api_url}/v1/products?limit=200", token)
            items3 = resp3.get("data", {}).get("items") or resp3.get("items") or []
            for item in items3:
                if item.get("code") == code:
                    product_ids[code] = item["id"]
                    _record("product", code, "EXISTS")
                    break
        else:
            pid = (resp2.get("data") or resp2).get("id")
            if not pid:
                print(f"[error] Product create for '{code}' returned no id. Response: {resp2}", flush=True)
                raise SystemExit(1)
            product_ids[code] = str(pid)
            _record("product", code, "CREATED")

    return product_ids


# ---------------------------------------------------------------------------
# Step 3 — Upsert permissions
# ---------------------------------------------------------------------------

PERMISSIONS_DEFS = [
    ("cases",    "read",    "Read cases and investigations"),
    ("cases",    "create",  "Create new cases"),
    ("cases",    "update",  "Update case details"),
    ("cases",    "delete",  "Delete or archive cases"),
    ("evidence", "read",    "Read evidence items"),
    ("evidence", "upload",  "Upload evidence files"),
    ("evidence", "delete",  "Delete evidence items"),
    ("reports",  "read",    "Read investigation reports"),
    ("reports",  "create",  "Generate investigation reports"),
]


def upsert_permissions(api_url: str, token: str) -> dict[str, str]:
    """Attempt to create permissions via API. Returns {resource:action: id} map.

    The permissions endpoint is read-only (GET /v1/permissions only — no POST).
    We fetch the catalog and map existing permissions. Any that are missing cannot
    be created via API — the operator must run the SQL fallback.
    """
    print("\n[permissions] Resolving permissions catalog ...")

    resp = get(f"{api_url}/v1/permissions", token)
    items = resp.get("data", {}).get("items") or resp.get("items") or []
    perm_map: dict[str, str] = {}
    for item in items:
        key = f"{item['resource']}:{item['action']}"
        perm_map[key] = item["id"]

    missing: list[tuple[str, str]] = []
    for resource, action, _ in PERMISSIONS_DEFS:
        key = f"{resource}:{action}"
        if key in perm_map:
            _record("permission", key, "EXISTS")
        else:
            missing.append((resource, action))

    if missing:
        print(
            f"\n  WARNING: {len(missing)} permission(s) not found in catalog.\n"
            f"  The permissions catalog has no POST endpoint — seed them via SQL:\n"
            f"\n    psql $DATABASE_URL -f 03_seed/00_permissions.sql\n"
            f"\n  Missing: {[f'{r}:{a}' for r, a in missing]}\n"
            f"  Then re-run this seeder.\n"
        )
        # Don't exit — continue with what we have; role-permission grants will
        # be skipped for any missing permissions.

    return perm_map


# ---------------------------------------------------------------------------
# Step 4 — Upsert org roles
# ---------------------------------------------------------------------------


def upsert_roles(api_url: str, token: str, org_id: str) -> dict[str, str]:
    """Create org-tier roles. Returns {code: id} map."""
    print("\n[roles] Upserting org roles ...")
    specs = json.loads((SEED_DIR / "05_roles.json").read_text())

    resp = get(f"{api_url}/v1/orgs/{org_id}/roles", token)
    existing_items = resp.get("data", {}).get("items") or resp.get("items") or []
    existing = {item["code"]: item["id"] for item in existing_items}

    role_ids: dict[str, str] = {}
    for spec in specs:
        code = spec["code"]
        if code in existing:
            _record("role", code, "EXISTS")
            role_ids[code] = existing[code]
            continue

        payload: dict[str, Any] = {
            "code": spec["code"],
            "name": spec["name"],
            "category_code": spec["category_code"],
            "description": spec.get("description", ""),
            "is_system": False,
        }

        status, resp2 = post(f"{api_url}/v1/orgs/{org_id}/roles", token, payload)
        if status == 409:
            resp3 = get(f"{api_url}/v1/orgs/{org_id}/roles", token)
            items3 = resp3.get("data", {}).get("items") or resp3.get("items") or []
            for item in items3:
                if item.get("code") == code:
                    role_ids[code] = item["id"]
                    _record("role", code, "EXISTS")
                    break
        else:
            rid = (resp2.get("data") or resp2).get("id")
            if not rid:
                print(f"[error] Role create for '{code}' returned no id. Response: {resp2}", flush=True)
                raise SystemExit(1)
            role_ids[code] = str(rid)
            _record("role", code, "CREATED")

    return role_ids


# ---------------------------------------------------------------------------
# Step 5 — Upsert groups
# ---------------------------------------------------------------------------


def _slugify(code: str) -> str:
    return code.replace("_", "-").lower()


def upsert_groups(api_url: str, token: str, org_id: str) -> dict[str, str]:
    """Create org-scoped groups. Returns {code: id} map."""
    print("\n[groups] Upserting groups ...")
    specs = json.loads((SEED_DIR / "06_groups.json").read_text())

    resp = get(f"{api_url}/v1/groups?org_id={org_id}&limit=200", token)
    existing_items = resp.get("data", {}).get("items") or resp.get("items") or []
    # Groups may not have a 'code' field in the API — match by slug or name
    existing_by_slug = {item.get("slug", ""): item["id"] for item in existing_items}
    existing_by_name = {item.get("name", ""): item["id"] for item in existing_items}

    group_ids: dict[str, str] = {}
    for spec in specs:
        code = spec["code"]
        slug = _slugify(code)
        name = spec["name"]

        if slug in existing_by_slug:
            _record("group", code, "EXISTS")
            group_ids[code] = existing_by_slug[slug]
            continue
        if name in existing_by_name:
            _record("group", code, "EXISTS")
            group_ids[code] = existing_by_name[name]
            continue

        payload: dict[str, Any] = {
            "name": name,
            "slug": slug,
            "org_id": org_id,
            "description": spec.get("description", ""),
        }

        status, resp2 = post(f"{api_url}/v1/groups", token, payload)
        if status == 409:
            resp3 = get(f"{api_url}/v1/groups?org_id={org_id}&limit=200", token)
            items3 = resp3.get("data", {}).get("items") or resp3.get("items") or []
            for item in items3:
                if item.get("slug") == slug or item.get("name") == name:
                    group_ids[code] = item["id"]
                    _record("group", code, "EXISTS")
                    break
        else:
            gid = (resp2.get("data") or resp2).get("id")
            if not gid:
                print(f"[error] Group create for '{code}' returned no id. Response: {resp2}", flush=True)
                raise SystemExit(1)
            group_ids[code] = str(gid)
            _record("group", code, "CREATED")

    return group_ids


# ---------------------------------------------------------------------------
# Step 6 — Grant role permissions
# ---------------------------------------------------------------------------


def grant_role_permissions(
    api_url: str,
    token: str,
    org_id: str,
    role_ids: dict[str, str],
    perm_map: dict[str, str],
) -> None:
    """Grant permissions to roles per 07_role_permissions.json."""
    print("\n[role-perms] Granting role permissions ...")
    specs = json.loads((SEED_DIR / "07_role_permissions.json").read_text())

    for entry in specs:
        role_code = entry["role_code"]
        role_id = role_ids.get(role_code)
        if not role_id:
            print(f"  SKIP: role '{role_code}' not found (not seeded).")
            continue

        # Fetch current grants for this role
        resp = get(f"{api_url}/v1/orgs/{org_id}/roles/{role_id}/permissions", token)
        existing_grants = resp.get("data", {}).get("items") or resp.get("items") or []
        existing_perm_ids = {item.get("permission_id") or item.get("id") for item in existing_grants}

        for perm in entry["permissions"]:
            key = f"{perm['resource']}:{perm['action']}"
            perm_id = perm_map.get(key)
            if not perm_id:
                print(f"  SKIP grant {role_code} -> {key}: permission not in catalog.")
                continue
            if perm_id in existing_perm_ids:
                _record("role-perm", f"{role_code} -> {key}", "EXISTS")
                continue

            status, _ = post(
                f"{api_url}/v1/orgs/{org_id}/roles/{role_id}/permissions",
                token,
                {"permission_id": perm_id},
            )
            if status == 409:
                _record("role-perm", f"{role_code} -> {key}", "EXISTS")
            else:
                _record("role-perm", f"{role_code} -> {key}", "CREATED")


# ---------------------------------------------------------------------------
# Step 7 — Link application to products
# ---------------------------------------------------------------------------


def link_application_products(
    api_url: str,
    token: str,
    app_id: str,
    product_ids: dict[str, str],
) -> None:
    """Link products to the k-forensics application."""
    print("\n[app-products] Linking products to application ...")
    specs = json.loads((SEED_DIR / "08_application_products.json").read_text())

    resp = get(f"{api_url}/v1/applications/{app_id}/products?limit=200", token)
    existing_items = resp.get("data", {}).get("items") or resp.get("items") or []
    existing_product_ids = {item.get("product_id") or item.get("id") for item in existing_items}

    for link in specs:
        product_code = link["product_code"]
        product_id = product_ids.get(product_code)
        if not product_id:
            print(f"  SKIP: product '{product_code}' not found (not seeded).")
            continue

        if product_id in existing_product_ids:
            _record("app-product", f"k-forensics -> {product_code}", "EXISTS")
            continue

        status, _ = post(
            f"{api_url}/v1/applications/{app_id}/products",
            token,
            {"product_id": product_id},
        )
        if status == 409:
            _record("app-product", f"k-forensics -> {product_code}", "EXISTS")
        else:
            _record("app-product", f"k-forensics -> {product_code}", "CREATED")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def print_summary() -> None:
    print("\n" + "=" * 60)
    print("=== Seed Summary ===")
    print("=" * 60)
    col_w = max(len(e) for e, _, _ in _summary) + 2 if _summary else 12
    key_w = max(len(k) for _, k, _ in _summary) + 2 if _summary else 30
    for entity, key, outcome in _summary:
        print(f"  {entity:<{col_w}} {key:<{key_w}} {outcome}")
    created = sum(1 for _, _, o in _summary if o == "CREATED")
    skipped = sum(1 for _, _, o in _summary if o == "EXISTS")
    print(f"\n  Total: {created} created, {skipped} already existed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="K-Forensics tennetctl seeder")
    parser.add_argument("--api-url", default="http://localhost:58000", help="tennetctl API base URL")
    parser.add_argument("--admin-username", default="admin", help="Admin username")
    parser.add_argument("--admin-password", required=True, help="Admin password")
    parser.add_argument("--org-code", default=None, help="Org code to seed into (default: first org)")
    args = parser.parse_args()

    api = args.api_url.rstrip("/")

    # 1. Auth
    token = login(api, args.admin_username, args.admin_password)

    # 2. Org
    org_id = resolve_org_id(api, token, args.org_code)

    # 3. Application
    app_id = upsert_application(api, token)

    # 4. Products
    product_ids = upsert_products(api, token)

    # 5. Permissions (read-only catalog — warns if missing, prints SQL fallback)
    perm_map = upsert_permissions(api, token)

    # 6. Roles
    role_ids = upsert_roles(api, token, org_id)

    # 7. Groups
    upsert_groups(api, token, org_id)

    # 8. Role-permission grants
    grant_role_permissions(api, token, org_id, role_ids, perm_map)

    # 9. Link app to products
    link_application_products(api, token, app_id, product_ids)

    print_summary()

    print(
        "\nNext step: issue an application token in the tennetctl UI.\n"
        "  IAM -> Applications -> k-forensics -> Tokens tab -> Issue Token\n"
        "  Copy the raw token and paste into 06_frontend/.env.local as:\n"
        "    NEXT_PUBLIC_APPLICATION_TOKEN=<token>\n"
    )


if __name__ == "__main__":
    main()
