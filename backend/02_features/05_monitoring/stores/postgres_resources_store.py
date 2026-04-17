"""Postgres implementation of ResourcesStore — hash-interned service identities."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_resource_hash(
    service_name: str,
    service_instance_id: str | None,
    service_version: str | None,
    attributes: dict[str, Any],
) -> bytes:
    """SHA-256 of canonical JSON of the identity tuple. Deterministic."""
    payload = {
        "service_name": service_name,
        "service_instance_id": service_instance_id,
        "service_version": service_version,
        "attributes": attributes or {},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


class PostgresResourcesStore:
    """Hash-interned resource records. Idempotent upsert on (org_id, resource_hash)."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def upsert(self, conn: Any, record: Any) -> int:
        resource_hash = compute_resource_hash(
            record.service_name,
            record.service_instance_id,
            record.service_version,
            record.attributes,
        )
        row = await conn.fetchrow(
            """
            INSERT INTO "05_monitoring"."11_fct_monitoring_resources"
                (org_id, resource_hash, service_name, service_instance_id, service_version, attributes)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (org_id, resource_hash) DO UPDATE
                SET service_name = EXCLUDED.service_name
            RETURNING id
            """,
            record.org_id,
            resource_hash,
            record.service_name,
            record.service_instance_id,
            record.service_version,
            record.attributes or {},
        )
        return int(row["id"])
