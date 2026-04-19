# 29-02 SUMMARY — TypeScript SDK: flags + iam + audit + notify modules

**Status:** ✅ Complete (2026-04-18)
**Mirrors:** `29-01-SUMMARY.md` (Python)

## What shipped

Four new capability modules in `@tennetctl/sdk` — exact API parity with Python 29-01.

### Public surface

```ts
import { Tennetctl } from "@tennetctl/sdk";
const client = new Tennetctl(baseUrl, { apiKey: "...", flagsTtlSeconds: 60 });

// flags
await client.flags.evaluate("flag-key", { entity: "user:1", context: { country: "US" } });
await client.flags.evaluateBulk([{ key: "a", entity: "u" }]);
client.flags.invalidate("flag-key");

// iam (read-only)
await client.iam.users.list({ status: "active" });
await client.iam.users.get("u1");
// orgs, workspaces, roles, groups — same shape

// audit (query-only)
await client.audit.events.list({ category: "iam" });
await client.audit.events.get("e1");
await client.audit.events.stats();
await client.audit.events.tail();
await client.audit.events.funnel({ steps: [...] });
await client.audit.events.retention();
await client.audit.events.outboxCursor();
await client.audit.events.eventKeys();

// notify
await client.notify.send({
  template_key: "password_reset",
  recipient_user_id: "u1",
  variables: { link: "..." },
  channel: "email",
  idempotency_key: "uuid-123",
});
```

### Parity vs Python

| Binding | Python | TS | Match |
|---|---|---|---|
| `flags.evaluate` cache TTL | `flags_ttl_seconds` | `flagsTtlSeconds` | ✅ |
| Bulk call name | `evaluate_bulk` | `evaluateBulk` (JS idiomatic) | ✅ (intentional casing diff) |
| `iam.*.list/get` shape | property → resource | readonly property → resource | ✅ |
| `audit.events.*` methods | same 8 methods | same 8 methods | ✅ |
| No `audit.emit` | absent | absent (tested) | ✅ |
| `notify.send` idempotency | `idempotency_key=` → `Idempotency-Key` header | `idempotency_key:` → same header | ✅ |
| Optional fields omitted when undefined | yes | yes | ✅ |

## Verification

```
cd sdk/typescript
pnpm test:cov
pnpm typecheck
pnpm build
```

Results:
```
Tests:     55 passed (55) — transport(19) + auth(15) + capabilities(21)
Coverage:  96.51% stmts, 82.11% branch, 91.52% funcs
           flags.ts 100%   iam.ts 100%   notify.ts 100%   audit.ts 80.76%
           auth.ts 97.46%  transport.ts 97.63%
Typecheck: clean
Build:     dist/ emitted cleanly
```

Note: audit.ts coverage is 80.76% because the `stringParams` helper has paths for non-JSON values that tests don't hit. All public methods have tests.

## Files created / modified

| File | Action |
|---|---|
| `sdk/typescript/src/transport.ts` | +`headers` in request opts |
| `sdk/typescript/src/client.ts` | wire flags/iam/audit/notify |
| `sdk/typescript/src/index.ts` | re-export new classes |
| `sdk/typescript/src/flags.ts` | NEW — 55 lines |
| `sdk/typescript/src/iam.ts` | NEW — 44 lines |
| `sdk/typescript/src/audit.ts` | NEW — 62 lines |
| `sdk/typescript/src/notify.ts` | NEW — 28 lines |
| `sdk/typescript/tests/capabilities.test.ts` | NEW — 21 tests |

## Phase 29 status

- 29-01 Python ✅
- 29-02 TypeScript ✅
- **Phase 29 complete**.
