"""Shared fixtures for somaerp real-DB pytest suite (Plan 56-03 Task 3).

Strategy
--------
One session-scoped asyncpg Pool wired to `tennetctl_test` on port 5434. The
bootstrap migration (`00_bootstrap/..._001_create-somaerp-schema.sql`) and
the geography migration (`10_locations/..._002_create-locations-kitchens-zones.sql`)
are applied at session start after dropping any prior `"11_somaerp"` schema
to guarantee a clean slate. The IN-TG region is hardcoded-inserted so tests
don't need the tennetctl YAML seeder.

Per-test cleanup truncates the three geography fct_* tables (but keeps
dim_regions seeded). The FastAPI app is built without its real lifespan
(no live tennetctl, no live asyncpg pool creation in lifespan) — instead
app.state is populated manually from fixtures, matching the pattern in
test_health.py.

Auth is resolved by `SessionProxyMiddleware` which normally calls a live
tennetctl `/v1/auth/me`. For tests we REPLACE that middleware with a
lightweight `_TestAuthMiddleware` that reads request headers
`X-Test-Workspace-Id`, `X-Test-User-Id`, `X-Test-Session-Id`, `X-Test-Org-Id`
and binds them to `request.state`. This keeps the real middleware contract
(request.state carries the 4-tuple) without talking to tennetctl.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from importlib import import_module
from pathlib import Path
from typing import Any, AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Repo-root on sys.path so `apps.somaerp.backend.*` imports resolve ────
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Config env (must be set before load_config).
os.environ.setdefault("SOMAERP_PG_PASS", "tennetctl_dev")
os.environ.setdefault("TENNETCTL_SERVICE_API_KEY", "test-service-key")
os.environ.setdefault(
    "SOMAERP_PG_DB", os.environ.get("TENNETCTL_TEST_PG_DB", "tennetctl_test"),
)


# ── Paths to the migration files we apply at session start ───────────────

_SOMAERP_DOCS = _REPO_ROOT / "apps/somaerp/03_docs/features/11_somaerp/05_sub_features"
_BOOTSTRAP_MIGRATIONS_DIRS = [
    _SOMAERP_DOCS / "00_bootstrap/09_sql_migrations/01_migrated",
    _SOMAERP_DOCS / "00_bootstrap/09_sql_migrations/02_in_progress",
]
_GEOGRAPHY_MIGRATIONS_DIRS = [
    _SOMAERP_DOCS / "10_locations/09_sql_migrations/01_migrated",
    _SOMAERP_DOCS / "10_locations/09_sql_migrations/02_in_progress",
]


def _glob_migrations(dirs: list[Path]) -> list[Path]:
    out: list[Path] = []
    for d in dirs:
        if d.exists():
            out.extend(d.glob("*.sql"))
    return sorted(out, key=lambda p: p.name)


def _test_dsn() -> str:
    host = os.getenv("TENNETCTL_TEST_PG_HOST", "localhost")
    port = os.getenv("TENNETCTL_TEST_PG_PORT", "5434")
    user = os.getenv("TENNETCTL_TEST_PG_USER", "tennetctl")
    pw = os.getenv("TENNETCTL_TEST_PG_PASS", "tennetctl_dev")
    db = os.getenv("TENNETCTL_TEST_PG_DB", "tennetctl_test")
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"


async def _db_reachable() -> bool:
    try:
        conn = await asyncpg.connect(_test_dsn(), timeout=2.0)
        await conn.close()
        return True
    except Exception:
        return False


def _extract_up(sql: str) -> str:
    """Return everything between '-- UP' and '-- DOWN'. If no markers, return
    the full text."""
    up_idx = sql.find("-- UP")
    down_idx = sql.find("-- DOWN")
    if up_idx == -1:
        return sql
    start = sql.find("\n", up_idx) + 1
    end = down_idx if down_idx != -1 else len(sql)
    return sql[start:end]


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog",
    )


# ── Event loop (session scope so session fixtures can share it) ──────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Session-scoped pool + migrations + seed ──────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_pool() -> AsyncIterator[asyncpg.Pool]:
    if not await _db_reachable():
        pytest.skip(
            "Test DB unreachable at "
            f"{_test_dsn()} — set TENNETCTL_TEST_PG_* to override.",
        )

    pool = await asyncpg.create_pool(
        _test_dsn(), min_size=1, max_size=4, init=_init_conn,
    )

    # Drop any prior state to guarantee a clean slate.
    async with pool.acquire() as conn:
        await conn.execute('DROP SCHEMA IF EXISTS "11_somaerp" CASCADE')

        # Apply bootstrap migration (creates the schema).
        for mig in _glob_migrations(_BOOTSTRAP_MIGRATIONS_DIRS):
            await conn.execute(_extract_up(mig.read_text()))

        # Apply geography migration (tables + views).
        for mig in _glob_migrations(_GEOGRAPHY_MIGRATIONS_DIRS):
            await conn.execute(_extract_up(mig.read_text()))

        # Seed the IN-TG region directly — matches
        # `10_locations/09_sql_migrations/seeds/11somaerp_dim_regions.yaml`.
        await conn.execute(
            'INSERT INTO "11_somaerp".dim_regions '
            "(id, code, country_code, state_name, regulatory_body, "
            " default_currency_code, default_timezone, deprecated_at) "
            "VALUES (1, 'IN-TG', 'IN', 'Telangana', 'FSSAI', 'INR', "
            "'Asia/Kolkata', NULL) ON CONFLICT (id) DO NOTHING",
        )

    try:
        yield pool
    finally:
        # Final cleanup: drop schema so a follow-up run starts fresh.
        async with pool.acquire() as conn:
            await conn.execute('DROP SCHEMA IF EXISTS "11_somaerp" CASCADE')
        await pool.close()


# ── Per-test cleanup of the geography tables ────────────────────────────

@pytest_asyncio.fixture
async def clean_geography(test_pool: asyncpg.Pool) -> AsyncIterator[None]:
    """Truncate fct_service_zones, fct_kitchens, fct_locations BEFORE each
    test. dim_regions is preserved (idempotent seed)."""
    async with test_pool.acquire() as conn:
        await conn.execute(
            'TRUNCATE TABLE "11_somaerp".fct_service_zones, '
            '"11_somaerp".fct_kitchens, "11_somaerp".fct_locations '
            "RESTART IDENTITY CASCADE",
        )
    yield


# ── Stable identity fixtures ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def tenant_a_id() -> str:
    return "11111111-1111-7111-8111-111111111111"


@pytest.fixture(scope="session")
def tenant_b_id() -> str:
    return "22222222-2222-7222-8222-222222222222"


@pytest.fixture(scope="session")
def actor_user_id() -> str:
    return "33333333-3333-7333-8333-333333333333"


@pytest.fixture(scope="session")
def actor_session_id() -> str:
    return "44444444-4444-7444-8444-444444444444"


@pytest.fixture(scope="session")
def actor_org_id() -> str:
    return "55555555-5555-7555-8555-555555555555"


# ── Stub TennetctlClient that records audit_emit calls ───────────────────

class _StubTennetctlClient:
    """In-process stub matching the real TennetctlClient surface used by
    somaerp routes/services. `audit_emit` records each call so tests can
    assert emission without a network hop."""

    def __init__(self, base_url: str = "http://localhost:51734") -> None:
        self._base_url = base_url
        self.audit_calls: list[dict[str, Any]] = []

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def application_id(self) -> str | None:
        return None

    @property
    def org_id(self) -> str | None:
        return None

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def audit_emit(
        self,
        event_key: str,
        scope: dict,
        payload: dict | None = None,
    ) -> None:
        self.audit_calls.append(
            {"event_key": event_key, "scope": dict(scope),
             "payload": dict(payload or {})},
        )

    async def ping(self) -> dict:
        return {"ok": True, "data": {"service": "tennetctl", "status": "healthy"}}

    async def get_me(self, user_session_cookie: str) -> dict:
        return {}


@pytest_asyncio.fixture
async def stub_tennetctl() -> _StubTennetctlClient:
    return _StubTennetctlClient()


# ── Test auth middleware — sets request.state from headers ────────────────

# We build it as a plain ASGI middleware class so it slots into the same
# starlette middleware stack as SessionProxyMiddleware.

from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from fastapi import Request  # noqa: E402


class _TestAuthMiddleware(BaseHTTPMiddleware):
    """Replacement for SessionProxyMiddleware used only during tests.

    Binds the 4-tuple auth scope (workspace_id, user_id, session_id, org_id)
    to request.state from custom X-Test-* headers so tests don't need a
    live tennetctl auth session.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.workspace_id = request.headers.get("X-Test-Workspace-Id")
        request.state.user_id = request.headers.get("X-Test-User-Id")
        request.state.session_id = request.headers.get("X-Test-Session-Id")
        request.state.org_id = request.headers.get("X-Test-Org-Id")
        request.state.auth_token = request.headers.get("X-Test-Auth-Token")
        return await call_next(request)


