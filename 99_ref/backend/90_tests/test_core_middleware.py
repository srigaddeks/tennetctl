from __future__ import annotations

from contextlib import nullcontext
from importlib import import_module
from pathlib import Path
from unittest.mock import patch
import unittest

import httpx
from fastapi import FastAPI

application_module = import_module("backend.01_core.application")
rate_limit_module = import_module("backend.01_core.rate_limit")
pagination_module = import_module("backend.01_core.pagination")
settings_module = import_module("backend.00_config.settings")

Settings = settings_module.Settings
SlidingWindowRateLimiter = rate_limit_module.SlidingWindowRateLimiter
RateLimitMiddleware = rate_limit_module.RateLimitMiddleware
SecurityHeadersMiddleware = application_module.SecurityHeadersMiddleware
RequestSizeLimitMiddleware = application_module.RequestSizeLimitMiddleware
PaginationParams = pagination_module.PaginationParams
PaginatedResponse = pagination_module.PaginatedResponse
paginate = pagination_module.paginate
get_pagination_params = pagination_module.get_pagination_params


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        environment="test",
        app_name="kcontrol-test",
        auth_local_core_enabled=True,
        run_migrations_on_startup=False,
        database_url="postgresql://localhost/test",
        database_min_pool_size=1,
        database_max_pool_size=2,
        database_command_timeout_seconds=30,
        access_token_secret="test-secret",
        access_token_algorithm="HS256",
        access_token_issuer="kcontrol-test",
        access_token_audience="kcontrol-test-api",
        access_token_ttl_seconds=900,
        refresh_token_ttl_seconds=86400,
        brute_force_window_seconds=900,
        brute_force_max_attempts=5,
        default_tenant_key="default",
        trust_proxy_headers=False,
        trusted_proxy_depth=1,
        migration_directory=Path("/nonexistent"),
        cors_allowed_origins=("http://localhost:3000",),
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _create_test_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or _make_settings()
    with (
        patch.object(application_module, "start_operation_span", return_value=nullcontext()),
        patch.object(application_module, "configure_observability"),
        patch.object(application_module, "instrument_fastapi_app"),
    ):
        return application_module.create_app(resolved)


# ---------------------------------------------------------------------------
# CORS Tests
# ---------------------------------------------------------------------------

