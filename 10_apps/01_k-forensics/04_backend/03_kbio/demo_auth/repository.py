"""kbio demo auth repository.

Reads from kdemo.v_users (safe view — no hashes).
Writes to kdemo.fct_users and kdemo.dtl_security_questions.
No business logic here.
"""
from __future__ import annotations

import uuid
from typing import Any

import asyncpg


async def get_user_by_username(conn: asyncpg.Connection, username: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT * FROM kdemo.v_users WHERE username = $1",
        username,
    )
    return dict(row) if row else None


async def get_user_credentials(conn: asyncpg.Connection, username: str) -> dict[str, Any] | None:
    """Return password_hash and status for login — reads fct_users directly."""
    row = await conn.fetchrow(
        """
        SELECT u.id, u.username, u.email, u.password_hash, s.code AS status
        FROM kdemo.fct_users u
        JOIN kdemo.dim_user_statuses s ON s.id = u.status_id
        WHERE u.username = $1 AND u.deleted_at IS NULL
        """,
        username,
    )
    return dict(row) if row else None


async def create_user(
    conn: asyncpg.Connection,
    *,
    username: str,
    email: str,
    password_hash: str,
    phone_number: str | None,
    mpin_hash: str | None,
) -> str:
    """Insert into kdemo.fct_users, return new user UUID."""
    user_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO kdemo.fct_users
            (id, username, email, password_hash, phone_number, mpin_hash,
             status_id, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        user_id,
        username,
        email,
        password_hash,
        phone_number,
        mpin_hash,
    )
    return user_id


async def insert_security_question(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    position: int,
    question: str,
    answer_hash: str,
) -> None:
    await conn.execute(
        """
        INSERT INTO kdemo.dtl_security_questions
            (id, user_id, position, question, answer_hash, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, position)
            DO UPDATE SET question = EXCLUDED.question,
                          answer_hash = EXCLUDED.answer_hash,
                          updated_at = CURRENT_TIMESTAMP
        """,
        str(uuid.uuid4()),
        user_id,
        position,
        question,
        answer_hash,
    )
