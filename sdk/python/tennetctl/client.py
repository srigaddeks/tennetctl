from __future__ import annotations

from typing import Any

import httpx

from ._transport import Transport
from .audit import Audit
from .auth import Auth
from .catalog import Catalog
from .flags import Flags
from .iam import IAM
from .logs import Logs
from .metrics import Metrics
from .notify import Notify
from .traces import Traces
from .vault import Vault


class Tennetctl:
    """Unified client for the TennetCTL platform.

    Modules (v0.2.1): auth, flags, iam, audit, notify.
    Observability (v0.2.2): metrics, logs, traces.
    Platform (v0.2.3): vault, catalog.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        session_token: str | None = None,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
        flags_ttl_seconds: float = 60.0,
    ) -> None:
        self._t = Transport(
            base_url,
            api_key=api_key,
            session_token=session_token,
            timeout=timeout,
            client=client,
        )
        self.auth = Auth(self._t, self)
        self.flags = Flags(self._t, ttl_seconds=flags_ttl_seconds)
        self.iam = IAM(self._t)
        self.audit = Audit(self._t)
        self.notify = Notify(self._t)
        self.metrics = Metrics(self._t)
        self.logs = Logs(self._t)
        self.traces = Traces(self._t)
        self.vault = Vault(self._t)
        self.catalog = Catalog(self._t)

    @property
    def session_token(self) -> str | None:
        return self._t.session_token

    async def close(self) -> None:
        await self._t.close()

    async def __aenter__(self) -> Tennetctl:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()
