"""Service layer for notify.campaigns.

Business rules:
  - Campaigns can only be scheduled from draft status.
  - Campaigns can only be cancelled from draft or scheduled status.
  - Running / completed / failed campaigns are immutable.
  - channel_code is resolved to channel_id at create time.
  - audience_query DSL: {} = all org users; {account_type_codes: [...]} = filtered.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.repository"
)
_core_id: Any = import_module("backend.01_core.id")

_CHANNEL_MAP = {
    "email":   1,
    "webpush": 2,
    "in_app":  3,
    "sms":     4,
}

_MUTABLE_STATUSES = {
    _repo.STATUS_DRAFT,
    _repo.STATUS_SCHEDULED,
}


def _resolve_channel(code: str) -> int:
    _errors: Any = import_module("backend.01_core.errors")
    ch_id = _CHANNEL_MAP.get(code)
    if ch_id is None:
        raise _errors.ValidationError(f"unknown channel_code {code!r}")
    return ch_id


async def list_campaigns(
    conn: Any,
    *,
    org_id: str,
    status_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    return await _repo.list_campaigns(
        conn, org_id=org_id, status_code=status_code, limit=limit, offset=offset
    )


async def get_campaign(conn: Any, *, campaign_id: str) -> dict | None:
    return await _repo.get_campaign(conn, campaign_id)


async def create_campaign(
    conn: Any,
    *,
    data: dict,
    created_by: str,
) -> dict:
    campaign_id = _core_id.uuid7()
    channel_id = _resolve_channel(data["channel_code"])
    raw_aq = data.get("audience_query") or {}
    audience_query: dict = raw_aq if isinstance(raw_aq, dict) else raw_aq.model_dump()

    return await _repo.create_campaign(
        conn,
        campaign_id=campaign_id,
        org_id=data["org_id"],
        name=data["name"],
        template_id=data["template_id"],
        channel_id=channel_id,
        audience_query=audience_query,
        scheduled_at=data.get("scheduled_at"),
        throttle_per_minute=data.get("throttle_per_minute", 60),
        created_by=created_by,
    )


async def update_campaign(
    conn: Any,
    *,
    campaign_id: str,
    data: dict,
    updated_by: str,
) -> dict | None:
    _errors: Any = import_module("backend.01_core.errors")

    campaign = await _repo.get_campaign(conn, campaign_id)
    if campaign is None:
        raise _errors.NotFoundError(f"campaign {campaign_id!r} not found")
    if campaign["status_id"] not in _MUTABLE_STATUSES:
        raise _errors.ValidationError(
            f"cannot edit campaign in status {campaign['status_code']!r}"
        )

    status_id: int | None = None
    if data.get("status") == "scheduled":
        if campaign["status_id"] != _repo.STATUS_DRAFT:
            raise _errors.ValidationError("can only schedule from draft status")
        if not (campaign.get("scheduled_at") or data.get("scheduled_at")):
            raise _errors.ValidationError("scheduled_at is required to schedule campaign")
        status_id = _repo.STATUS_SCHEDULED
    elif data.get("status") == "cancelled":
        if campaign["status_id"] not in (_repo.STATUS_DRAFT, _repo.STATUS_SCHEDULED):
            raise _errors.ValidationError("can only cancel draft or scheduled campaigns")
        status_id = _repo.STATUS_CANCELLED

    channel_id: int | None = None
    if data.get("channel_code"):
        channel_id = _resolve_channel(data["channel_code"])

    audience_query: dict | None = None
    if data.get("audience_query") is not None:
        q = data["audience_query"]
        audience_query = q if isinstance(q, dict) else q.model_dump()

    return await _repo.update_campaign(
        conn,
        campaign_id=campaign_id,
        updated_by=updated_by,
        name=data.get("name"),
        template_id=data.get("template_id"),
        channel_id=channel_id,
        audience_query=audience_query,
        scheduled_at=data.get("scheduled_at"),
        throttle_per_minute=data.get("throttle_per_minute"),
        status_id=status_id,
    )


async def delete_campaign(conn: Any, *, campaign_id: str, updated_by: str) -> bool:
    _errors: Any = import_module("backend.01_core.errors")

    campaign = await _repo.get_campaign(conn, campaign_id)
    if campaign is None:
        raise _errors.NotFoundError(f"campaign {campaign_id!r} not found")
    if campaign["status_id"] == _repo.STATUS_RUNNING:
        raise _errors.ValidationError("cannot delete a running campaign")
    return await _repo.delete_campaign(conn, campaign_id=campaign_id, updated_by=updated_by)


async def resolve_audience(
    conn: Any,
    *,
    org_id: str,
    audience_query: dict,
) -> list[str]:
    """Execute the audience DSL and return user IDs."""
    account_type_codes = audience_query.get("account_type_codes") or None
    return await _repo.get_audience_user_ids(
        conn, org_id=org_id, account_type_codes=account_type_codes
    )
