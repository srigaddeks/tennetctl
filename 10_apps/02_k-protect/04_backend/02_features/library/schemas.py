"""kprotect library schemas.

The library is a pass-through proxy to kbio's predefined policy catalog.
Responses are dicts shaped by kbio — no rigid Pydantic model enforced here.
"""

from __future__ import annotations

from pydantic import BaseModel


class LibraryListQuery(BaseModel):
    limit: int = 50
    offset: int = 0
    category: str | None = None
    tag: str | None = None
