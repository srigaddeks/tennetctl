"""
JetStream stream bootstrap for monitoring.

Streams:
- MONITORING_LOGS   — workqueue, 72h retention, 2GB, subjects monitoring.logs.otel.>
- MONITORING_SPANS  — workqueue, 24h retention, 4GB, subjects monitoring.traces.otel.>
- MONITORING_DLQ    — limits, 7d retention, 1GB, subjects monitoring.dlq.>

Idempotent: update_stream() if exists, add_stream() on NotFoundError.
nats-py 2.9+ uses seconds for max_age at the config level; server stores as nanos.
"""

from __future__ import annotations

import logging

from nats.js import JetStreamContext  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
from nats.js.api import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    DiscardPolicy,
    RetentionPolicy,
    StorageType,
    StreamConfig,
)
from nats.js.errors import NotFoundError  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

logger = logging.getLogger("tennetctl.monitoring.jetstream")

_H = 3600  # seconds
_D = 86400

LOGS_STREAM_CONFIG = StreamConfig(
    name="MONITORING_LOGS",
    subjects=["monitoring.logs.otel.>"],
    retention=RetentionPolicy.WORK_QUEUE,
    storage=StorageType.FILE,
    max_age=72 * _H,
    max_bytes=2 * 1024 * 1024 * 1024,
    discard=DiscardPolicy.OLD,
)

SPANS_STREAM_CONFIG = StreamConfig(
    name="MONITORING_SPANS",
    subjects=["monitoring.traces.otel.>"],
    retention=RetentionPolicy.WORK_QUEUE,
    storage=StorageType.FILE,
    max_age=24 * _H,
    max_bytes=4 * 1024 * 1024 * 1024,
    discard=DiscardPolicy.OLD,
)

DLQ_STREAM_CONFIG = StreamConfig(
    name="MONITORING_DLQ",
    subjects=["monitoring.dlq.>"],
    retention=RetentionPolicy.LIMITS,
    storage=StorageType.FILE,
    max_age=7 * _D,
    max_bytes=1 * 1024 * 1024 * 1024,
    discard=DiscardPolicy.OLD,
)

ALL_STREAMS = (LOGS_STREAM_CONFIG, SPANS_STREAM_CONFIG, DLQ_STREAM_CONFIG)


async def bootstrap_monitoring_jetstream(js: JetStreamContext) -> None:
    """Create or update all monitoring streams idempotently."""
    for cfg in ALL_STREAMS:
        try:
            await js.update_stream(config=cfg)
            logger.info("jetstream stream updated: %s", cfg.name)
        except NotFoundError:
            await js.add_stream(config=cfg)
            logger.info("jetstream stream created: %s", cfg.name)
