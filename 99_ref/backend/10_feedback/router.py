from __future__ import annotations
from importlib import import_module

_tickets_router_module = import_module("backend.10_feedback.01_tickets.router")
router = _tickets_router_module.router
