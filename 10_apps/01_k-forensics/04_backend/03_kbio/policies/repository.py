"""kbio policies repository.

All reads query v_predefined_policies view in the 10_kbio schema.
Supports paginated list with optional category/tag filters.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def list_policies(
    conn: asyncpg.Connection,
    *,
    limit: int,
    offset: int,
    category: str | None = None,
    tag: str | None = None,
) -> list[dict[str, Any]]:
    """Return a paginated list of predefined policies.

    Optionally filters by category (exact match) and/or tag (substring in
    the tags column, which is stored as a comma-separated string).
    """
    clauses: list[str] = ["is_active = TRUE"]
    params: list[Any] = []

    if category:
        params.append(category)
        clauses.append(f"category = ${len(params)}")

    if tag:
        params.append(f"%{tag}%")
        clauses.append(f"tags ILIKE ${len(params)}")

    where = " AND ".join(clauses)
    params.extend([limit, offset])
    limit_ph = f"${len(params) - 1}"
    offset_ph = f"${len(params)}"

    rows = await conn.fetch(
        f"""SELECT * FROM "10_kbio".v_predefined_policies
            WHERE {where}
            ORDER BY severity DESC, code ASC
            LIMIT {limit_ph} OFFSET {offset_ph}""",
        *params,
    )
    return [dict(r) for r in rows]


async def get_policy_by_code(
    conn: asyncpg.Connection, code: str
) -> dict[str, Any] | None:
    """Fetch a single predefined policy by its unique code.

    Returns None if not found or the policy is inactive.
    """
    row = await conn.fetchrow(
        """SELECT * FROM "10_kbio".v_predefined_policies
           WHERE code = $1 AND is_active = TRUE""",
        code,
    )
    return dict(row) if row else None


async def count_policies(
    conn: asyncpg.Connection,
    *,
    category: str | None = None,
    tag: str | None = None,
) -> int:
    """Return the total count of active policies matching the given filters.

    Used alongside list_policies to build the pagination envelope.
    """
    clauses: list[str] = ["is_active = TRUE"]
    params: list[Any] = []

    if category:
        params.append(category)
        clauses.append(f"category = ${len(params)}")

    if tag:
        params.append(f"%{tag}%")
        clauses.append(f"tags ILIKE ${len(params)}")

    where = " AND ".join(clauses)

    row = await conn.fetchrow(
        f'SELECT COUNT(*) AS n FROM "10_kbio".v_predefined_policies WHERE {where}',
        *params,
    )
    return int(row["n"])