class CORSTests(unittest.IsolatedAsyncioTestCase):
    async def test_cors_preflight_returns_expected_headers(self) -> None:
        app = _create_test_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.options(
                "/livez",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3000")

    async def test_cors_rejects_unlisted_origin(self) -> None:
        app = _create_test_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.options(
                "/livez",
                headers={
                    "Origin": "http://evil.example.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
        # Starlette CORS middleware returns 400 for disallowed origins
        self.assertNotEqual(
            response.headers.get("access-control-allow-origin"),
            "http://evil.example.com",
        )

    async def test_cors_wildcard_allows_any_origin(self) -> None:
        settings = _make_settings(cors_allowed_origins=("*",))
        app = _create_test_app(settings)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/livez",
                headers={"Origin": "http://any-origin.example.com"},
            )
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")

    async def test_no_cors_when_origins_empty(self) -> None:
        settings = _make_settings(cors_allowed_origins=())
        app = _create_test_app(settings)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/livez",
                headers={"Origin": "http://localhost:3000"},
            )
        self.assertIsNone(response.headers.get("access-control-allow-origin"))


# ---------------------------------------------------------------------------
# Rate Limit Tests
# ---------------------------------------------------------------------------

class SlidingWindowRateLimiterTests(unittest.TestCase):
    def test_allows_within_limit(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            allowed, remaining, _ = limiter.is_allowed("client-1")
            self.assertTrue(allowed)
        self.assertEqual(remaining, 0)

    def test_denies_after_limit_exceeded(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("client-1")
        allowed, remaining, reset_after = limiter.is_allowed("client-1")
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(reset_after, 0)

    def test_different_keys_are_independent(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        for _ in range(2):
            limiter.is_allowed("client-a")
        allowed_a, _, _ = limiter.is_allowed("client-a")
        allowed_b, _, _ = limiter.is_allowed("client-b")
        self.assertFalse(allowed_a)
        self.assertTrue(allowed_b)

    def test_cleanup_removes_expired_keys(self) -> None:
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=0)
        limiter.is_allowed("client-1")
        removed = limiter.cleanup()
        self.assertEqual(removed, 1)


class RateLimitMiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit_returns_429_after_exceeding_limit(self) -> None:
        settings = _make_settings(
            rate_limit_enabled=True,
            rate_limit_requests_per_minute=3,
            rate_limit_exclude_paths=(),
            cors_allowed_origins=(),
        )
        app = _create_test_app(settings)

        @app.get("/test-rate")
        async def test_rate():
            return {"ok": True}

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            for _ in range(3):
                resp = await client.get("/test-rate")
                self.assertEqual(resp.status_code, 200)

            resp = await client.get("/test-rate")
            self.assertEqual(resp.status_code, 429)
            data = resp.json()
            self.assertEqual(data["error"]["code"], "rate_limited")
            self.assertIn("retry-after", resp.headers)

    async def test_rate_limit_headers_present_on_responses(self) -> None:
        settings = _make_settings(
            rate_limit_enabled=True,
            rate_limit_requests_per_minute=10,
            rate_limit_exclude_paths=(),
            cors_allowed_origins=(),
        )
        app = _create_test_app(settings)

        @app.get("/test-headers")
        async def test_headers():
            return {"ok": True}

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/test-headers")

        self.assertEqual(response.status_code, 200)
        self.assertIn("x-ratelimit-limit", response.headers)
        self.assertIn("x-ratelimit-remaining", response.headers)
        self.assertIn("x-ratelimit-reset", response.headers)
        self.assertEqual(response.headers["x-ratelimit-limit"], "10")

    async def test_rate_limit_excludes_health_endpoints(self) -> None:
        settings = _make_settings(
            rate_limit_enabled=True,
            rate_limit_requests_per_minute=1,
            rate_limit_exclude_paths=("/livez", "/readyz", "/healthz"),
            cors_allowed_origins=(),
        )
        app = _create_test_app(settings)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            # Should not be rate-limited even with max_requests=1
            for _ in range(5):
                resp = await client.get("/livez")
                self.assertEqual(resp.status_code, 200)

    async def test_rate_limit_disabled(self) -> None:
        settings = _make_settings(
            rate_limit_enabled=False,
            cors_allowed_origins=(),
        )
        app = _create_test_app(settings)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            for _ in range(100):
                resp = await client.get("/livez")
                self.assertEqual(resp.status_code, 200)
            # No rate-limit headers when disabled
            self.assertNotIn("x-ratelimit-limit", resp.headers)


# ---------------------------------------------------------------------------
# Security Headers Tests
# ---------------------------------------------------------------------------

class SecurityHeadersTests(unittest.IsolatedAsyncioTestCase):
    async def test_security_headers_present_on_responses(self) -> None:
        app = _create_test_app()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/livez")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertEqual(response.headers.get("x-xss-protection"), "0")

    async def test_hsts_not_included_in_test_env(self) -> None:
        settings = _make_settings(environment="test")
        app = _create_test_app(settings)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/livez")

        self.assertIsNone(response.headers.get("strict-transport-security"))

    async def test_hsts_included_in_production_env(self) -> None:
        settings = _make_settings(environment="production")
        app = _create_test_app(settings)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/livez")

        self.assertEqual(
            response.headers.get("strict-transport-security"),
            "max-age=31536000; includeSubDomains",
        )


# ---------------------------------------------------------------------------
# Request Size Limit Tests
# ---------------------------------------------------------------------------

class RequestSizeLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_request_body_size_limit_returns_413(self) -> None:
        settings = _make_settings(
            max_request_body_bytes=100,
            cors_allowed_origins=(),
            rate_limit_enabled=False,
        )
        app = _create_test_app(settings)

        @app.post("/test-upload")
        async def upload():
            return {"ok": True}

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/test-upload",
                content="x" * 200,
                headers={"Content-Length": "200", "Content-Type": "text/plain"},
            )

        self.assertEqual(response.status_code, 413)
        data = response.json()
        self.assertEqual(data["error"]["code"], "request_too_large")

    async def test_request_within_limit_passes(self) -> None:
        settings = _make_settings(
            max_request_body_bytes=1024,
            cors_allowed_origins=(),
            rate_limit_enabled=False,
        )
        app = _create_test_app(settings)

        @app.post("/test-upload")
        async def upload():
            return {"ok": True}

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/test-upload",
                content="x" * 100,
                headers={"Content-Type": "text/plain"},
            )

        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Pagination Tests
# ---------------------------------------------------------------------------

class PaginationParamsTests(unittest.TestCase):
    def test_defaults(self) -> None:
        params = PaginationParams()
        self.assertEqual(params.page, 1)
        self.assertEqual(params.page_size, 20)
        self.assertEqual(params.offset, 0)
        self.assertEqual(params.limit, 20)

    def test_offset_calculation(self) -> None:
        params = PaginationParams(page=3, page_size=20)
        self.assertEqual(params.offset, 40)

    def test_page_1_offset_is_zero(self) -> None:
        params = PaginationParams(page=1, page_size=10)
        self.assertEqual(params.offset, 0)

    def test_limit_equals_page_size(self) -> None:
        params = PaginationParams(page=1, page_size=50)
        self.assertEqual(params.limit, 50)


class PaginatedResponseTests(unittest.TestCase):
    def test_total_pages_calculation(self) -> None:
        params = PaginationParams(page=1, page_size=10)
        result = paginate(list(range(10)), total=25, params=params)
        self.assertEqual(result.total_pages, 3)
        self.assertEqual(result.total, 25)
        self.assertEqual(result.page, 1)
        self.assertEqual(result.page_size, 10)
        self.assertEqual(len(result.items), 10)

    def test_total_pages_zero_when_empty(self) -> None:
        params = PaginationParams(page=1, page_size=20)
        result = paginate([], total=0, params=params)
        self.assertEqual(result.total_pages, 0)
        self.assertEqual(result.total, 0)

    def test_total_pages_exact_division(self) -> None:
        params = PaginationParams(page=1, page_size=5)
        result = paginate(list(range(5)), total=20, params=params)
        self.assertEqual(result.total_pages, 4)

    def test_single_page(self) -> None:
        params = PaginationParams(page=1, page_size=100)
        result = paginate(["a", "b", "c"], total=3, params=params)
        self.assertEqual(result.total_pages, 1)
        self.assertEqual(result.items, ["a", "b", "c"])


class GetPaginationParamsTests(unittest.TestCase):
    def test_returns_params_with_defaults(self) -> None:
        params = get_pagination_params()
        self.assertEqual(params.page, 1)
        self.assertEqual(params.page_size, 20)

    def test_returns_params_with_custom_values(self) -> None:
        params = get_pagination_params(page=5, page_size=50)
        self.assertEqual(params.page, 5)
        self.assertEqual(params.page_size, 50)
        self.assertEqual(params.offset, 200)
