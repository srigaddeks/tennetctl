# 29-01 SUMMARY — Python SDK: flags + iam + audit + notify modules

**Status:** ✅ Complete (2026-04-18)
**Plan:** `.paul/phases/29-sdk-core-flags-iam-audit-notify/29-01-PLAN.md`

## What shipped

Four new capability modules layered on the Transport + error hierarchy from 28-01.

### Public surface (new additions to `tennetctl`)

```python
from tennetctl import Flags, IAM, Audit, AuditEvents, Notify

client = Tennetctl(base_url, api_key=..., flags_ttl_seconds=60.0)

# flags — 60s TTL cache per (key, entity, context)
await client.flags.evaluate("flag-key", entity="user:1", context={"country": "US"})
await client.flags.evaluate_bulk([{"key": "a", "entity": "u"}, ...])
client.flags.clear_cache()
client.flags.invalidate("flag-key")

# iam — read-only
await client.iam.users.list(status="active", limit=50)
await client.iam.users.get("u1")
# same shape for: orgs, workspaces, roles, groups

# audit — query only (emission is backend node — no SDK emit)
await client.audit.events.list(category="iam", limit=100)
await client.audit.events.get("evt-id")
await client.audit.events.stats()
await client.audit.events.tail(category="iam")
await client.audit.events.funnel({"steps": [...]})
await client.audit.events.retention()
await client.audit.events.outbox_cursor()
await client.audit.events.event_keys()

# notify
await client.notify.send(
    template_key="password_reset",
    recipient_user_id="u1",
    variables={"link": "..."},
    channel="email",
    idempotency_key="uuid-123",
)
```

### Endpoints wrapped

| SDK | HTTP |
|---|---|
| `flags.evaluate` | `POST /v1/evaluate` |
| `flags.evaluate_bulk` | `POST /v1/evaluate/bulk` |
| `iam.users.list/get` | `GET /v1/users` / `/{id}` |
| `iam.orgs.list/get` | `GET /v1/orgs` / `/{id}` |
| `iam.workspaces.list/get` | `GET /v1/workspaces` / `/{id}` |
| `iam.roles.list/get` | `GET /v1/roles` / `/{id}` |
| `iam.groups.list/get` | `GET /v1/groups` / `/{id}` |
| `audit.events.list` | `GET /v1/audit-events` |
| `audit.events.get` | `GET /v1/audit-events/{id}` |
| `audit.events.stats` | `GET /v1/audit-events/stats` |
| `audit.events.tail` | `GET /v1/audit-events/tail` |
| `audit.events.funnel` | `POST /v1/audit-events/funnel` |
| `audit.events.retention` | `GET /v1/audit-events/retention` |
| `audit.events.outbox_cursor` | `GET /v1/audit-events/outbox-cursor` |
| `audit.events.event_keys` | `GET /v1/audit-event-keys` |
| `notify.send` | `POST /v1/notify/send` (+ optional `Idempotency-Key` header) |

## Decisions taken

1. **`client.audit` has no `.emit()`** — audit emission is a backend-only `run_node("audit.events.emit")` pattern. Adding SDK emit would couple external callers to backend internals. External services wanting to record events go through feature APIs that emit audit as a side-effect.
2. **Flag SWR cache is TTL-only in v0.2.1** — no background refresh; expired entry blocks on refetch. True stale-while-revalidate (async refresh in background) lands in v0.2.2 alongside other observability work.
3. **Flag cache invalidation is all-or-nothing by key** — cache uses sha256 of `(key, entity, context)` so per-key invalidation would need a reverse index. Current behavior: `invalidate(key)` wipes everything. Acceptable at v0.2.1 scale; proper per-key index in v0.2.2.
4. **IAM mutations deferred** — only `.list()` / `.get()` exposed. Admins who need mutation use the existing HTTP routes directly. IAM `.create/update/delete` helpers in v0.2.4 when admin UI builds push against them.
5. **Response types are dicts** — no Pydantic response models. Typed models land as a separate cross-cutting pass.
6. **Transport gained `headers` parameter** — needed by `notify.send` for `Idempotency-Key`. Stable addition, backward compatible.

## Verification

```
cd sdk/python && ../../.venv/bin/pytest --cov=tennetctl --cov-report=term-missing
```

```
59 passed in 0.43s

Name                      Stmts   Miss Branch BrPart  Cover
tennetctl/__init__.py         9      0      0      0   100%
tennetctl/_transport.py      70      8     22      4    87%
tennetctl/audit.py           29      0      0      0   100%
tennetctl/auth.py            62      1     14      5    92%
tennetctl/client.py          26      2      0      0    92%
tennetctl/errors.py          31      1      6      2    92%
tennetctl/flags.py           36      2      6      1    93%
tennetctl/iam.py             19      0      0      0   100%
tennetctl/notify.py          13      0      4      0   100%
TOTAL                       295     14     52     12    93%
```

- ≥80% coverage on each new module ✅ (flags 93, iam 100, audit 100, notify 100)
- 26 new tests added (total 59, up from 33 after 28-01)

## Acceptance criteria

- **AC-1** flags.evaluate + SWR cache ✅ (`test_evaluate_caches_within_ttl`, `test_evaluate_bypasses_cache_for_different_entity`, `test_invalidate_clears_cache`)
- **AC-2** iam read helpers ✅ (parametrized test across users/orgs/workspaces/roles/groups + filter forwarding)
- **AC-3** audit query endpoints + no emit() ✅ (`test_audit_has_no_emit_method` + 8 endpoint tests)
- **AC-4** notify.send + idempotency header ✅ (`test_notify_send_passes_idempotency_key` + 3 more)
- **AC-5** ≥80% coverage per module ✅

## Files created / modified

| File | Action |
|---|---|
| `sdk/python/tennetctl/_transport.py` | +`headers` parameter |
| `sdk/python/tennetctl/client.py` | wire flags/iam/audit/notify |
| `sdk/python/tennetctl/__init__.py` | re-export new classes |
| `sdk/python/tennetctl/flags.py` | NEW — 64 lines |
| `sdk/python/tennetctl/iam.py` | NEW — 32 lines |
| `sdk/python/tennetctl/audit.py` | NEW — 46 lines |
| `sdk/python/tennetctl/notify.py` | NEW — 36 lines |
| `sdk/python/tests/test_flags.py` | NEW — 6 tests |
| `sdk/python/tests/test_iam.py` | NEW — 7 tests |
| `sdk/python/tests/test_audit.py` | NEW — 9 tests |
| `sdk/python/tests/test_notify.py` | NEW — 4 tests |
