"""APISIX Prometheus scraper.

Every ``scrape_interval_s`` (default 15s):
1. GET apisix_url → Prometheus text exposition
2. Parse with prometheus_client.parser.text_string_to_metric_families
3. Auto-register each unique metric under key ``apisix.<name>`` (once)
4. Write points via MetricsStore (counter → increment with delta, gauge →
   set_gauge, histogram → observe_histogram) per sample

Scrape failures log a warning and continue — never raise into the supervisor.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import httpx
from prometheus_client.parser import text_string_to_metric_families  # pyright: ignore[reportMissingTypeStubs]

_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")

logger = logging.getLogger("tennetctl.monitoring.apisix_scraper")

_KIND_COUNTER = 1
_KIND_GAUGE = 2
_KIND_HISTOGRAM = 3


class ApisixScraper:
    """Polls APISIX /apisix/prometheus/metrics and writes to MetricsStore."""

    def __init__(
        self,
        pool: Any,
        config: Any,
        org_id: str = "tennetctl",
        scrape_interval_s: float = 15.0,
    ) -> None:
        self._pool = pool
        self._config = config
        self._org_id = org_id
        self._interval = scrape_interval_s
        self._metrics_store = _stores.get_metrics_store(pool)
        self._resources_store = _stores.get_resources_store(pool)
        self._resource_id: int | None = None
        self._metric_ids: dict[tuple[str, int], int] = {}
        self._last_counter_value: dict[tuple[int, str], float] = {}
        self._stop = asyncio.Event()
        self.heartbeat_at: datetime | None = None

    @property
    def url(self) -> str:
        return str(getattr(self._config, "monitoring_apisix_url", ""))

    async def _ensure_resource(self, conn: Any) -> int:
        if self._resource_id is not None:
            return self._resource_id
        rec = _types.ResourceRecord(
            org_id=self._org_id,
            service_name="apisix",
            service_instance_id=os.environ.get("HOSTNAME", "apisix-0"),
            service_version=None,
            attributes={"source": "apisix"},
        )
        rid = await self._resources_store.upsert(conn, rec)
        self._resource_id = int(rid)
        return int(rid)

    async def _register_metric(
        self, conn: Any, name: str, kind_id: int, description: str, label_keys: list[str],
    ) -> int:
        cache_key = (name, kind_id)
        if cache_key in self._metric_ids:
            return self._metric_ids[cache_key]
        metric_def = _types.MetricDef(
            org_id=self._org_id,
            key=f"apisix.{name}",
            kind_id=kind_id,
            label_keys=sorted(set(label_keys)),
            histogram_buckets=[0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0] if kind_id == _KIND_HISTOGRAM else None,
            max_cardinality=10_000,
            description=description or "",
            unit="",
        )
        mid = await self._metrics_store.register(conn, metric_def)
        self._metric_ids[cache_key] = mid
        return mid

    @staticmethod
    def _prom_kind_to_id(prom_type: str) -> int:
        t = (prom_type or "").lower()
        if t == "counter":
            return _KIND_COUNTER
        if t == "gauge":
            return _KIND_GAUGE
        if t in ("histogram", "summary"):
            return _KIND_HISTOGRAM
        return 0

    async def scrape_once(self, client: httpx.AsyncClient) -> int:
        """Single scrape. Returns number of samples written. Never raises."""
        try:
            resp = await client.get(self.url, timeout=10.0)
            if resp.status_code >= 400:
                logger.warning("apisix_scraper: HTTP %d from %s", resp.status_code, self.url)
                return 0
            text = resp.text
        except Exception as e:  # noqa: BLE001
            logger.warning("apisix_scraper: GET failed for %s: %s", self.url, e)
            return 0

        written = 0
        now_ts = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            families = list(text_string_to_metric_families(text))
        except Exception as e:  # noqa: BLE001
            logger.warning("apisix_scraper: parse failed: %s", e)
            return 0

        async with self._pool.acquire() as conn:
            resource_id = await self._ensure_resource(conn)
            for family in families:
                kind_id = self._prom_kind_to_id(family.type)
                if kind_id == 0:
                    continue
                label_keys_seen: set[str] = set()
                for sample in family.samples:
                    label_keys_seen.update(sample.labels.keys())
                metric_id = await self._register_metric(
                    conn, family.name, kind_id, family.documentation or "", sorted(label_keys_seen),
                )
                for sample in family.samples:
                    labels = dict(sample.labels)
                    value = float(sample.value)
                    try:
                        if kind_id == _KIND_COUNTER:
                            label_key = repr(sorted(labels.items()))
                            last = self._last_counter_value.get((metric_id, label_key), 0.0)
                            delta = value - last if value >= last else value
                            self._last_counter_value[(metric_id, label_key)] = value
                            if delta <= 0:
                                continue
                            ok = await self._metrics_store.increment(
                                conn, metric_id, labels, delta,
                                resource_id=resource_id, org_id=self._org_id, recorded_at=now_ts,
                            )
                        elif kind_id == _KIND_GAUGE:
                            ok = await self._metrics_store.set_gauge(
                                conn, metric_id, labels, value,
                                resource_id=resource_id, org_id=self._org_id, recorded_at=now_ts,
                            )
                        else:
                            # histogram — only record sum-like samples
                            if sample.name.endswith("_sum") or sample.name.endswith("_count"):
                                continue
                            ok = await self._metrics_store.observe_histogram(
                                conn, metric_id, labels, value,
                                resource_id=resource_id, org_id=self._org_id, recorded_at=now_ts,
                            )
                        if ok:
                            written += 1
                    except Exception as e:  # noqa: BLE001
                        logger.warning("apisix_scraper: write failed for %s: %s", family.name, e)
        self.heartbeat_at = now_ts
        return written

    async def start(self) -> None:
        async with httpx.AsyncClient() as client:
            while not self._stop.is_set():
                try:
                    await self.scrape_once(client)
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa: BLE001
                    logger.exception("apisix_scraper: unexpected error: %s", e)
                    raise
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
                except asyncio.TimeoutError:
                    continue

    async def stop(self) -> None:
        self._stop.set()


__all__ = ["ApisixScraper"]
