"""
iam.dsar.export.request — effect node.

Thin catalog-exposed wrapper around service.create_export_request. Delegates all
validation + audit emission to the service; declared emits_audit=true so the
catalog's effect-must-emit-audit triple-defense stays honest.

Transaction mode: caller — runs on the caller's conn so the fct_dsar_jobs INSERT
and the downstream audit emission commit atomically.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_dsar.service"
)


class DsarExportRequest(_node_mod.Node):
    key = "iam.dsar.export.request"
    kind = "effect"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        subject_user_id: str
        org_id: str

    class Output(BaseModel):
        job: dict

    async def run(self, ctx: Any, inputs: "DsarExportRequest.Input") -> "DsarExportRequest.Output":
        pool = ctx.pool or (ctx.extras.get("pool") if ctx.extras else None)
        if pool is None:
            raise RuntimeError(
                "NodeContext.pool required for iam.dsar.export.request "
                "(service emits audit via run_node which needs the pool)."
            )
        job = await _service.create_export_request(
            pool,
            ctx.conn,
            ctx,
            subject_user_id=inputs.subject_user_id,
            org_id=inputs.org_id,
        )
        return self.Output(job=job)
