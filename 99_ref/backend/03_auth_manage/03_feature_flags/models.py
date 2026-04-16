from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FeatureCategoryRecord:
    id: str
    code: str
    name: str
    description: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class FeatureFlagRecord:
    id: str
    code: str
    name: str
    description: str
    category_code: str
    feature_scope: str
    access_mode: str
    lifecycle_state: str
    initial_audience: str
    env_dev: bool
    env_staging: bool
    env_prod: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class FeaturePermissionRecord:
    id: str
    code: str
    feature_flag_code: str
    permission_action_code: str
    name: str
    description: str
@dataclass(frozen=True, slots=True)
class PermissionActionRecord:
    id: str
    code: str
    name: str
    description: str
    sort_order: int
