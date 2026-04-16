from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserAccessAction:
    feature_code: str
    feature_name: str
    action_code: str
    category_code: str
    access_mode: str
    env_dev: bool
    env_staging: bool
    env_prod: bool


@dataclass(frozen=True, slots=True)
class OrgInfo:
    id: str
    name: str
    slug: str
    org_type_code: str


@dataclass(frozen=True, slots=True)
class WorkspaceInfo:
    id: str
    org_id: str
    name: str
    slug: str
    workspace_type_code: str
    product_id: str | None
    product_name: str | None
    product_code: str | None
