"""UUID v7 generator — the only ID generator in somaerp. NEVER uuid4()."""

from __future__ import annotations

from uuid_utils import uuid7 as _uuid7


def uuid7() -> str:
    return str(_uuid7())
