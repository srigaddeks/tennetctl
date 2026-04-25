"""Global pytest fixtures — real Postgres, real FastAPI app, no mocks.

Design:
- Session-scoped ``test_db``: drops + recreates ``tennetctl_test``, applies every
  migration (01_migrated + 02_in_progress, ordered by filename) with seed
  interleaving. Runs once per ``pytest`` invocation.
- Session-scoped ``app``: FastAPI app wired to the test DB, going through the
  real lifespan (catalog upsert, vault bootstrap, etc.).
- Function-scoped ``client``: httpx.AsyncClient against the app via ASGI.
- Function-scoped ``admin_session``: calls ``/v1/setup/initial-admin`` once per
  session, then signs in to return ``(user_id, org_id, workspace_id, token)``.

No monkey-patching of services, no mocked DB — every assertion hits Postgres
through the real FastAPI route + service + repository path.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from importlib import import_module
from pathlib import Path
from typing import Any, AsyncIterator

import asyncpg
import httpx
import pytest
import pytest_asyncio
import yaml

ROOT = Path(__file__).resolve().parent.parent
PG_HOST = os.environ.get("TENNETCTL_TEST_PG_HOST", "localhost")
PG_PORT = os.environ.get("TENNETCTL_TEST_PG_PORT", "5434")
PG_USER = os.environ.get("TENNETCTL_TEST_PG_USER", "tennetctl")
PG_PASS = os.environ.get("TENNETCTL_TEST_PG_PASS", "tennetctl_dev")
TEST_DB = os.environ.get("TENNETCTL_TEST_DB", "tennetctl_test")
TEST_DSN = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{TEST_DB}"

UP_MARKER = "-- UP ===="
DOWN_MARKER = "-- DOWN ===="


# ─── asyncio scope ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ─── database setup ────────────────────────────────────────────────────────

def _extract_up(content: str) -> str:
    up_idx = content.find(UP_MARKER)
    if up_idx < 0:
        return content
    # Markers can extend with extra '=' (e.g. '-- UP =================='). Skip
    # past the entire marker line, otherwise the trailing '=' chars get fed
    # to Postgres as SQL.
    after_marker = content[up_idx + len(UP_MARKER):]
    nl = after_marker.find("\n")
    after = after_marker[nl + 1:] if nl >= 0 else after_marker
    down_idx = after.find(DOWN_MARKER)
    return after[:down_idx] if down_idx >= 0 else after


def _discover_migrations() -> list[Path]:
    migrated = list(ROOT.rglob("09_sql_migrations/01_migrated/*.sql"))
    in_progress = list(ROOT.rglob("09_sql_migrations/02_in_progress/*.sql"))
    return sorted(migrated + in_progress, key=lambda p: p.name)


def _discover_seeds() -> list[Path]:
    yaml_files = list(ROOT.rglob("09_sql_migrations/seeds/*.yaml"))
    json_files = list(ROOT.rglob("09_sql_migrations/seeds/*.json"))
    return sorted(yaml_files + json_files, key=lambda p: p.name)


async def _apply_seed(conn: asyncpg.Connection, path: Path) -> None:
    raw = path.read_text()
    doc = yaml.safe_load(raw) if path.suffix == ".yaml" else json.loads(raw)
    if not doc or not doc.get("rows"):
        return
    schema = doc["schema"]
    table = doc["table"]
    rows = doc["rows"]
    cols = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
    sql = (
        f'INSERT INTO "{schema}"."{table}" ({col_list}) '
        f'VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    )
    for row in rows:
        await conn.execute(sql, *[row.get(c) for c in cols])


def _recreate_db() -> None:
    """Drop + create the test DB via psql (can't run DROP DATABASE over asyncpg pool)."""
    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASS
    base_args = ["psql", "-h", PG_HOST, "-p", PG_PORT, "-U", PG_USER, "-d", "postgres", "-v", "ON_ERROR_STOP=1"]
    subprocess.run([*base_args, "-c", f"DROP DATABASE IF EXISTS {TEST_DB}"], env=env, check=True, capture_output=True)
    subprocess.run([*base_args, "-c", f"CREATE DATABASE {TEST_DB}"], env=env, check=True, capture_output=True)


async def _migrate_and_seed() -> None:
    migrations = _discover_migrations()
    seeds = _discover_seeds()
    conn = await asyncpg.connect(TEST_DSN)
    try:
        for f in migrations:
            up = _extract_up(f.read_text()).strip()
            if not up:
                continue
            try:
                await conn.execute(up)
            except Exception as e:
                raise RuntimeError(f"migration {f.name} failed: {e}") from e
            # Seed interleave so later migrations can reference dim rows.
            for s in seeds:
                try:
                    await _apply_seed(conn, s)
                except Exception:
                    pass  # table may not exist yet
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def test_db() -> str:
    """Drop + recreate + migrate + seed the test DB. Returns its DSN."""
    _recreate_db()
    asyncio.new_event_loop().run_until_complete(_migrate_and_seed())
    return TEST_DSN


# ─── FastAPI app + client ──────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def app(test_db: str) -> AsyncIterator[Any]:
    """Boot the real FastAPI app against the test DB via its lifespan.

    Restricts enabled modules to the ones exercised by the suite so that
    monitoring worker pools, notify scheduler, etc. don't race with test
    assertions or spam the DB with writes to partitioned tables. Routes
    for excluded modules are simply not mounted.
    """
    os.environ["DATABASE_URL"] = test_db
    os.environ["TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT"] = "true"
    os.environ["TENNETCTL_DISABLE_AUTH_RATE_LIMIT"] = "1"
    # Mount every module so monitoring/notify routes are reachable. The
    # monitoring workers log noise about partition lookups but don't block
    # tests.
    os.environ.setdefault(
        "TENNETCTL_MODULES",
        "core,iam,audit,vault,notify,featureflags,monitoring",
    )
    _main = import_module("backend.main")
    async with _main.app.router.lifespan_context(_main.app):
        yield _main.app


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    """Async HTTP client bound to the in-process ASGI app."""
    # raise_app_exceptions=False so unhandled server exceptions come back as
    # 500 responses (matching production behaviour) instead of propagating
    # into the test as a bare Python exception.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as ac:
        yield ac


# ─── test helpers ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def pool(app) -> asyncpg.Pool:
    """Direct pool access for tests that want to assert raw DB state."""
    return app.state.pool


async def _ensure_admin(client: httpx.AsyncClient) -> dict:
    """Call /v1/setup/initial-admin once; return the seeded admin payload.

    Safe to call repeatedly — subsequent calls will 409 with ALREADY_INITIALIZED
    and we fall back to /v1/auth/signin.
    """
    email = "pytest-admin@example.com"
    password = "pytest-password-1234"
    resp = await client.post(
        "/v1/setup/initial-admin",
        json={"email": email, "password": password, "display_name": "Pytest Admin"},
    )
    # Debug aid: surface the response body on unexpected status codes.
    if resp.status_code not in (201, 400, 403, 409):
        raise AssertionError(
            f"initial-admin unexpected status {resp.status_code}: {resp.text}"
        )
    if resp.status_code == 201:
        body = resp.json()
        assert body["ok"]
        data = body["data"]
        return {
            "email": email,
            "password": password,
            "user_id": data["user_id"],
            "token": data["session_token"],
            "org_id": data["session"].get("org_id"),
            "workspace_id": data["session"].get("workspace_id"),
        }
    # Already initialized — sign in instead.
    signin = await client.post(
        "/v1/auth/signin",
        json={"email": email, "password": password},
    )
    assert signin.status_code == 200, signin.text
    data = signin.json()["data"]
    return {
        "email": email,
        "password": password,
        "user_id": data["user"]["id"],
        "token": data["token"],
        "org_id": data["session"].get("org_id"),
        "workspace_id": data["session"].get("workspace_id"),
    }


@pytest_asyncio.fixture(scope="session")
async def admin_session(app) -> dict:
    """Seed the initial admin + org + workspace once per session.

    POST /v1/setup/initial-admin only creates the user (not an org). Tests
    that touch org-scoped routes need an org; we create one explicitly here
    and tie the admin's session to it by signing in fresh once the org exists.
    """
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        admin = await _ensure_admin(ac)
        auth = {"Authorization": f"Bearer {admin['token']}"}

        # Ensure an org exists and the admin is a member.
        if not admin.get("org_id"):
            org_resp = await ac.post(
                "/v1/orgs",
                headers=auth,
                json={"slug": "pytest", "display_name": "Pytest Org"},
            )
            assert org_resp.status_code in (200, 201), org_resp.text
            admin["org_id"] = org_resp.json()["data"]["id"]

            # Sign in again so the fresh session carries org_id on
            # request.state — the previous token predates the org.
            signin = await ac.post(
                "/v1/auth/signin",
                json={"email": admin["email"], "password": admin["password"]},
            )
            assert signin.status_code == 200, signin.text
            signin_data = signin.json()["data"]
            admin["token"] = signin_data["token"]
            admin["workspace_id"] = signin_data["session"].get("workspace_id")
            # In single-tenant mode the re-sign-in attaches the user to the
            # "default" org (not the manually created "pytest" org). Keep
            # admin["org_id"] consistent with the workspace's actual org.
            if signin_data["session"].get("org_id"):
                admin["org_id"] = signin_data["session"]["org_id"]
            auth = {"Authorization": f"Bearer {admin['token']}"}

        # Ensure a workspace exists under the admin's org.
        if not admin.get("workspace_id"):
            ws_resp = await ac.post(
                "/v1/workspaces",
                headers=auth,
                json={
                    "org_id": admin["org_id"],
                    "slug": "default",
                    "display_name": "Default",
                },
            )
            assert ws_resp.status_code in (200, 201), ws_resp.text
            admin["workspace_id"] = ws_resp.json()["data"]["id"]
    return admin


@pytest_asyncio.fixture
async def auth_headers(app, admin_session) -> dict:
    """Fresh authorization + x-workspace-id headers for every test.

    We re-sign-in per test because session-scoped tokens can get evicted or
    expire mid-run when other tests create many sessions in rapid succession.
    Every test gets a known-live token.
    """
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        r = await ac.post(
            "/v1/auth/signin",
            json={"email": admin_session["email"], "password": admin_session["password"]},
        )
        assert r.status_code == 200, r.text
        token = r.json()["data"]["token"]
    return {
        "Authorization": f"Bearer {token}",
        "x-workspace-id": admin_session["workspace_id"],
    }
