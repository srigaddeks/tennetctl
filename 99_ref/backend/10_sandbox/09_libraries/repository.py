from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import LibraryRecord, LibraryPolicyRecord, RecommendedLibraryRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.libraries.repository", logger_name="backend.sandbox.libraries.repository.instrumentation")
class LibraryRepository:

    # ── list ──────────────────────────────────────────────────

    async def list_libraries(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        library_type_code: str | None = None,
        is_published: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LibraryRecord]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if library_type_code is not None:
            filters.append(f"library_type_code = ${idx}")
            values.append(library_type_code)
            idx += 1
        if is_published is not None:
            filters.append(f"is_published = ${idx}")
            values.append(is_published)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, library_code, library_type_code,
                   library_type_name, version_number, is_published, is_active,
                   created_at::text, updated_at::text, name, description,
                   policy_count
            FROM {SCHEMA}."64_vw_library_detail"
            WHERE {where_clause}
            ORDER BY library_code ASC, version_number DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_library(r) for r in rows]

    async def count_libraries(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        library_type_code: str | None = None,
        is_published: bool | None = None,
    ) -> int:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if library_type_code is not None:
            filters.append(f"library_type_code = ${idx}")
            values.append(library_type_code)
            idx += 1
        if is_published is not None:
            filters.append(f"is_published = ${idx}")
            values.append(is_published)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."64_vw_library_detail" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    # ── get ───────────────────────────────────────────────────

    async def get_library_by_id(
        self, connection: asyncpg.Connection, library_id: str
    ) -> LibraryRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, library_code, library_type_code,
                   library_type_name, version_number, is_published, is_active,
                   created_at::text, updated_at::text, name, description,
                   policy_count
            FROM {SCHEMA}."64_vw_library_detail"
            WHERE id = $1
            """,
            library_id,
        )
        return _row_to_library(row) if row else None

    async def get_library_properties(
        self, connection: asyncpg.Connection, library_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."48_dtl_library_properties"
            WHERE library_id = $1
            """,
            library_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    # ── create ────────────────────────────────────────────────

    async def create_library(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        library_code: str,
        library_type_code: str,
        version_number: int,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."29_fct_libraries"
                (id, tenant_key, org_id, library_code, library_type_code,
                 version_number, is_published,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, FALSE,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $7, $8, $9, $10, NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            library_code,
            library_type_code,
            version_number,
            now,
            now,
            created_by,
            created_by,
        )
        return id

    async def get_next_version(
        self, connection: asyncpg.Connection, org_id: str, library_code: str
    ) -> int:
        """Returns next version number with advisory lock to prevent races.
        Must be called inside a transaction."""
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"sb:library_version:{org_id}:{library_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."29_fct_libraries"
            WHERE org_id = $1 AND library_code = $2
            """,
            org_id,
            library_code,
        )
        return row["next_version"] if row else 1

    # ── update ────────────────────────────────────────────────

    async def update_library(
        self,
        connection: asyncpg.Connection,
        library_id: str,
        *,
        library_type_code: str | None = None,
        updated_by: str,
        now: object,
    ) -> bool:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if library_type_code is not None:
            fields.append(f"library_type_code = ${idx}")
            values.append(library_type_code)
            idx += 1

        values.append(library_id)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."29_fct_libraries"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    # ── upsert properties ────────────────────────────────────

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        library_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (library_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."48_dtl_library_properties"
                (id, library_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (library_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── soft delete ───────────────────────────────────────────

    async def soft_delete(
        self,
        connection: asyncpg.Connection,
        library_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."29_fct_libraries"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, library_id,
        )
        return result != "UPDATE 0"

    # ── publish ───────────────────────────────────────────────

    async def publish_library(
        self,
        connection: asyncpg.Connection,
        library_id: str,
        *,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."29_fct_libraries"
            SET is_published = TRUE, updated_at = $1, updated_by = $2
            WHERE id = $3 AND is_deleted = FALSE AND is_published = FALSE
            """,
            now, updated_by, library_id,
        )
        return result != "UPDATE 0"

    # ── clone ─────────────────────────────────────────────────

    async def clone_library(
        self,
        connection: asyncpg.Connection,
        source_id: str,
        *,
        new_id: str,
        new_version: int,
        created_by: str,
        now: object,
    ) -> str:
        # Copy fact row
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."29_fct_libraries"
                (id, tenant_key, org_id, library_code, library_type_code,
                 version_number, is_published,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            SELECT
                $1, tenant_key, org_id, library_code, library_type_code,
                $2, FALSE,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $3, $4, $5, $6, NULL, NULL
            FROM {SCHEMA}."29_fct_libraries"
            WHERE id = $7 AND is_deleted = FALSE
            """,
            new_id, new_version, now, now, created_by, created_by, source_id,
        )
        # Copy properties
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."48_dtl_library_properties"
                (id, library_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            SELECT gen_random_uuid(), $1, property_key, property_value,
                   $2, $3, $4, $5
            FROM {SCHEMA}."48_dtl_library_properties"
            WHERE library_id = $6
            """,
            new_id, now, now, created_by, created_by, source_id,
        )
        # Copy policy links
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."51_lnk_library_policies"
                (id, library_id, policy_id, sort_order, created_at, created_by)
            SELECT gen_random_uuid(), $1, policy_id, sort_order, $2, $3
            FROM {SCHEMA}."51_lnk_library_policies"
            WHERE library_id = $4
            """,
            new_id, now, created_by, source_id,
        )
        return new_id

    # ── policy links ──────────────────────────────────────────

    async def add_policy(
        self,
        connection: asyncpg.Connection,
        *,
        library_id: str,
        policy_id: str,
        sort_order: int,
        created_by: str,
    ) -> str:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."51_lnk_library_policies"
                (id, library_id, policy_id, sort_order, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, NOW(), $4)
            ON CONFLICT (library_id, policy_id) DO UPDATE
            SET sort_order = EXCLUDED.sort_order
            RETURNING id::text
            """,
            library_id, policy_id, sort_order, created_by,
        )
        return row["id"] if row else ""

    async def remove_policy(
        self,
        connection: asyncpg.Connection,
        library_id: str,
        policy_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."51_lnk_library_policies"
            WHERE library_id = $1 AND policy_id = $2
            """,
            library_id, policy_id,
        )
        return result != "DELETE 0"

    async def list_library_policies(
        self,
        connection: asyncpg.Connection,
        library_id: str,
    ) -> list[LibraryPolicyRecord]:
        rows = await connection.fetch(
            f"""
            SELECT lp.id::text, lp.library_id::text, lp.policy_id::text,
                   pol.policy_code, pol.name AS policy_name, lp.sort_order
            FROM {SCHEMA}."51_lnk_library_policies" lp
            LEFT JOIN {SCHEMA}."63_vw_policy_detail" pol ON pol.id = lp.policy_id
            WHERE lp.library_id = $1
            ORDER BY lp.sort_order ASC
            """,
            library_id,
        )
        return [
            LibraryPolicyRecord(
                id=r["id"],
                library_id=r["library_id"],
                policy_id=r["policy_id"],
                policy_code=r["policy_code"],
                policy_name=r["policy_name"],
                sort_order=r["sort_order"],
            )
            for r in rows
        ]

    # ── connector type mappings ───────────────────────────────

    async def add_connector_type_mapping(
        self,
        connection: asyncpg.Connection,
        *,
        library_id: str,
        connector_type_code: str,
        asset_version_id: str | None,
        is_recommended: bool,
        created_by: str,
    ) -> str:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."13_lnk_library_connector_types"
                (id, library_id, connector_type_code, asset_version_id,
                 is_recommended, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW(), $5)
            ON CONFLICT (library_id, connector_type_code, asset_version_id) DO UPDATE
            SET is_recommended = EXCLUDED.is_recommended
            RETURNING id::text
            """,
            library_id, connector_type_code, asset_version_id,
            is_recommended, created_by,
        )
        return row["id"] if row else ""

    async def list_recommended_libraries(
        self,
        connection: asyncpg.Connection,
        connector_type_code: str,
        asset_version_id: str | None = None,
    ) -> list[RecommendedLibraryRecord]:
        if asset_version_id is not None:
            rows = await connection.fetch(
                f"""
                SELECT lct.library_id::text, lib.library_code,
                       (SELECT p.property_value FROM {SCHEMA}."48_dtl_library_properties" p
                        WHERE p.library_id = lib.id AND p.property_key = 'name') AS library_name,
                       lib.library_type_code,
                       lct.is_recommended,
                       lct.connector_type_code,
                       av.version_code AS asset_version_code
                FROM {SCHEMA}."13_lnk_library_connector_types" lct
                JOIN {SCHEMA}."29_fct_libraries" lib ON lib.id = lct.library_id
                    AND lib.is_deleted = FALSE AND lib.is_published = TRUE
                LEFT JOIN {SCHEMA}."12_dim_asset_versions" av ON av.id = lct.asset_version_id
                WHERE lct.connector_type_code = $1
                  AND lct.asset_version_id = $2
                ORDER BY lct.is_recommended DESC, lib.library_code ASC
                """,
                connector_type_code, asset_version_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT lct.library_id::text, lib.library_code,
                       (SELECT p.property_value FROM {SCHEMA}."48_dtl_library_properties" p
                        WHERE p.library_id = lib.id AND p.property_key = 'name') AS library_name,
                       lib.library_type_code,
                       lct.is_recommended,
                       lct.connector_type_code,
                       av.version_code AS asset_version_code
                FROM {SCHEMA}."13_lnk_library_connector_types" lct
                JOIN {SCHEMA}."29_fct_libraries" lib ON lib.id = lct.library_id
                    AND lib.is_deleted = FALSE AND lib.is_published = TRUE
                LEFT JOIN {SCHEMA}."12_dim_asset_versions" av ON av.id = lct.asset_version_id
                WHERE lct.connector_type_code = $1
                ORDER BY lct.is_recommended DESC, lib.library_code ASC
                """,
                connector_type_code,
            )
        return [
            RecommendedLibraryRecord(
                library_id=r["library_id"],
                library_code=r["library_code"],
                library_name=r["library_name"],
                library_type_code=r["library_type_code"],
                is_recommended=r["is_recommended"],
                connector_type_code=r["connector_type_code"],
                asset_version_code=r["asset_version_code"],
            )
            for r in rows
        ]


def _row_to_library(r) -> LibraryRecord:
    return LibraryRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        library_code=r["library_code"],
        library_type_code=r["library_type_code"],
        library_type_name=r["library_type_name"],
        version_number=r["version_number"],
        is_published=r["is_published"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
        policy_count=r["policy_count"],
    )
