"""
Internal tool API endpoints — called by api_endpoint type tools in the agent pipeline.

POST /api/v1/asb/tools/inspect-schema
POST /api/v1/asb/tools/run-signal-on-dataset
POST /api/v1/asb/tools/save-signal
POST /api/v1/asb/tools/trigger-live-run
"""

from __future__ import annotations

import datetime
import json
import uuid as uuid_module
from importlib import import_module

from fastapi import Depends, Request
from pydantic import BaseModel

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_errors_module = import_module("backend.01_core.errors")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
NotFoundError = _errors_module.NotFoundError

router = InstrumentedAPIRouter(prefix="/api/v1/asb/tools", tags=["agent-sandbox-tools"])

SANDBOX_SCHEMA = '"25_agent_sandbox"'
SANDBOX_15_SCHEMA = '"15_sandbox"'

# Asset type → Steampipe table + explicit columns
ASSET_TYPE_CONFIG = {
    "github_repo": {
        "table": "github_my_repository",
        "columns": [
            "name",
            "name_with_owner",
            "is_private",
            "is_archived",
            "is_disabled",
            "is_fork",
            "is_template",
            "visibility",
            "owner_login",
            "primary_language",
            "stargazer_count",
            "created_at",
            "updated_at",
            "pushed_at",
        ],
    },
    "github_org_member": {
        "table": "github_organization_member",
        "columns": ["login", "role", "organization", "created_at"],
    },
    "github_team": {
        "table": "github_team",
        "columns": [
            "name",
            "slug",
            "description",
            "privacy",
            "members_total_count",
            "repositories_total_count",
        ],
    },
    "github_workflow": {
        "table": "github_workflow",
        "columns": ["name", "path", "state", "repository_full_name", "node_id"],
    },
}


class InspectSchemaRequest(BaseModel):
    connector_id: str
    asset_type: str


class RunSignalOnDatasetRequest(BaseModel):
    python_source: str
    dataset: list


class SaveSignalRequest(BaseModel):
    signal_code: str
    signal_intent: str
    python_source: str
    org_id: str
    workspace_id: str = ""
    asset_type: str = "github_repo"


class TriggerLiveRunRequest(BaseModel):
    connector_id: str
    signal_id: str
    org_id: str


@router.post("/inspect-schema")
async def inspect_schema(
    body: InspectSchemaRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
) -> dict:
    """Load connector credentials and run Steampipe LIMIT 3 query to get schema + sample rows."""
    db_pool = request.app.state.database_pool
    settings = request.app.state.settings

    asset_cfg = ASSET_TYPE_CONFIG.get(body.asset_type)
    if not asset_cfg:
        raise NotFoundError(f"Unknown asset_type '{body.asset_type}'")

    async with db_pool.acquire() as conn:
        # Load connector credentials
        cred_row = await conn.fetchrow(
            f"""
            SELECT cred.credential_value
            FROM {SANDBOX_SCHEMA}."20_fct_connector_instances" ci
            JOIN {SANDBOX_SCHEMA}."41_dtl_connector_credentials" cred
                ON cred.connector_instance_id = ci.id
            WHERE ci.id = $1 AND ci.is_deleted = FALSE
            ORDER BY cred.created_at DESC
            LIMIT 1
            """,
            body.connector_id,
        )
        if not cred_row:
            raise NotFoundError(
                f"Connector '{body.connector_id}' not found or has no credentials"
            )

        # Load connector type
        type_row = await conn.fetchrow(
            f"""
            SELECT ct.connector_type_code
            FROM {SANDBOX_SCHEMA}."20_fct_connector_instances" ci
            JOIN {SANDBOX_SCHEMA}."03_dim_connector_types" ct ON ct.id = ci.connector_type_id
            WHERE ci.id = $1
            """,
            body.connector_id,
        )
        connector_type_code = type_row["connector_type_code"] if type_row else "github"

    # Decrypt credentials
    _crypto_module = import_module("backend.10_sandbox.02_connectors.crypto")
    encryption_key = settings.sandbox_encryption_key
    raw_creds_json = _crypto_module.decrypt_credential(
        cred_row["credential_value"], encryption_key
    )
    credentials = json.loads(raw_creds_json)

    # Run Steampipe query
    _steampipe_module = import_module("backend.10_sandbox.19_steampipe.steampipe")
    substrate = _steampipe_module.SteampipeSubstrate(settings=settings)

    columns = asset_cfg["columns"]
    col_list = ", ".join(columns)
    sql = f"SELECT {col_list} FROM {asset_cfg['table']} LIMIT 3"

    rows = await substrate.execute_query(
        sql=sql,
        provider_type=connector_type_code,
        credentials=credentials,
    )

    return {
        "columns": columns,
        "sample_rows": rows,
    }