# ── Function-scoped client (no lifespan) ─────────────────────────────────

@pytest_asyncio.fixture
async def client(
    test_pool: asyncpg.Pool,
    stub_tennetctl: _StubTennetctlClient,
    clean_geography: None,
) -> AsyncIterator[AsyncClient]:
    """Build the somaerp FastAPI app with test-injected state.

    The real lifespan is bypassed by using httpx.ASGITransport which runs
    only the HTTP scope; we populate `app.state` ourselves.
    """
    _main = import_module("apps.somaerp.backend.main")
    _config_mod = import_module("apps.somaerp.backend.01_core.config")

    app = _main.create_app()
    cfg = _config_mod.load_config()
    app.state.config = cfg
    app.state.pool = test_pool
    app.state.tennetctl = stub_tennetctl

    # Swap SessionProxyMiddleware for our test middleware. FastAPI/starlette
    # only exposes the user_middleware list; we replace the class reference
    # there (the middleware stack is built lazily on first request).
    _somaerp_mw = import_module("apps.somaerp.backend.01_core.middleware")
    replaced = False
    new_stack = []
    for mw in app.user_middleware:
        if mw.cls is _somaerp_mw.SessionProxyMiddleware:
            new_stack.append(
                type(mw)(_TestAuthMiddleware, *mw.args, **mw.kwargs)
                if hasattr(mw, "args")
                else mw,
            )
            replaced = True
        else:
            new_stack.append(mw)
    if replaced:
        app.user_middleware = new_stack
    # Force rebuild of the middleware stack on next request.
    app.middleware_stack = None

    # raise_app_exceptions=False so unhandled server exceptions surface as
    # HTTP 500 responses instead of blowing up the test client — matches
    # what a real HTTP caller would see, lets tests assert on status codes
    # rather than catching driver exceptions.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Helper: default auth headers for tenant A ────────────────────────────

@pytest.fixture
def auth_headers_a(
    tenant_a_id: str,
    actor_user_id: str,
    actor_session_id: str,
    actor_org_id: str,
) -> dict[str, str]:
    return {
        "X-Test-Workspace-Id": tenant_a_id,
        "X-Test-User-Id": actor_user_id,
        "X-Test-Session-Id": actor_session_id,
        "X-Test-Org-Id": actor_org_id,
    }


@pytest.fixture
def auth_headers_b(
    tenant_b_id: str,
    actor_user_id: str,
    actor_session_id: str,
    actor_org_id: str,
) -> dict[str, str]:
    return {
        "X-Test-Workspace-Id": tenant_b_id,
        "X-Test-User-Id": actor_user_id,
        "X-Test-Session-Id": actor_session_id,
        "X-Test-Org-Id": actor_org_id,
    }


# ── Helpers for test data construction ───────────────────────────────────

def _uuid7() -> str:
    """Local uuid7 so helpers don't need repo imports inside tests."""
    _id = import_module("apps.somaerp.backend.01_core.id")
    return _id.uuid7()


@pytest.fixture
def make_uuid():
    return _uuid7
