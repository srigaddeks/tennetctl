"""
notify feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'notify' module is enabled.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_smtp: Any = import_module("backend.02_features.06_notify.sub_features.01_smtp_configs.routes")
_groups: Any = import_module("backend.02_features.06_notify.sub_features.02_template_groups.routes")
_templates: Any = import_module("backend.02_features.06_notify.sub_features.03_templates.routes")
_variables: Any = import_module("backend.02_features.06_notify.sub_features.04_variables.routes")
_subscriptions: Any = import_module("backend.02_features.06_notify.sub_features.05_subscriptions.routes")
_deliveries: Any = import_module("backend.02_features.06_notify.sub_features.06_deliveries.routes")
_email: Any = import_module("backend.02_features.06_notify.sub_features.07_email.routes")
_webpush: Any = import_module("backend.02_features.06_notify.sub_features.08_webpush.routes")
_preferences: Any = import_module("backend.02_features.06_notify.sub_features.09_preferences.routes")
_campaigns: Any = import_module("backend.02_features.06_notify.sub_features.10_campaigns.routes")
_send: Any = import_module("backend.02_features.06_notify.sub_features.11_send.routes")

router = APIRouter()
router.include_router(_smtp.router)
router.include_router(_groups.router)
router.include_router(_templates.router)
# Variables are nested: /{template_id}/variables — must include under /v1/notify/templates prefix
router.include_router(_variables.router, prefix="/v1/notify/templates")
router.include_router(_subscriptions.router)
router.include_router(_deliveries.router)
router.include_router(_email.router)
router.include_router(_webpush.router)
router.include_router(_preferences.router)
router.include_router(_campaigns.router)
router.include_router(_send.router)
