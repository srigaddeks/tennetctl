"""monitoring.logs.otlp_ingest — effect node for OTLP logs ingest.

Hot path: emits_audit=False (same pattern as vault.secrets.get). Just
forwards the body to publish_logs_batch.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.service"
)
_nats_core: Any = import_module("backend.01_core.nats")

Node = _catalog_node.Node


class OtlpLogsIngest(Node):
    key = "monitoring.logs.otlp_ingest"
    kind = "request"
    emits_audit = False

    class Input(BaseModel):
        body: bytes
        content_type: str = "application/x-protobuf"

    class Output(BaseModel):
        published: int
        rejected: int

    async def run(self, ctx: Any, inputs: "OtlpLogsIngest.Input") -> "OtlpLogsIngest.Output":
        del ctx
        js = _nats_core.get_js()
        published, rejected = await _service.publish_logs_batch(
            inputs.body, inputs.content_type, js,
        )
        return self.Output(published=published, rejected=rejected)
