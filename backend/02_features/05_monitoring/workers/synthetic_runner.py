"""Synthetic check runner — periodically fetches each active check's target URL.

Emits metrics:
  - monitoring.synthetic.up (gauge: 1/0)
  - monitoring.synthetic.duration_ms (histogram)

Updates dtl_monitoring_synthetic_state every run. On 3rd consecutive failure
emits audit event ``monitoring.synthetic.down``.

Every 30s the runner reloads the list of active checks. Each check runs on its
own asyncio.Task at its own ``interval_seconds``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from importlib import import_module
from typing import Any
from urllib.parse import urlparse

import httpx

_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_sdk: Any = import_module("backend.02_features.05_monitoring.sdk")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.repository"
)

logger = logging.getLogger("tennetctl.monitoring.synthetic_runner")


_DURATION_BUCKETS = [10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0]


def _evaluate_assertions(
    assertions: list[dict[str, Any]],
    *,
    status_code: int,
    body_text: str,
) -> tuple[bool, str | None]:
    """Returns (ok, err_msg)."""
    for a in assertions or []:
        op = a.get("op")
        field = a.get("field")
        value = a.get("value")
        if value is None:
            continue
        str_value = str(value)
        if op == "contains" and field == "body":
            if str_value not in body_text:
                return False, f"assertion failed: body does not contain {str_value!r}"
        elif op == "equals" and field == "status":
            try:
                iv = int(str_value)
            except (TypeError, ValueError):
                return False, f"assertion failed: non-integer status value {str_value!r}"
            if int(status_code) != iv:
                return False, f"assertion failed: status {status_code} != {iv}"
        elif op == "not_contains" and field == "body":
            if str_value in body_text:
                return False, f"assertion failed: body contains {str_value!r}"
    return True, None


class SyntheticRunner:
    def __init__(self, pool: Any) -> None:
        self._pool = pool
        self._task: asyncio.Task[None] | None = None
        self._per_check: dict[str, asyncio.Task[None]] = {}
        self._stopped = False
        self.heartbeat_at: datetime | None = None
        # Handles are SDK-level (org_id is taken from ctx at call time).
        self._gauge_up = _sdk.metrics.gauge(
            "monitoring.synthetic.up",
            labels=["check_name", "target_host"],
            description="Synthetic check up/down (1/0).",
            unit="1",
            max_cardinality=10000,
        )
        self._hist_dur = _sdk.metrics.histogram(
            "monitoring.synthetic.duration_ms",
            labels=["check_name", "target_host"],
            description="Synthetic check HTTP duration in ms.",
            unit="ms",
            buckets=_DURATION_BUCKETS,
            max_cardinality=10000,
        )

    def _ctx(self, org_id: str) -> Any:
        return _catalog_ctx.NodeContext(
            user_id=None,
            session_id=None,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(),
            audit_category="system",
            extras={"pool": self._pool},
        )

    async def _run_single(self, check: dict[str, Any]) -> None:
        check_id = check["id"]
        org_id = check["org_id"]
        name = check["name"]
        url = check["target_url"]
        host = urlparse(url).hostname or ""
        timeout_s = max(0.1, (check["timeout_ms"] or 5000) / 1000.0)
        method = (check["method"] or "GET").upper()
        expected_status = check["expected_status"]
        assertions = check.get("assertions") or []
        import json as _json
        if isinstance(assertions, str):
            try:
                assertions = _json.loads(assertions)
            except Exception:  # noqa: BLE001
                assertions = []
        headers = check.get("headers") or {}
        if isinstance(headers, str):
            try:
                headers = _json.loads(headers)
            except Exception:  # noqa: BLE001
                headers = {}
        body = check.get("body")

        t0 = time.perf_counter()
        status_code: int | None = None
        err: str | None = None
        ok = False
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.request(method=method, url=url, headers=headers, content=body)
                status_code = int(resp.status_code)
                body_text = resp.text
            if status_code != int(expected_status):
                err = f"unexpected status {status_code} (expected {expected_status})"
            else:
                asserts_ok, assert_err = _evaluate_assertions(
                    assertions, status_code=status_code, body_text=body_text,
                )
                if not asserts_ok:
                    err = assert_err
                else:
                    ok = True
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            err = repr(e)

        duration_ms = int((time.perf_counter() - t0) * 1000)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        labels = {"check_name": name, "target_host": host}
        ctx = self._ctx(org_id)

        try:
            await self._gauge_up.set(ctx, value=1.0 if ok else 0.0, labels=labels)
            await self._hist_dur.observe(ctx, value=float(duration_ms), labels=labels)
        except Exception as e:  # noqa: BLE001
            logger.warning("emit metrics for check %s failed: %r", name, e)

        # Update state + possibly emit down audit.
        prev_failures = 0
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT consecutive_failures FROM "05_monitoring"."20_dtl_monitoring_synthetic_state" '
                'WHERE check_id = $1',
                check_id,
            )
            if row:
                prev_failures = row["consecutive_failures"]
            new_failures = 0 if ok else prev_failures + 1
            await _repo.upsert_state(
                conn,
                check_id=check_id,
                consecutive_failures=new_failures,
                last_ok_at=now if ok else None,
                last_fail_at=None if ok else now,
                last_run_at=now,
                last_status_code=status_code,
                last_duration_ms=duration_ms,
                last_error=err,
            )

        if not ok and prev_failures + 1 >= 3 and new_failures == prev_failures + 1:
            # crossed the 3-strike threshold (only emit on the exact transition)
            if prev_failures + 1 == 3:
                try:
                    await _catalog.run_node(
                        self._pool, "audit.events.emit", ctx,
                        {
                            "event_key": "monitoring.synthetic.down",
                            "outcome": "failure",
                            "metadata": {
                                "check_id": check_id,
                                "name": name,
                                "target_url": url,
                                "error": err,
                                "consecutive_failures": new_failures,
                            },
                        },
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning("audit emit failed for check %s: %r", name, e)

    async def _per_check_loop(self, initial: dict[str, Any]) -> None:
        check = initial
        interval = max(30, int(check["interval_seconds"] or 60))
        # Stagger by name hash so checks don't all fire at the same instant.
        stagger = (hash(check["id"]) % interval)
        try:
            await asyncio.sleep(stagger)
        except asyncio.CancelledError:
            return
        while not self._stopped:
            try:
                # refresh check row to pick up mutations
                async with self._pool.acquire() as conn:
                    row = await _repo.get_by_id(conn, id=check["id"])
                if row is None or not row.get("is_active"):
                    return
                check = row
                interval = max(30, int(check["interval_seconds"] or 60))
                await self._run_single(check)
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("synthetic check %s loop error: %r", check.get("name"), e)
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                return

    async def _reload_loop(self) -> None:
        while not self._stopped:
            try:
                async with self._pool.acquire() as conn:
                    rows = await _repo.list_all_active(conn)
                current_ids = {r["id"] for r in rows}

                # Spawn tasks for new checks
                for r in rows:
                    if r["id"] not in self._per_check:
                        t = asyncio.create_task(
                            self._per_check_loop(r),
                            name=f"monitoring.synthetic.{r['name']}",
                        )
                        self._per_check[r["id"]] = t

                # Cancel tasks for removed/deactivated checks
                for cid in list(self._per_check.keys()):
                    if cid not in current_ids:
                        t = self._per_check.pop(cid)
                        t.cancel()

                self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("synthetic reload loop error: %r", e)
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                return

    async def start(self) -> None:
        self._stopped = False
        self._task = asyncio.create_task(self._reload_loop(), name="monitoring.synthetic_runner")
        logger.info("synthetic runner started")
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        self._stopped = True
        for t in self._per_check.values():
            t.cancel()
        self._per_check.clear()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except Exception:  # noqa: BLE001
                pass
            self._task = None
