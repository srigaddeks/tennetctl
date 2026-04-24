"""Delivery runs service — orchestrates repo + audit.

Audit keys:
  - somaerp.delivery.runs.created / .started / .completed / .cancelled / .deleted
  - somaerp.delivery.stops.generated / .delivered / .missed / .rescheduled / .cancelled
"""

from __future__ import annotations

from datetime import date
from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.95_delivery_runs.repository",
)
_errors = import_module("apps.somaerp.backend.01_core.errors")


def _scope(
    *, actor_user_id: str | None, session_id: str | None,
    org_id: str | None, tenant_id: str,
) -> dict:
    return {
        "user_id": actor_user_id,
        "session_id": session_id,
        "org_id": org_id,
        "workspace_id": tenant_id,
    }


# ── Runs ─────────────────────────────────────────────────────────────


async def list_runs(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_runs(conn, **kwargs)


async def get_run_detail(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict:
    run = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if run is None:
        raise _errors.NotFoundError(f"Run {run_id} not found.")
    stops = await _repo.list_stops(conn, tenant_id=tenant_id, run_id=run_id)
    return {"run": run, "stops": stops}


async def get_run(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict:
    row = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if row is None:
        raise _errors.NotFoundError(f"Run {run_id} not found.")
    return row


async def create_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.route_exists_active(
        conn, tenant_id=tenant_id, route_id=data["route_id"],
    ):
        raise _errors.ValidationError(
            f"Route {data['route_id']} not found for this tenant.",
            code="INVALID_ROUTE",
        )
    if not await _repo.rider_exists_active(
        conn, tenant_id=tenant_id, rider_id=data["rider_id"],
    ):
        raise _errors.ValidationError(
            f"Rider {data['rider_id']} not found for this tenant.",
            code="INVALID_RIDER",
        )
    # Uniqueness: one active (non-cancelled) run per route+date.
    existing_active = await _repo.get_active_run_for_date(
        conn,
        tenant_id=tenant_id,
        route_id=data["route_id"],
        run_date_val=data["run_date"],
    )
    if existing_active is not None:
        raise _errors.ValidationError(
            f"An active run already exists for route+date (run_id="
            f"{existing_active['id']}).",
            code="RUN_ALREADY_EXISTS",
            status_code=409,
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_run(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.runs.created",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "delivery.run",
                "route_id": str(data["route_id"]),
                "rider_id": str(data["rider_id"]),
                "run_date": str(data["run_date"]),
            },
        },
    )
    return row


async def patch_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_run(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Run {run_id} not found.")

    if patch.get("rider_id"):
        if not await _repo.rider_exists_active(
            conn, tenant_id=tenant_id, rider_id=patch["rider_id"],
        ):
            raise _errors.ValidationError(
                f"Rider {patch['rider_id']} not found for this tenant.",
                code="INVALID_RIDER",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row, event_kind = await _repo.patch_run(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        existing=existing,
        patch=patch,
    )

    event_map = {
        "updated":   "somaerp.delivery.runs.updated",
        "started":   "somaerp.delivery.runs.started",
        "completed": "somaerp.delivery.runs.completed",
        "cancelled": "somaerp.delivery.runs.cancelled",
    }
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(run_id),
        "entity_kind": "delivery.run",
    }
    if event_kind != "updated":
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = patch.get("status")
    else:
        metadata["changed_fields"] = sorted(
            [k for k, v in patch.items() if v is not None],
        )

    await tennetctl.audit_emit(
        event_key=event_map[event_kind],
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={"outcome": "success", "metadata": metadata},
    )
    return row


async def soft_delete_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
) -> None:
    existing = await _repo.get_run(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Run {run_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_run(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run_id=run_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Run {run_id} not found.")
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.runs.deleted",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(run_id),
                "entity_kind": "delivery.run",
            },
        },
    )


# ── Stops ───────────────────────────────────────────────────────────


async def _require_run(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict:
    row = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if row is None:
        raise _errors.NotFoundError(f"Run {run_id} not found.")
    return row


async def generate_stops(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
) -> dict:
    run = await _require_run(conn, tenant_id=tenant_id, run_id=run_id)
    if run["status"] != "planned":
        raise _errors.ValidationError(
            f"Cannot generate stops for run in status={run['status']}.",
            code="INVALID_RUN_STATUS",
        )
    if int(run.get("total_stops") or 0) > 0:
        raise _errors.ValidationError(
            "Stops already generated for this run.",
            code="STOPS_ALREADY_GENERATED",
            status_code=409,
        )
    route = await _repo.get_route_raw(
        conn, tenant_id=tenant_id, route_id=run["route_id"],
    )
    if route is None:
        raise _errors.ValidationError(
            f"Route {run['route_id']} not found.",
            code="INVALID_ROUTE",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    count = await _repo.generate_stops(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run_row=run,
        route_row=route,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.stops.generated",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_kind": "delivery.stop",
                "run_id": str(run_id),
                "route_id": str(run["route_id"]),
                "count": count,
            },
        },
    )
    updated = await _repo.get_run(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    stops = await _repo.list_stops(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    return {"run": updated, "stops": stops, "count": count}


async def list_stops(
    conn: Any, *, tenant_id: str, run_id: str,
) -> list[dict]:
    await _require_run(conn, tenant_id=tenant_id, run_id=run_id)
    return await _repo.list_stops(
        conn, tenant_id=tenant_id, run_id=run_id,
    )


async def patch_stop(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    stop_id: str,
    patch: dict,
) -> dict:
    await _require_run(conn, tenant_id=tenant_id, run_id=run_id)
    stop = await _repo.get_stop(
        conn, tenant_id=tenant_id, run_id=run_id, stop_id=stop_id,
    )
    if stop is None:
        raise _errors.NotFoundError(f"Stop {stop_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row, event_kind = await _repo.patch_stop(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run_id=run_id,
        existing_stop=stop,
        patch=patch,
    )

    if event_kind is not None:
        await tennetctl.audit_emit(
            event_key=f"somaerp.delivery.stops.{event_kind}",
            scope=_scope(
                actor_user_id=actor_user_id,
                session_id=session_id,
                org_id=org_id,
                tenant_id=tenant_id,
            ),
            payload={
                "outcome": "success",
                "metadata": {
                    "category": "setup" if is_setup else "operational",
                    "entity_id": str(stop_id),
                    "entity_kind": "delivery.stop",
                    "run_id": str(run_id),
                    "customer_id": str(stop["customer_id"]),
                    "sequence_position": int(stop["sequence_position"]),
                    "previous_status": stop["status"],
                    "new_status": patch.get("status"),
                },
            },
        )

    return row


# ── Board ────────────────────────────────────────────────────────────


async def get_board(
    conn: Any, *, tenant_id: str, on_date: date,
) -> dict:
    return await _repo.get_board(
        conn, tenant_id=tenant_id, on_date=on_date,
    )
