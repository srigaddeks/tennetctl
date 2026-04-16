"""Repository for global library CRUD + subscriptions."""

from __future__ import annotations


_GL = '"15_sandbox"."80_fct_global_libraries"'
_SUBS = '"15_sandbox"."81_lnk_org_library_subscriptions"'
_LIBS = '"15_sandbox"."29_fct_libraries"'
_LIB_PROPS = '"15_sandbox"."48_dtl_library_properties"'
_LIB_POLICIES = '"15_sandbox"."51_lnk_library_policies"'
_POLICIES = '"15_sandbox"."24_fct_policies"'
_POLICY_PROPS = '"15_sandbox"."47_dtl_policy_properties"'
_THREAT_TYPES = '"15_sandbox"."23_fct_threat_types"'
_THREAT_PROPS = '"15_sandbox"."46_dtl_threat_type_properties"'
_SIGNALS = '"15_sandbox"."22_fct_signals"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'
_CONN_TYPES = '"15_sandbox"."03_dim_connector_types"'


class GlobalLibraryRepository:

    async def list_published(
        self,
        conn,
        *,
        category_code: str | None = None,
        connector_type_code: str | None = None,
        is_featured: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        conditions = ["publish_status = 'published'"]
        params: list = []
        idx = 1

        if category_code:
            conditions.append(f"category_code = ${idx}")
            params.append(category_code)
            idx += 1
        if connector_type_code:
            conditions.append(f"${idx} = ANY(connector_type_codes)")
            params.append(connector_type_code)
            idx += 1
        if is_featured is not None:
            conditions.append(f"is_featured = ${idx}")
            params.append(is_featured)
            idx += 1
        if search:
            conditions.append(f"(global_name ILIKE ${idx} OR description ILIKE ${idx})")
            params.append(f"%{search}%")
            idx += 1

        where = " AND ".join(conditions)
        offset = (page - 1) * page_size

        total_row = await conn.fetchrow(
            f"SELECT COUNT(*) AS cnt FROM {_GL} WHERE {where}",
            *params,
        )
        total = total_row["cnt"] if total_row else 0

        rows = await conn.fetch(
            f"""
            SELECT id::text, global_code, global_name, description, category_code,
                   connector_type_codes, publish_status, is_featured, download_count,
                   version_number, published_at::text, created_at::text, updated_at::text
            FROM {_GL}
            WHERE {where}
            ORDER BY is_featured DESC, download_count DESC, created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params, page_size, offset,
        )
        return [dict(r) for r in rows], total

    async def get_by_id(self, conn, global_library_id: str) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT id::text, global_code, global_name, description, category_code,
                   connector_type_codes, publish_status, is_featured, download_count,
                   version_number, source_library_id::text, source_org_id::text,
                   curator_user_id::text, published_at::text, created_at::text, updated_at::text
            FROM {_GL}
            WHERE id = $1::uuid
            """,
            global_library_id,
        )
        return dict(row) if row else None

    async def create_global_library(
        self,
        conn,
        *,
        global_library_id: str,
        source_library_id: str,
        source_org_id: str,
        global_code: str,
        global_name: str,
        description: str | None,
        category_code: str | None,
        connector_type_codes: list[str],
        curator_user_id: str,
        is_featured: bool,
    ) -> None:
        await conn.execute(
            f"""
            INSERT INTO {_GL} (
                id, source_library_id, source_org_id,
                global_code, global_name, description, category_code,
                connector_type_codes, curator_user_id,
                publish_status, is_featured, published_at,
                created_at, updated_at
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid,
                $4, $5, $6, $7,
                $8::text[], $9::uuid,
                'published', $10, NOW(),
                NOW(), NOW()
            )
            """,
            global_library_id, source_library_id, source_org_id,
            global_code, global_name, description, category_code,
            connector_type_codes, curator_user_id,
            is_featured,
        )

    async def get_subscription(self, conn, *, org_id: str, global_library_id: str) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT s.id::text, s.org_id::text, s.global_library_id::text,
                   s.subscribed_by::text, s.subscribed_version, s.local_library_id::text,
                   s.auto_update, s.subscribed_at::text,
                   g.global_code, g.global_name, g.version_number AS latest_version
            FROM {_SUBS} s
            JOIN {_GL} g ON g.id = s.global_library_id
            WHERE s.org_id = $1::uuid AND s.global_library_id = $2::uuid
            """,
            org_id, global_library_id,
        )
        return dict(row) if row else None

    async def list_subscriptions(self, conn, *, org_id: str) -> list[dict]:
        rows = await conn.fetch(
            f"""
            SELECT s.id::text, s.org_id::text, s.global_library_id::text,
                   s.subscribed_version, s.local_library_id::text,
                   s.auto_update, s.subscribed_at::text,
                   g.global_code, g.global_name, g.version_number AS latest_version
            FROM {_SUBS} s
            JOIN {_GL} g ON g.id = s.global_library_id
            WHERE s.org_id = $1::uuid
            ORDER BY s.subscribed_at DESC
            """,
            org_id,
        )
        return [dict(r) for r in rows]

    async def create_subscription(
        self,
        conn,
        *,
        org_id: str,
        global_library_id: str,
        subscribed_by: str,
        subscribed_version: int,
        local_library_id: str,
        auto_update: bool,
    ) -> str:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_SUBS} (
                org_id, global_library_id, subscribed_by,
                subscribed_version, local_library_id, auto_update
            ) VALUES (
                $1::uuid, $2::uuid, $3::uuid,
                $4, $5::uuid, $6
            )
            ON CONFLICT (org_id, global_library_id) DO UPDATE SET
                subscribed_version = EXCLUDED.subscribed_version,
                local_library_id = EXCLUDED.local_library_id,
                auto_update = EXCLUDED.auto_update
            RETURNING id::text
            """,
            org_id, global_library_id, subscribed_by,
            subscribed_version, local_library_id, auto_update,
        )
        return row["id"]

    async def increment_download_count(self, conn, global_library_id: str) -> None:
        await conn.execute(
            f"UPDATE {_GL} SET download_count = download_count + 1, updated_at = NOW() WHERE id = $1::uuid",
            global_library_id,
        )

    async def load_source_library_entities(self, conn, *, source_library_id: str) -> dict:
        """Load policies, threat types, and signals linked to a library."""
        # Load linked policies
        policy_rows = await conn.fetch(
            f"""
            SELECT p.id::text, p.policy_code, p.threat_type_id::text,
                   p.actions::text, p.is_enabled,
                   pp.property_value AS name
            FROM {_LIB_POLICIES} lp
            JOIN {_POLICIES} p ON p.id = lp.policy_id
            LEFT JOIN {_POLICY_PROPS} pp ON pp.policy_id = p.id AND pp.property_key = 'name'
            WHERE lp.library_id = $1::uuid AND p.is_active = true
            ORDER BY lp.sort_order
            """,
            source_library_id,
        )

        # Load threat types for these policies
        threat_ids = list({r["threat_type_id"] for r in policy_rows if r["threat_type_id"]})
        threat_rows = []
        for tt_id in threat_ids:
            tt = await conn.fetchrow(
                f"""
                SELECT t.id::text, t.threat_type_code,
                       t.expression_tree::text,
                       tp.property_value AS name,
                       td.property_value AS description,
                       ct.code AS connector_type_code
                FROM {_THREAT_TYPES} t
                LEFT JOIN {_THREAT_PROPS} tp ON tp.threat_type_id = t.id AND tp.property_key = 'name'
                LEFT JOIN {_THREAT_PROPS} td ON td.threat_type_id = t.id AND td.property_key = 'description'
                LEFT JOIN {_CONN_TYPES} ct ON ct.id = t.connector_type_id
                WHERE t.id = $1::uuid AND t.is_active = true
                """,
                tt_id,
            )
            if tt:
                threat_rows.append(dict(tt))

        # Load signals referenced in expression trees
        import json
        signal_codes: set[str] = set()
        for tt in threat_rows:
            try:
                tree = json.loads(tt["expression_tree"] or "{}")
                _collect_signal_codes(tree, signal_codes)
            except Exception:
                pass

        signal_rows = []
        if signal_codes:
            for code in signal_codes:
                sig = await conn.fetchrow(
                    f"""
                    SELECT s.id::text, s.signal_code,
                           sp_name.property_value AS name,
                           sp_src.property_value AS python_source,
                           sp_args.property_value AS signal_args_schema,
                           ct.code AS connector_type_code
                    FROM {_SIGNALS} s
                    LEFT JOIN {_SIGNAL_PROPS} sp_name ON sp_name.signal_id = s.id AND sp_name.property_key = 'name'
                    LEFT JOIN {_SIGNAL_PROPS} sp_src ON sp_src.signal_id = s.id AND sp_src.property_key = 'python_source'
                    LEFT JOIN {_SIGNAL_PROPS} sp_args ON sp_args.signal_id = s.id AND sp_args.property_key = 'signal_args_schema'
                    LEFT JOIN {_CONN_TYPES} ct ON ct.id = s.connector_type_id
                    WHERE s.signal_code = $1 AND s.is_active = true
                    LIMIT 1
                    """,
                    code,
                )
                if sig:
                    signal_rows.append(dict(sig))

        return {
            "policies": [dict(r) for r in policy_rows],
            "threat_types": threat_rows,
            "signals": signal_rows,
        }


def _collect_signal_codes(tree: dict, codes: set) -> None:
    if not isinstance(tree, dict):
        return
    if "signal_code" in tree:
        codes.add(tree["signal_code"])
    for child in tree.get("conditions", []):
        _collect_signal_codes(child, codes)
