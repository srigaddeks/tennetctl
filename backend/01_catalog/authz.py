"""
Authorization hook for the node runner (NCP v1 §9).

Runs before every `run_node` dispatch. First denial wins.
Custom checkers run first; the default checker runs last.

Register custom checkers at app startup (or in tests):
    authz.register_checker(my_rbac_check)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Awaitable, Callable

_errors: Any = import_module("backend.01_catalog.errors")
_context: Any = import_module("backend.01_catalog.context")

Checker = Callable[["_context.NodeContext", dict], Awaitable[None]]
# A Checker raises `NodeAuthDenied` to reject; otherwise returns None.

_checkers: list[Checker] = []


def register_checker(fn: Checker) -> None:
    """Append a checker to the chain. Runs before the default checker."""
    _checkers.append(fn)


def clear_checkers() -> None:
    """Clear all custom checkers. For tests/teardown."""
    _checkers.clear()


async def check_call(ctx: Any, node_meta: dict) -> None:
    """
    Validate that `ctx` is allowed to call `node_meta`.

    node_meta fields used: `key`, `kind_code`, `emits_audit`.

    Runs all registered custom checkers first (in registration order).
    Then applies the default: system calls OK; user calls need user_id.
    """
    for fn in _checkers:
        await fn(ctx, node_meta)

    if ctx.audit_category == "system":
        return

    if ctx.user_id is None:
        raise _errors.NodeAuthDenied(
            f"user_id required when audit_category={ctx.audit_category!r}",
            node_key=node_meta.get("key"),
        )
