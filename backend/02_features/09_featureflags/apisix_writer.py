"""
featureflags.apisix_writer — publish compiled APISIX config.

Two publishing paths:

  1. **YAML file** (primary, for APISIX `config_provider: yaml` mode) —
     writes a complete `apisix.yaml` to a configurable path. APISIX polls
     this file every ~1s and hot-reloads routes/plugins on change.

  2. **Admin API PUT** (secondary, for APISIX with etcd backend) — sends
     each compiled route to the APISIX Admin API. Used opportunistically;
     failures degrade to YAML-only.

Both paths are idempotent. The worker computes a content hash and skips
I/O when the compilation is unchanged.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from . import apisix_sync

logger = logging.getLogger("tennetctl.featureflags.apisix_writer")


# ---------------------------------------------------------------- config


DEFAULT_YAML_PATH = "/tmp/tennetctl_apisix.yaml"
DEFAULT_ADMIN_URL = "http://localhost:51718/apisix/admin"
DEFAULT_ADMIN_KEY = os.environ.get("APISIX_ADMIN_KEY", "")


@dataclass
class ApisixWriterConfig:
    yaml_path: str = DEFAULT_YAML_PATH
    admin_url: str = DEFAULT_ADMIN_URL
    admin_key: str = DEFAULT_ADMIN_KEY
    admin_enabled: bool = False  # default off; YAML-mode APISIX ignores Admin API

    @classmethod
    def from_env(cls) -> ApisixWriterConfig:
        return cls(
            yaml_path=os.environ.get("APISIX_YAML_PATH", DEFAULT_YAML_PATH),
            admin_url=os.environ.get("APISIX_ADMIN_URL", DEFAULT_ADMIN_URL),
            admin_key=os.environ.get("APISIX_ADMIN_KEY", DEFAULT_ADMIN_KEY),
            admin_enabled=os.environ.get("APISIX_ADMIN_ENABLED", "").lower()
            in ("true", "1", "yes"),
        )


# ---------------------------------------------------------------- YAML writer


def build_apisix_yaml(configs: list[dict]) -> str:
    """Build the `apisix.yaml` body from compiled flag configs.

    Schema mirrors APISIX `standalone` mode — a top-level `routes` list with
    `#END` sentinel at the bottom (required by APISIX parser).
    """
    import yaml as _yaml  # lazy import — pyyaml already a transitive dep

    routes = []
    for cfg in configs:
        route = {
            "id": cfg["id"],
            "uri": cfg["uri"],
            "methods": ["GET", "POST"],
            "plugins": cfg.get("plugins", {}),
        }
        routes.append(route)

    doc = {"routes": routes}
    body = _yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)
    return body + "#END\n"


def digest(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def write_yaml(body: str, path: str | Path) -> bool:
    """Write the APISIX YAML atomically. Returns True iff file content changed.

    Atomicity: write to `<path>.tmp` then rename, so APISIX never reads a
    partially-written file during its reload poll.
    """
    p = Path(path)
    new_digest = digest(body)

    if p.exists():
        existing = p.read_text()
        if digest(existing) == new_digest:
            return False  # unchanged — skip write

    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(body)
    tmp.replace(p)
    return True


# ---------------------------------------------------------------- admin API writer


async def put_admin_routes(
    configs: list[dict],
    *,
    admin_url: str,
    admin_key: str,
    timeout: float = 5.0,
) -> tuple[int, int]:
    """PUT each config to APISIX Admin API. Returns (succeeded, failed).

    Used only when running against an etcd-backed APISIX. When APISIX is in
    YAML config mode, Admin API writes are ignored (or return 404). The
    worker treats success/failure counts as advisory.
    """
    if not admin_key:
        logger.debug("apisix admin PUT skipped: no admin key configured")
        return (0, 0)

    headers = {"X-API-KEY": admin_key, "Content-Type": "application/json"}
    succeeded = 0
    failed = 0

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as http:
        for cfg in configs:
            route_id = cfg["id"]
            url = f"{admin_url.rstrip('/')}/routes/{route_id}"
            try:
                r = await http.put(url, json={
                    "uri": cfg["uri"],
                    "methods": ["GET", "POST"],
                    "plugins": cfg.get("plugins", {}),
                })
                if 200 <= r.status_code < 300:
                    succeeded += 1
                else:
                    failed += 1
                    logger.debug(
                        "apisix admin PUT %s → %d: %s",
                        route_id, r.status_code, r.text[:200],
                    )
            except httpx.HTTPError as exc:
                failed += 1
                logger.debug("apisix admin PUT %s failed: %s", route_id, exc)

    return succeeded, failed


# ---------------------------------------------------------------- publish entrypoint


@dataclass
class PublishResult:
    configs_compiled: int
    yaml_written: bool
    yaml_path: str
    admin_succeeded: int
    admin_failed: int
    content_digest: str
    error: str | None = None


async def publish(
    conn: Any,
    *,
    writer_config: ApisixWriterConfig | None = None,
) -> PublishResult:
    """Compile current flag state and publish to APISIX.

    Call path:
    1. Compile all `kind=request` flags via `apisix_sync.compile_all_request_flags`.
    2. Build YAML body; write iff content changed.
    3. If Admin API enabled, PUT each route (best-effort).
    4. Return `PublishResult` with before/after state.

    Errors in compilation are fatal; errors in individual Admin API PUTs are
    counted in `admin_failed` but not raised.
    """
    cfg = writer_config or ApisixWriterConfig.from_env()

    try:
        configs = await apisix_sync.compile_all_request_flags(conn)
    except Exception as exc:  # noqa: BLE001 — compilation is best-effort
        return PublishResult(
            configs_compiled=0,
            yaml_written=False,
            yaml_path=cfg.yaml_path,
            admin_succeeded=0,
            admin_failed=0,
            content_digest="",
            error=f"compile_failed: {exc}",
        )

    body = build_apisix_yaml(configs)
    content_digest = digest(body)

    try:
        yaml_written = write_yaml(body, cfg.yaml_path)
    except OSError as exc:
        return PublishResult(
            configs_compiled=len(configs),
            yaml_written=False,
            yaml_path=cfg.yaml_path,
            admin_succeeded=0,
            admin_failed=0,
            content_digest=content_digest,
            error=f"write_failed: {exc}",
        )

    admin_succeeded = 0
    admin_failed = 0
    if cfg.admin_enabled:
        admin_succeeded, admin_failed = await put_admin_routes(
            configs, admin_url=cfg.admin_url, admin_key=cfg.admin_key,
        )

    return PublishResult(
        configs_compiled=len(configs),
        yaml_written=yaml_written,
        yaml_path=cfg.yaml_path,
        admin_succeeded=admin_succeeded,
        admin_failed=admin_failed,
        content_digest=content_digest,
    )


__all__ = [
    "ApisixWriterConfig",
    "PublishResult",
    "build_apisix_yaml",
    "write_yaml",
    "put_admin_routes",
    "publish",
    "digest",
]
