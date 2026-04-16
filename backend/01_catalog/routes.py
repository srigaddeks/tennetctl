"""
Catalog read-only HTTP surface — exposes the live node registry for UI/inspection.

Core infra router (not module-gated). Reads from 01_catalog fct tables joined
with their dim lookups. Ignores tombstoned rows.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_response: Any = import_module("backend.01_core.response")

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


_NODES_SQL = """
SELECT
    n.key              AS node_key,
    nk.code            AS kind,
    n.handler_path     AS handler,
    n.emits_audit      AS emits_audit,
    n.timeout_ms       AS timeout_ms,
    n.retries          AS retries,
    tx.code            AS tx_mode,
    n.version          AS version,
    n.deprecated_at    AS deprecated_at,
    sf.key             AS sub_feature_key,
    sf.number          AS sub_feature_number,
    f.key              AS feature_key,
    f.number           AS feature_number,
    m.code             AS module
FROM "01_catalog"."12_fct_nodes" n
JOIN "01_catalog"."02_dim_node_kinds" nk ON nk.id = n.kind_id
JOIN "01_catalog"."03_dim_tx_modes"   tx ON tx.id = n.tx_mode_id
JOIN "01_catalog"."11_fct_sub_features" sf ON sf.id = n.sub_feature_id
JOIN "01_catalog"."10_fct_features"     f  ON f.id  = sf.feature_id
JOIN "01_catalog"."01_dim_modules"      m  ON m.id  = f.module_id
WHERE n.tombstoned_at IS NULL
ORDER BY f.number, sf.number, n.key;
"""


@router.get("/nodes")
async def list_nodes(request: Request):
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(_NODES_SQL)
    nodes = [
        {
            "node_key": r["node_key"],
            "kind": r["kind"],
            "handler": r["handler"],
            "emits_audit": r["emits_audit"],
            "timeout_ms": r["timeout_ms"],
            "retries": r["retries"],
            "tx_mode": r["tx_mode"],
            "version": r["version"],
            "deprecated": r["deprecated_at"] is not None,
            "sub_feature_key": r["sub_feature_key"],
            "feature_key": r["feature_key"],
            "feature_number": r["feature_number"],
            "module": r["module"],
        }
        for r in rows
    ]
    return _response.paginated(nodes, total=len(nodes), limit=len(nodes), offset=0)
