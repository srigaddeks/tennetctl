"""Smoke tests — import graph + Pydantic schema validation."""

from __future__ import annotations

from importlib import import_module


def test_core_modules_import():
    for mod in [
        "apps.solsocial.backend.01_core.config",
        "apps.solsocial.backend.01_core.database",
        "apps.solsocial.backend.01_core.response",
        "apps.solsocial.backend.01_core.errors",
        "apps.solsocial.backend.01_core.id",
        "apps.solsocial.backend.01_core.middleware",
        "apps.solsocial.backend.01_core.authz",
        "apps.solsocial.backend.01_core.tennetctl_client",
    ]:
        import_module(mod)


def test_feature_modules_import():
    for mod in [
        "apps.solsocial.backend.02_features.10_channels.routes",
        "apps.solsocial.backend.02_features.20_posts.routes",
        "apps.solsocial.backend.02_features.30_queue.routes",
        "apps.solsocial.backend.02_features.40_calendar.routes",
        "apps.solsocial.backend.02_features.50_ideas.routes",
        "apps.solsocial.backend.02_features.60_oauth.routes",
    ]:
        import_module(mod)


def test_post_create_schema_rejects_extra_fields():
    from pydantic import ValidationError
    import pytest
    schemas = import_module("apps.solsocial.backend.02_features.20_posts.schemas")
    with pytest.raises(ValidationError):
        schemas.PostCreate(channel_id="x", body="hello", bogus=True)  # type: ignore[call-arg]


def test_id_generates_uuidv7():
    _id = import_module("apps.solsocial.backend.01_core.id")
    v = _id.uuid7()
    assert isinstance(v, str)
    assert len(v) == 36


def test_stub_publisher_roundtrip():
    import asyncio
    providers = import_module("apps.solsocial.backend.02_features.60_oauth.providers")
    adapter = providers.StubAdapter("linkedin")

    async def go():
        result = await adapter.exchange_code(code="abcdef", redirect_uri="x", state="s")
        assert result["tokens"]["access_token"].startswith("stub_linkedin_at_")
        assert result["external_id"].startswith("stub_linkedin_")
        pub = await adapter.publish(
            tokens=result["tokens"],
            channel={"provider_code": "linkedin", "handle": "@x", "external_id": "abc"},
            post={"id": "01234567-89ab-cdef-0123-456789abcdef", "body": "hi", "link": None, "media": []},
        )
        assert pub["external_post_id"].startswith("stub_linkedin_post_")

    asyncio.run(go())
