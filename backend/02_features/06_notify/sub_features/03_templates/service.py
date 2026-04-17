"""Service layer for notify.templates."""

from __future__ import annotations

import email.message
from importlib import import_module
from typing import Any

import aiosmtplib
import jinja2

_repo: Any = import_module("backend.02_features.06_notify.sub_features.03_templates.repository")
_group_repo: Any = import_module("backend.02_features.06_notify.sub_features.02_template_groups.repository")
_smtp_repo: Any = import_module("backend.02_features.06_notify.sub_features.01_smtp_configs.repository")
_var_service: Any = import_module("backend.02_features.06_notify.sub_features.04_variables.service")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")

_jinja_env = jinja2.Environment(undefined=jinja2.Undefined, autoescape=False)


async def list_templates(conn: Any, *, org_id: str) -> list[dict]:
    return await _repo.list_templates(conn, org_id=org_id)


async def get_template(conn: Any, *, template_id: str) -> dict | None:
    return await _repo.get_template(conn, template_id=template_id)


async def get_template_by_key(conn: Any, *, org_id: str, key: str) -> dict | None:
    return await _repo.get_template_by_key(conn, org_id=org_id, key=key)


async def create_template(conn: Any, pool: Any, ctx: Any, *, data: dict) -> dict:
    template_id = _core_id.uuid7()
    await _repo.create_template(
        conn,
        template_id=template_id,
        org_id=data["org_id"],
        key=data["key"],
        group_id=data["group_id"],
        subject=data["subject"],
        reply_to=data.get("reply_to"),
        priority_id=data.get("priority_id", 2),
        created_by=ctx.user_id or "system",
    )
    # Upsert bodies if provided
    if data.get("bodies"):
        await _repo.upsert_bodies(
            conn,
            template_id=template_id,
            body_id_fn=_core_id.uuid7,
            bodies=data["bodies"],
        )
    row = await _repo.get_template(conn, template_id=template_id)
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "notify.templates.created", "outcome": "success",
         "metadata": {"template_id": template_id, "key": data["key"]}},
    )
    return row


async def update_template(conn: Any, pool: Any, ctx: Any, *, template_id: str, data: dict) -> dict | None:
    row = await _repo.update_template(
        conn, template_id=template_id, updated_by=ctx.user_id or "system", **data,
    )
    if row:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.templates.updated", "outcome": "success",
             "metadata": {"template_id": template_id}},
        )
    return row


async def upsert_bodies(conn: Any, pool: Any, ctx: Any, *, template_id: str, bodies: list[dict]) -> dict | None:
    template = await _repo.get_template(conn, template_id=template_id)
    if template is None:
        return None
    await _repo.upsert_bodies(
        conn,
        template_id=template_id,
        body_id_fn=_core_id.uuid7,
        bodies=bodies,
    )
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "notify.templates.bodies_updated", "outcome": "success",
         "metadata": {"template_id": template_id}},
    )
    return await _repo.get_template(conn, template_id=template_id)


async def delete_template(conn: Any, pool: Any, ctx: Any, *, template_id: str) -> bool:
    deleted = await _repo.delete_template(
        conn, template_id=template_id, updated_by=ctx.user_id or "system"
    )
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.templates.deleted", "outcome": "success",
             "metadata": {"template_id": template_id}},
        )
    return deleted


async def send_test_email(
    conn: Any,
    *,
    template_id: str,
    to_email: str,
    context: dict,
    vault: Any,
) -> str:
    template = await _repo.get_template(conn, template_id=template_id)
    if template is None:
        from importlib import import_module as _im
        _errors = _im("backend.01_core.errors")
        raise _errors.NotFoundError(f"template {template_id!r} not found")

    email_body = next(
        (b for b in (template.get("bodies") or []) if b["channel_id"] == 1),
        None,
    )
    if email_body is None:
        from importlib import import_module as _im
        _errors = _im("backend.01_core.errors")
        raise _errors.AppError("NO_EMAIL_BODY", "Template has no email body.", 422)

    group = await _group_repo.get_template_group(conn, group_id=template["group_id"])
    if group is None or not group.get("smtp_config_id"):
        from importlib import import_module as _im
        _errors = _im("backend.01_core.errors")
        raise _errors.AppError("NO_SMTP_CONFIG", "Template group has no SMTP config.", 422)

    smtp_config = await _smtp_repo.get_smtp_config(conn, config_id=group["smtp_config_id"])
    if smtp_config is None:
        from importlib import import_module as _im
        _errors = _im("backend.01_core.errors")
        raise _errors.AppError("NO_SMTP_CONFIG", "SMTP config not found.", 422)

    smtp_password = await vault.get(smtp_config["auth_vault_key"])

    resolved = await _var_service.resolve_variables(conn, template_id=template_id, context=context)

    rendered_subject = _jinja_env.from_string(template["subject"]).render(**resolved)
    rendered_html = _jinja_env.from_string(email_body["body_html"]).render(**resolved)
    rendered_text: str | None = None
    if email_body.get("body_text"):
        rendered_text = _jinja_env.from_string(email_body["body_text"]).render(**resolved)

    msg = email.message.EmailMessage()
    msg["From"] = smtp_config["username"]
    msg["To"] = to_email
    msg["Subject"] = rendered_subject
    if template.get("reply_to"):
        msg["Reply-To"] = template["reply_to"]
    msg.set_content(rendered_text or "")
    msg.add_alternative(rendered_html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=smtp_config["host"],
        port=smtp_config["port"],
        username=smtp_config["username"],
        password=smtp_password,
        use_tls=smtp_config["tls"],
        validate_certs=False,
    )
    return to_email
