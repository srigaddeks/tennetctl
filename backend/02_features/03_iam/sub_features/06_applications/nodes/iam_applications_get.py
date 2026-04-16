"""iam.applications.get — control node."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from pydantic import BaseModel, ConfigDict

_node_mod: Any = import_module("backend.01_catalog.node")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.06_applications.service"
)


class ApplicationsGet(_node_mod.Node):
    key = "iam.applications.get"
    kind = "control"

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        id: str

    class Output(BaseModel):
        application: dict | None

    async def run(self, ctx: Any, inputs: Input) -> "ApplicationsGet.Output":
        a = await _service.get_application(ctx.conn, ctx, application_id=inputs.id)
        return self.Output(application=a)
