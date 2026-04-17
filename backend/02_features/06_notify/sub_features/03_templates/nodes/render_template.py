"""
notify.templates.render — Jinja2 StrictUndefined template rendering node.

Control node (tx=caller). Fetches template + body for requested channel
from the DB, resolves registered variables (static + dynamic SQL), then
renders subject + body with the merged variable dict.

Variable resolution order (last wins):
  1. Registered static variables (stored in fct_notify_template_variables)
  2. Registered dynamic_sql variables (safelisted SELECT, parameterized from context)
  3. Caller-supplied variables (inputs.variables) — always wins

Raises:
  ValueError — template_key not found, channel body not found, or dynamic SQL fails
  jinja2.UndefinedError — required variable missing from merged dict (StrictUndefined)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import jinja2
from pydantic import BaseModel

_catalog_node: Any = import_module("backend.01_catalog.node")
_repo: Any = import_module("backend.02_features.06_notify.sub_features.03_templates.repository")
_var_repo: Any = import_module("backend.02_features.06_notify.sub_features.04_variables.repository")

Node = _catalog_node.Node

_env = jinja2.Environment(
    undefined=jinja2.StrictUndefined,
    autoescape=False,  # caller is responsible for HTML safety in stored templates
)

_CHANNEL_CODE_TO_ID = {"email": 1, "webpush": 2, "in_app": 3, "sms": 4}


class RenderTemplate(Node):
    key = "notify.templates.render"
    kind = "control"
    config_schema: dict = {}
    input_schema: dict = {
        "type": "object",
        "required": ["template_key", "org_id", "channel"],
        "properties": {
            "template_key": {"type": "string"},
            "org_id": {"type": "string"},
            "channel": {"type": "string", "enum": ["email", "webpush", "in_app", "sms"]},
            "variables": {"type": "object"},
            "context": {
                "type": "object",
                "description": "Audit event context for dynamic SQL resolution (actor_user_id, org_id, workspace_id, event_metadata)",
            },
        },
    }
    output_schema: dict = {
        "type": "object",
        "properties": {
            "rendered_subject": {"type": "string"},
            "rendered_html": {"type": "string"},
            "rendered_text": {"type": ["string", "null"]},
        },
    }

    class Input(BaseModel):
        template_key: str
        org_id: str
        channel: str  # "email" | "webpush" | "in_app" | "sms"
        variables: dict[str, Any] = {}
        context: dict[str, Any] = {}  # audit event context for dynamic SQL resolution

    class Output(BaseModel):
        rendered_subject: str
        rendered_html: str
        rendered_text: str | None = None

    async def run(self, ctx: Any, inputs: Any) -> "RenderTemplate.Output":
        channel_id = _CHANNEL_CODE_TO_ID.get(inputs.channel)
        if channel_id is None:
            raise ValueError(f"unknown channel {inputs.channel!r}")

        conn = ctx.conn
        template = await _repo.get_template_by_key(conn, org_id=inputs.org_id, key=inputs.template_key)
        if template is None:
            raise ValueError(f"template {inputs.template_key!r} not found for org {inputs.org_id!r}")

        # Find the body for the requested channel
        body_row = next(
            (b for b in (template.get("bodies") or []) if b["channel_id"] == channel_id),
            None,
        )
        if body_row is None:
            raise ValueError(
                f"template {inputs.template_key!r} has no body for channel {inputs.channel!r}"
            )

        # Resolve registered variables (static + dynamic SQL), then merge with caller vars.
        # Caller variables always win — they can override any registered variable.
        registered = await _var_repo.resolve_variables(
            conn,
            template_id=template["id"],
            context=inputs.context,
        )
        merged_vars = {**registered, **inputs.variables}

        rendered_subject = _env.from_string(template["subject"]).render(**merged_vars)
        rendered_html = _env.from_string(body_row["body_html"]).render(**merged_vars)
        rendered_text: str | None = None
        if body_row.get("body_text"):
            rendered_text = _env.from_string(body_row["body_text"]).render(**merged_vars)

        return RenderTemplate.Output(
            rendered_subject=rendered_subject,
            rendered_html=rendered_html,
            rendered_text=rendered_text,
        )
