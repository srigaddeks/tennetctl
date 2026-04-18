"""iam.scim — Pydantic v2 schemas: SCIM 2.0 + admin token models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# ── SCIM 2.0 core schemas (RFC 7643 / RFC 7644) ──────────────────────────────

SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_LIST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCIM_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


def scim_error(status: int, detail: str) -> dict:
    return {
        "schemas": [SCIM_ERROR_SCHEMA],
        "status": str(status),
        "detail": detail,
    }


def scim_user(user: dict, base_url: str, org_slug: str) -> dict:
    uid = user["id"]
    meta = {
        "resourceType": "User",
        "location": f"{base_url}/scim/v2/{org_slug}/Users/{uid}",
    }
    if user.get("created_at"):
        meta["created"] = user["created_at"].isoformat() if hasattr(user["created_at"], "isoformat") else user["created_at"]
    if user.get("updated_at"):
        meta["lastModified"] = user["updated_at"].isoformat() if hasattr(user["updated_at"], "isoformat") else user["updated_at"]

    return {
        "schemas": [SCIM_USER_SCHEMA],
        "id": uid,
        "externalId": user.get("scim_external_id"),
        "userName": user.get("email", ""),
        "displayName": user.get("display_name", ""),
        "name": {"formatted": user.get("display_name", "")},
        "emails": [{"value": user.get("email", ""), "primary": True, "type": "work"}],
        "active": bool(user.get("is_active", True)),
        "meta": meta,
    }


def scim_group(group: dict, base_url: str, org_slug: str, members: list[dict] | None = None) -> dict:
    gid = group["id"]
    meta = {
        "resourceType": "Group",
        "location": f"{base_url}/scim/v2/{org_slug}/Groups/{gid}",
    }
    result: dict[str, Any] = {
        "schemas": [SCIM_GROUP_SCHEMA],
        "id": gid,
        "displayName": group.get("label", group.get("code", "")),
        "meta": meta,
    }
    if members is not None:
        result["members"] = [{"value": m["id"], "display": m.get("display_name", "")} for m in members]
    return result


def scim_list(resources: list[dict], total: int, start_index: int = 1) -> dict:
    return {
        "schemas": [SCIM_LIST_SCHEMA],
        "totalResults": total,
        "startIndex": start_index,
        "itemsPerPage": len(resources),
        "Resources": resources,
    }


# ── Admin token schemas ───────────────────────────────────────────────────────

class ScimTokenCreate(BaseModel):
    label: str = ""


class ScimTokenRow(BaseModel):
    id: str
    org_id: str
    label: str
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
