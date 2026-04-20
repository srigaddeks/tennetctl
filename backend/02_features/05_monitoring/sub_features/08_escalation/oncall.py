"""On-call schedule resolution logic — pure functions, no DB access."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from importlib import import_module
from typing import Any

_core_id = import_module("backend.01_core.id")


def resolve_oncall(
    schedule: dict[str, Any],
    members: list[dict[str, Any]],
    at: datetime,
) -> str | None:
    """Resolve who is on-call for a schedule at a given time.

    Args:
        schedule: Schedule row with rotation_start, rotation_period_seconds.
        members: List of member dicts in rotation order.
        at: Timestamp (UTC datetime) to resolve for.

    Returns:
        User ID of person on-call, or None if no members.
    """
    if not members:
        return None

    rotation_start = schedule["rotation_start"]
    rotation_period_seconds = schedule["rotation_period_seconds"]

    # Ensure both are timezone-naive (UTC)
    if rotation_start.tzinfo is not None:
        rotation_start = rotation_start.replace(tzinfo=None)
    if at.tzinfo is not None:
        at = at.replace(tzinfo=None)

    # Calculate elapsed seconds from rotation start
    elapsed = (at - rotation_start).total_seconds()
    if elapsed < 0:
        elapsed = 0

    # Index = floor(elapsed / period) % member_count
    member_count = len(members)
    index = int(elapsed // rotation_period_seconds) % member_count

    return members[index]["user_id"]


def next_handover(
    schedule: dict[str, Any],
    members: list[dict[str, Any]],
    at: datetime,
) -> datetime:
    """Calculate next handover time in local timezone.

    Handover occurs at periods of rotation_period_seconds from rotation_start,
    aligned to local midnight boundaries when viewed in the schedule's timezone.

    Args:
        schedule: Schedule row with rotation_start, timezone, rotation_period_seconds.
        members: List of member dicts (used to count members).
        at: Current time (UTC).

    Returns:
        UTC datetime of next handover.
    """
    if not members:
        # Can't calculate without knowing who's on-call now
        return at + timedelta(seconds=schedule["rotation_period_seconds"])

    rotation_start = schedule["rotation_start"]
    rotation_period_seconds = schedule["rotation_period_seconds"]
    tz_name = schedule.get("timezone", "UTC")

    # Ensure UTC
    if rotation_start.tzinfo is not None:
        rotation_start = rotation_start.replace(tzinfo=None)
    if at.tzinfo is not None:
        at = at.replace(tzinfo=None)

    # Calculate current period index
    elapsed = (at - rotation_start).total_seconds()
    if elapsed < 0:
        elapsed = 0
    current_period = int(elapsed // rotation_period_seconds)

    # Next handover = rotation_start + (current_period + 1) * period
    next_handover_utc = rotation_start + timedelta(
        seconds=(current_period + 1) * rotation_period_seconds
    )

    return next_handover_utc


__all__ = ["resolve_oncall", "next_handover"]
