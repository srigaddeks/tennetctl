"""
Pydantic schema tests for product_ops.events. Pure unit tests — no DB required.

Coverage targets:
  - Custom-kind requires event_name
  - UTM length cap (256 chars)
  - Properties default empty dict
  - Batch min/max length
  - DNT default false
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest
from pydantic import ValidationError

_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.schemas"
)


def _ev(**overrides) -> dict:
    base = {
        "kind": "page_view",
        "anonymous_id": "v_abc",
        "occurred_at": datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return base


# ── IngestEventIn ──────────────────────────────────────────────────

def test_minimal_page_view_validates() -> None:
    ev = _schemas.IngestEventIn(**_ev())
    assert ev.kind == "page_view"
    assert ev.properties == {}
    assert ev.event_name is None


def test_custom_without_event_name_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        _schemas.IngestEventIn(**_ev(kind="custom"))
    assert "event_name" in str(exc.value)


def test_custom_with_event_name_validates() -> None:
    ev = _schemas.IngestEventIn(**_ev(kind="custom", event_name="cta_click"))
    assert ev.event_name == "cta_click"


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        _schemas.IngestEventIn(**_ev(kind="page_unload"))  # not in EventKind literal


def test_utm_source_too_long_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        _schemas.IngestEventIn(**_ev(utm_source="x" * 257))
    msg = str(exc.value)
    assert "256" in msg or "string_too_long" in msg or "utm" in msg


def test_utm_source_at_cap_accepted() -> None:
    ev = _schemas.IngestEventIn(**_ev(utm_source="x" * 256))
    assert ev.utm_source == "x" * 256


def test_anonymous_id_required() -> None:
    bad = _ev()
    bad.pop("anonymous_id")
    with pytest.raises(ValidationError):
        _schemas.IngestEventIn(**bad)


def test_extra_fields_rejected_strict() -> None:
    with pytest.raises(ValidationError):
        _schemas.IngestEventIn(**_ev(unknown_field="x"))


# ── TrackBatchIn ────────────────────────────────────────────────────

def test_batch_min_one_event() -> None:
    with pytest.raises(ValidationError):
        _schemas.TrackBatchIn(project_key="pk_test", events=[])


def test_batch_max_thousand_events() -> None:
    with pytest.raises(ValidationError):
        _schemas.TrackBatchIn(
            project_key="pk_test",
            events=[_ev() for _ in range(1001)],
        )


def test_batch_dnt_defaults_false() -> None:
    batch = _schemas.TrackBatchIn(project_key="pk_test", events=[_ev()])
    assert batch.dnt is False


def test_batch_with_dnt_true() -> None:
    batch = _schemas.TrackBatchIn(project_key="pk_test", events=[_ev()], dnt=True)
    assert batch.dnt is True


def test_event_kind_id_map_complete() -> None:
    """Every literal in EventKind must have a row in the map."""
    # Pull EventKind's args via typing.get_args
    from typing import get_args
    expected = set(get_args(_schemas.EventKind))
    assert set(_schemas.EVENT_KIND_ID.keys()) == expected


# ── ProductEventOut + ProductEventListResponse ──────────────────────

def test_event_out_accepts_db_row_shape() -> None:
    row = {
        "id": "01-uuid",
        "visitor_id": "v-uuid",
        "user_id": None,
        "session_id": None,
        "org_id": "org-uuid",
        "workspace_id": "ws-uuid",
        "event_kind": "page_view",
        "event_name": None,
        "occurred_at": datetime(2026, 4, 19, 10, 0, 0),
        "page_url": "https://example.com",
        "referrer": None,
        "metadata": {"title": "Landing"},
        "created_at": datetime(2026, 4, 19, 10, 0, 1),
    }
    out = _schemas.ProductEventOut(**row)
    assert out.event_kind == "page_view"
    assert out.metadata == {"title": "Landing"}


# ── AttributionResolveOut ──────────────────────────────────────────

def test_attribution_resolve_out_with_no_touches() -> None:
    out = _schemas.AttributionResolveOut(
        visitor_id="v-uuid", first_touch=None, last_touch=None,
    )
    assert out.first_touch is None
    assert out.last_touch is None
