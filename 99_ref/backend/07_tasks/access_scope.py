from __future__ import annotations

from importlib import import_module

import asyncpg

_errors_module = import_module("backend.01_core.errors")

AuthorizationError = _errors_module.AuthorizationError

TASK_SCHEMA = '"08_tasks"'

ASSIGNEE_PORTAL_MODE = "assignee"


def normalize_portal_mode(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized or None


def is_assignee_portal_mode(value: str | None) -> bool:
    return normalize_portal_mode(value) == ASSIGNEE_PORTAL_MODE


async def user_has_any_assigned_task(
    connection: asyncpg.Connection,
    *,
    user_id: str,
    tenant_key: str,
) -> bool:
    row = await connection.fetchrow(
        f"""
        SELECT 1
        FROM {TASK_SCHEMA}."10_fct_tasks" AS t
        WHERE t.tenant_key = $1
          AND t.is_deleted = FALSE
          AND (
              t.assignee_user_id = $2::uuid
              OR EXISTS (
                  SELECT 1
                  FROM {TASK_SCHEMA}."31_lnk_task_assignments" AS a
                  WHERE a.task_id = t.id
                    AND a.user_id = $2::uuid
                    AND a.is_deleted = FALSE
              )
          )
        LIMIT 1
        """,
        tenant_key,
        user_id,
    )
    return row is not None


async def is_task_visible_to_user(
    connection: asyncpg.Connection,
    *,
    user_id: str,
    task_id: str,
) -> bool:
    row = await connection.fetchrow(
        f"""
        SELECT 1
        FROM {TASK_SCHEMA}."10_fct_tasks" AS t
        WHERE t.id = $1::uuid
          AND t.is_deleted = FALSE
          AND (
              t.assignee_user_id = $2::uuid
              OR EXISTS (
                  SELECT 1
                  FROM {TASK_SCHEMA}."31_lnk_task_assignments" AS a
                  WHERE a.task_id = t.id
                    AND a.user_id = $2::uuid
                    AND a.is_deleted = FALSE
              )
          )
        LIMIT 1
        """,
        task_id,
        user_id,
    )
    return row is not None


async def assert_assignee_task_entity_access(
    connection: asyncpg.Connection,
    *,
    portal_mode: str | None,
    user_id: str,
    entity_type: str,
    entity_id: str,
) -> None:
    if not is_assignee_portal_mode(portal_mode):
        return
    if entity_type != "task":
        raise AuthorizationError("Assignee portal can only access task entities.")
    visible = await is_task_visible_to_user(
        connection,
        user_id=user_id,
        task_id=entity_id,
    )
    if not visible:
        raise AuthorizationError("This task is not assigned to the current user.")
