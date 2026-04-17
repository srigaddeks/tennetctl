"""Resources store Protocol — interns OTel resource identities."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResourcesStore(Protocol):
    async def upsert(self, conn: Any, record: Any) -> int: ...
