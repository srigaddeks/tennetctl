# LangGraph Infrastructure

**Priority:** P0 — foundation for all pipeline agents
**Status:** Planned
**Dependencies:** `langgraph`, `langchain-core`

---

## Overview

Refactor all pipeline agents from simple for-loops to LangGraph `StateGraph` with typed state, named nodes, conditional edges, and PostgreSQL-backed checkpointing. This enables:

- **Resume on crash** — pick up from last completed node instead of restarting
- **Per-node observability** — LangFuse traces per node
- **Iteration control** — max iterations as graph state, not hardcoded loop
- **Tool use** — future: agent can call tools dynamically

---

## New Module: `backend/20_ai/00_graph_infra/`

```text
__init__.py
base_graph.py      — Base StateGraph builder with common patterns
checkpointer.py    — PostgreSQL-backed checkpointer
tracing.py         — LangFuse callback integration
llm_node.py        — Reusable LLM call node with retry + token tracking
```

---

## Checkpointer

Store graph state in PostgreSQL for resume-on-crash.

### Table: `20_ai.47_fct_graph_checkpoints`

```sql
CREATE TABLE "20_ai"."47_fct_graph_checkpoints" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES "20_ai"."45_fct_job_queue"(id),
    thread_id       VARCHAR(100) NOT NULL,
    node_name       VARCHAR(100) NOT NULL,
    state_json      JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(job_id, thread_id)
);
```

### Checkpointer Implementation

```python
from langgraph.checkpoint.base import BaseCheckpointSaver

class PostgresCheckpointer(BaseCheckpointSaver):
    """Persist LangGraph state to PostgreSQL for crash recovery."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def aget(self, config: dict) -> dict | None:
        """Load last checkpoint for this thread."""
        row = await self._pool.fetchrow(
            'SELECT state_json FROM "20_ai"."47_fct_graph_checkpoints" '
            'WHERE thread_id = $1 ORDER BY created_at DESC LIMIT 1',
            config["configurable"]["thread_id"]
        )
        return row["state_json"] if row else None

    async def aput(self, config: dict, state: dict) -> None:
        """Save checkpoint."""
        await self._pool.execute(
            'INSERT INTO "20_ai"."47_fct_graph_checkpoints" '
            '(job_id, thread_id, node_name, state_json) '
            'VALUES ($1, $2, $3, $4) '
            'ON CONFLICT (job_id, thread_id) DO UPDATE SET '
            'node_name = $3, state_json = $4, created_at = NOW()',
            config["configurable"]["job_id"],
            config["configurable"]["thread_id"],
            state.get("__node__", "unknown"),
            state
        )
```

---

## Base LLM Node

Reusable async LLM call with retry, timeout, and token tracking.

```python
async def llm_complete(
    provider_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.2,
    timeout_seconds: int = 120,
) -> tuple[str, dict]:
    """
    Call LLM via OpenAI-compatible API.
    Returns (content, usage_dict).
    Retries up to 3 times on transient errors (429, 500, 502, 503).
    """
```

---

## LangFuse Tracing

```python
from langfuse.callback import CallbackHandler

def create_langfuse_handler(job_id: str, agent_type: str) -> CallbackHandler | None:
    """Create LangFuse callback if enabled. Returns None if disabled."""
    if not settings.ai_langfuse_enabled:
        return None
    return CallbackHandler(
        trace_name=f"{agent_type}:{job_id}",
        tags=[agent_type],
        metadata={"job_id": job_id}
    )
```

---

## Migration

```sql
-- File: 01_sql_migrations/02_inprogress/20260320_graph-checkpoints.sql

CREATE TABLE IF NOT EXISTS "20_ai"."47_fct_graph_checkpoints" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL,
    thread_id       VARCHAR(100) NOT NULL,
    node_name       VARCHAR(100) NOT NULL,
    state_json      JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(job_id, thread_id)
);

CREATE INDEX idx_graph_checkpoints_job ON "20_ai"."47_fct_graph_checkpoints" (job_id);
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `backend/20_ai/00_graph_infra/__init__.py` | Module init |
| `backend/20_ai/00_graph_infra/base_graph.py` | Graph builder utilities |
| `backend/20_ai/00_graph_infra/checkpointer.py` | PostgresCheckpointer |
| `backend/20_ai/00_graph_infra/tracing.py` | LangFuse integration |
| `backend/20_ai/00_graph_infra/llm_node.py` | Reusable LLM call node |
| `backend/01_sql_migrations/02_inprogress/20260320_graph-checkpoints.sql` | Migration |

## Files to Modify

| File | Change |
|------|--------|
| `backend/00_config/settings.py` | Add `ai_langgraph_max_iterations` (default 10) |
| `backend/20_ai/router.py` | Include `00_graph_infra` if needed |

---

## Verification

1. Import `langgraph` succeeds
2. Create a minimal test graph with 2 nodes, run it, verify checkpoints saved to DB
3. Kill process mid-graph, restart, verify resume from last checkpoint
4. LangFuse traces visible (if enabled)
