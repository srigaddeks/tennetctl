"""
UUID v7 generation — the only ID generator in the project.

Never use uuid4(). Never use new_id(). Always uuid7().
"""

from __future__ import annotations

from uuid_utils import uuid7 as _uuid7


def uuid7() -> str:
    """Generate a UUID v7 string."""
    return str(_uuid7())
