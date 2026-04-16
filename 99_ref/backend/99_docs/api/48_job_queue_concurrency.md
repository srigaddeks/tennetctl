# Per-Type Job Queue Concurrency

**Priority:** P1 — enables reliable 1000+ signal generation
**Status:** Enhancement to existing module
**Module:** `backend/20_ai/15_job_queue/`

---

## Overview

The job queue currently has a single global `max_concurrent=3` semaphore for ALL job types. This means a heavy codegen job blocks a lightweight spec generation. We need per-type concurrency limits so 1000 signals can run cleanly through the pipeline.

---

## Current State

```python
# worker.py
class JobQueueWorker:
    def __init__(self, ...):
        self._sem = asyncio.Semaphore(max_concurrent)  # global: 3
```

All job types compete for the same 3 slots.

---

## Target State

```python
# Per-type semaphores
JOB_TYPE_CONCURRENCY = {
    "signal_test_dataset_gen": 2,   # medium LLM load
    "signal_codegen": 2,            # heavy: LLM + sandbox execution
    "signal_generate": 2,           # heavy: similar to codegen
    "threat_composer": 1,           # needs full signal catalog, sequential
    "library_builder": 1,           # lightweight, sequential is cleaner
    "evidence_check": 2,
    "generate_report": 2,
    "framework_build": 1,
    "framework_apply_changes": 1,
    "framework_gap_analysis": 1,
}

# Also: global max to prevent total overload
GLOBAL_MAX_CONCURRENT = 5
```

---

## Implementation

### Worker Changes (`worker.py`)

```python
class JobQueueWorker:
    def __init__(self, ..., type_concurrency: dict[str, int] | None = None, global_max: int = 5):
        self._global_sem = asyncio.Semaphore(global_max)
        self._type_sems: dict[str, asyncio.Semaphore] = {}
        for job_type, limit in (type_concurrency or JOB_TYPE_CONCURRENCY).items():
            self._type_sems[job_type] = asyncio.Semaphore(limit)

    async def _claim_job(self):
        # Only claim jobs whose per-type semaphore has capacity
        available_types = [t for t, s in self._type_sems.items() if s._value > 0]
        if not available_types:
            return None
        # SELECT ... WHERE job_type = ANY($1) AND status = 'queued'
        # ORDER BY priority, created_at
        # FOR UPDATE SKIP LOCKED LIMIT 1
        job = await self._repository.claim_next(available_types)
        return job

    async def _run_job(self, job):
        type_sem = self._type_sems.get(job.job_type, self._global_sem)
        async with self._global_sem:
            async with type_sem:
                await self._dispatch(job)
```

### Settings (`settings.py`)

```python
ai_job_type_concurrency: str  # JSON dict, env: AI_JOB_TYPE_CONCURRENCY
                               # default: '{"signal_codegen": 2, "threat_composer": 1, ...}'
ai_job_global_max_concurrent: int  # default: 5
```

### Repository Changes (`repository.py`)

Update `claim_next_job()` to accept list of eligible job types:

```sql
SELECT * FROM "20_ai"."45_fct_job_queue"
WHERE status_code = 'queued'
  AND job_type = ANY($1)
ORDER BY priority_code ASC, created_at ASC
FOR UPDATE SKIP LOCKED
LIMIT 1
```

---

## Queue Behavior at Scale

With `signal_codegen: max_parallel=2` and 1000 signals queued:

1. Worker claims 2 codegen jobs, runs them concurrently
2. Remaining 998 stay in `queued` status
3. As each finishes, worker claims next
4. If threat_composer jobs are queued too, they run in their own slot (max 1)
5. Total: at most 5 jobs running simultaneously (global max)
6. Pipeline stays orderly: no resource exhaustion, no LLM rate limit hits

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/20_ai/15_job_queue/worker.py` | Replace single semaphore with per-type + global. Update claim logic. |
| `backend/20_ai/15_job_queue/repository.py` | Update `claim_next_job()` to filter by eligible types. |
| `backend/00_config/settings.py` | Add `ai_job_type_concurrency`, `ai_job_global_max_concurrent`. |

---

## Verification

1. Enqueue 10 codegen jobs → verify only 2 run concurrently
2. Enqueue 5 codegen + 3 threat_composer → verify codegen:2 + threat_composer:1 = 3 concurrent
3. Verify global max: enqueue across all types → never exceed 5 total
4. Verify ordering: jobs processed in priority + FIFO order within each type
