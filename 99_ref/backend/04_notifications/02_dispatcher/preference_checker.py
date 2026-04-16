from __future__ import annotations

from importlib import import_module

import asyncpg

_constants_module = import_module("backend.04_notifications.constants")
NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'


class PreferenceChecker:
    async def is_enabled(
        self,
        conn: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        notification_type_code: str,
        channel_code: str,
        category_code: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> bool:
        # Check mandatory flags — mandatory types/categories are always delivered
        row = await conn.fetchrow(
            f"""
            SELECT nt.is_mandatory, nc.is_mandatory AS category_mandatory
            FROM {SCHEMA}."04_dim_notification_types" nt
            JOIN {SCHEMA}."03_dim_notification_categories" nc
                ON nc.code = nt.category_code
            WHERE nt.code = $1
            """,
            notification_type_code,
        )
        if not row:
            return False
        if row["is_mandatory"] or row["category_mandatory"]:
            return True

        # Retrieve all applicable user preferences, ordered from most specific
        # to least specific scope level. Within each scope level, preferences
        # scoped to a workspace beat org-scoped, which beat unscoped.
        prefs = await conn.fetch(
            f"""
            SELECT scope_level, channel_code, category_code,
                   notification_type_code, scope_org_id, scope_workspace_id,
                   is_enabled
            FROM {SCHEMA}."17_lnk_user_notification_preferences"
            WHERE user_id = $1
              AND tenant_key = $2
              AND (scope_org_id IS NULL OR scope_org_id = $3)
              AND (scope_workspace_id IS NULL OR scope_workspace_id = $4)
            ORDER BY
                CASE scope_level
                    WHEN 'type' THEN 1
                    WHEN 'category' THEN 2
                    WHEN 'channel' THEN 3
                    WHEN 'global' THEN 4
                END,
                CASE WHEN scope_workspace_id IS NOT NULL THEN 1
                     WHEN scope_org_id IS NOT NULL THEN 2
                     ELSE 3
                END
            """,
            user_id,
            tenant_key,
            org_id,
            workspace_id,
        )

        for pref in prefs:
            sl = pref["scope_level"]

            if sl == "type":
                # Must match the notification type; optionally also the channel
                if pref["notification_type_code"] != notification_type_code:
                    continue
                if pref["channel_code"] is not None and pref["channel_code"] != channel_code:
                    continue
                return pref["is_enabled"]

            if sl == "category":
                # Must match the category; optionally also the channel
                if pref["category_code"] != category_code:
                    continue
                if pref["channel_code"] is not None and pref["channel_code"] != channel_code:
                    continue
                return pref["is_enabled"]

            if sl == "channel":
                # Must match the channel
                if pref["channel_code"] != channel_code:
                    continue
                return pref["is_enabled"]

            if sl == "global":
                # Global preference — no additional filtering
                return pref["is_enabled"]

        # Fall back to the channel-type default from the dimension table
        default_row = await conn.fetchrow(
            f"""
            SELECT is_default
            FROM {SCHEMA}."07_dim_notification_channel_types"
            WHERE notification_type_code = $1 AND channel_code = $2
            """,
            notification_type_code,
            channel_code,
        )
        if default_row:
            return default_row["is_default"]
        return True