@router.post("/run-signal-on-dataset")
async def run_signal_on_dataset(
    body: RunSignalOnDatasetRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
) -> dict:
    """Execute signal python_source against each row in the dataset using the sandbox engine."""
    _engine_module = import_module("backend.10_sandbox.07_execution.engine")
    engine = _engine_module.SignalExecutionEngine(timeout_ms=10000, max_memory_mb=128)

    results = []
    for i, row in enumerate(body.dataset):
        result = await engine.execute(python_source=body.python_source, dataset=row)
        actual = result.result_code if result.status == "completed" else "error"
        results.append(
            {
                "row_index": i,
                "result": actual,
                "summary": result.result_summary or result.error_message or "",
                "details": result.result_details or [],
                "error": result.error_message if result.status != "completed" else None,
            }
        )

    return {"results": results}


@router.post("/save-signal")
async def save_signal(
    body: SaveSignalRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
) -> dict:
    """Save the generated signal to 15_sandbox schema."""
    import datetime

    db_pool = request.app.state.database_pool
    signal_id = str(uuid_module.uuid4())
    user_id = (
        claims.subject if hasattr(claims, "subject") else claims.get("sub", "system")
    )

    async with db_pool.acquire() as conn:
        # Get workspace_id — if not provided, use first sandbox workspace for org
        workspace_id = body.workspace_id
        if not workspace_id:
            ws_row = await conn.fetchrow(
                """
                SELECT w.id FROM "03_auth_manage"."34_fct_workspaces" w
                JOIN "03_auth_manage"."33_dim_workspace_types" wt ON wt.id = w.workspace_type_id
                WHERE w.org_id = $1 AND wt.workspace_type_code = 'sandbox' AND w.is_active = TRUE
                LIMIT 1
                """,
                body.org_id,
            )
            workspace_id = str(ws_row["id"]) if ws_row else ""

        # Get connector type dimension ID for "github"
        connector_type_row = await conn.fetchrow(
            """
            SELECT id FROM "15_sandbox"."03_dim_connector_types"
            WHERE connector_type_code = 'github'
            LIMIT 1
            """
        )
        connector_type_id = (
            str(connector_type_row["id"]) if connector_type_row else None
        )

        # Get signal status "active" ID
        status_row = await conn.fetchrow(
            'SELECT id FROM "15_sandbox"."04_dim_signal_statuses" WHERE signal_status_code = \'active\' LIMIT 1'
        )
        signal_status_id = str(status_row["id"]) if status_row else None

        # Get next version
        version_row = await conn.fetchrow(
            """
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM "15_sandbox"."22_fct_signals"
            WHERE org_id = $1 AND signal_code = $2
            """,
            body.org_id,
            body.signal_code,
        )
        version_number = version_row["next_version"]

        # Insert signal fact row
        await conn.execute(
            """
            INSERT INTO "15_sandbox"."22_fct_signals"
                (id, tenant_key, org_id, workspace_id, signal_code,
                 version_number, signal_status_id, connector_type_id,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, 'default', $2, $3, $4,
                 $5, $6, $7,
                 TRUE, FALSE,
                 NOW(), NOW(), $8, $9,
                 NULL, NULL)
            """,
            signal_id,
            body.org_id,
            workspace_id or None,
            body.signal_code,
            version_number,
            signal_status_id,
            connector_type_id,
            user_id,
            user_id,
        )

        # Insert signal properties (EAV)
        now_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        props = [
            (
                signal_id,
                "name",
                body.signal_intent[:200],
                now_dt,
                now_dt,
                user_id,
                user_id,
            ),
            (
                signal_id,
                "description",
                f"Auto-generated signal: {body.signal_intent}",
                now_dt,
                now_dt,
                user_id,
                user_id,
            ),
            (
                signal_id,
                "python_source",
                body.python_source,
                now_dt,
                now_dt,
                user_id,
                user_id,
            ),
            (
                signal_id,
                "asset_type",
                body.asset_type,
                now_dt,
                now_dt,
                user_id,
                user_id,
            ),
        ]
        await conn.executemany(
            """
            INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                (id, signal_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (signal_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at
            """,
            props,
        )

    return {"signal_id": signal_id, "signal_code": body.signal_code}


@router.post("/trigger-live-run")
async def trigger_live_run(
    body: TriggerLiveRunRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
) -> dict:
    """Collect live assets via Steampipe and run the saved signal against each row."""
    db_pool = request.app.state.database_pool
    settings = request.app.state.settings

    async with db_pool.acquire() as conn:
        # Load connector credentials + type
        cred_row = await conn.fetchrow(
            f"""
            SELECT cred.credential_value, ct.connector_type_code
            FROM {SANDBOX_SCHEMA}."20_fct_connector_instances" ci
            JOIN {SANDBOX_SCHEMA}."41_dtl_connector_credentials" cred
                ON cred.connector_instance_id = ci.id
            JOIN {SANDBOX_SCHEMA}."03_dim_connector_types" ct ON ct.id = ci.connector_type_id
            WHERE ci.id = $1 AND ci.is_deleted = FALSE
            ORDER BY cred.created_at DESC
            LIMIT 1
            """,
            body.connector_id,
        )
        if not cred_row:
            raise NotFoundError(
                f"Connector '{body.connector_id}' not found or has no credentials"
            )

        # Load signal python_source
        source_row = await conn.fetchrow(
            f"""
            SELECT property_value AS python_source
            FROM {SANDBOX_15_SCHEMA}."45_dtl_signal_properties"
            WHERE signal_id = $1 AND property_key = 'python_source'
            """,
            body.signal_id,
        )
        if not source_row:
            raise NotFoundError(f"Signal '{body.signal_id}' has no python_source")

        # Load asset_type from signal properties
        asset_type_row = await conn.fetchrow(
            f"""
            SELECT property_value AS asset_type
            FROM {SANDBOX_15_SCHEMA}."45_dtl_signal_properties"
            WHERE signal_id = $1 AND property_key = 'asset_type'
            """,
            body.signal_id,
        )

    python_source = source_row["python_source"]
    asset_type = asset_type_row["asset_type"] if asset_type_row else "github_repo"
    connector_type_code = cred_row["connector_type_code"]

    # Decrypt credentials
    _crypto_module = import_module("backend.10_sandbox.02_connectors.crypto")
    encryption_key = settings.sandbox_encryption_key
    raw_creds_json = _crypto_module.decrypt_credential(
        cred_row["credential_value"], encryption_key
    )
    credentials = json.loads(raw_creds_json)

    asset_cfg = ASSET_TYPE_CONFIG.get(asset_type, ASSET_TYPE_CONFIG["github_repo"])

    # Collect live assets
    _steampipe_module = import_module("backend.10_sandbox.19_steampipe.steampipe")
    substrate = _steampipe_module.SteampipeSubstrate(settings=settings)

    columns = asset_cfg["columns"]
    col_list = ", ".join(columns)
    sql = f"SELECT {col_list} FROM {asset_cfg['table']}"

    asset_rows = await substrate.execute_query(
        sql=sql,
        provider_type=connector_type_code,
        credentials=credentials,
    )

    if not asset_rows:
        return {
            "accuracy": 1.0,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "failed_cases": [],
        }

    # Run signal against each row
    _engine_module = import_module("backend.10_sandbox.07_execution.engine")
    engine = _engine_module.SignalExecutionEngine(timeout_ms=10000, max_memory_mb=128)

    passed = 0
    failed_cases = []

    for i, row in enumerate(asset_rows):
        result = await engine.execute(python_source=python_source, dataset=row)
        actual = result.result_code if result.status == "completed" else "error"
        if actual == "pass":
            passed += 1
        else:
            failed_cases.append(
                {
                    "asset_id": row.get("name", str(i)),
                    "actual_result": actual,
                    "summary": result.result_summary
                    or result.error_message
                    or "Signal failed",
                    "row": row,
                }
            )

    total = len(asset_rows)
    accuracy = passed / total if total > 0 else 1.0

    return {
        "accuracy": accuracy,
        "total": total,
        "passed": passed,
        "failed": len(failed_cases),
        "failed_cases": failed_cases,
    }
