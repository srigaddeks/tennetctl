# 28-02 SUMMARY — TypeScript SDK core + auth module

**Status:** ✅ Complete (2026-04-18)
**Mirrors:** `28-01-SUMMARY.md` (Python)

## What shipped

`@tennetctl/sdk` — zero-runtime-dep TypeScript SDK at `sdk/typescript/`. Native `fetch`, works in browser + Node ≥18 + Bun + Deno.

### Public surface

```ts
import {
  Tennetctl, TennetctlOptions,
  Auth, Sessions, ApiKeys, SignedInResponse,
  Transport, TransportOptions, FetchFn, SESSION_COOKIE,
  TennetctlError, AuthError, ValidationError, NotFoundError,
  ConflictError, RateLimitError, ServerError, NetworkError,
  mapError, ErrorEnvelope,
  VERSION,
} from "@tennetctl/sdk";
```

### API shape (matches Python SDK exactly)

```ts
const client = new Tennetctl(baseUrl, { apiKey?, sessionToken?, fetchFn?, sleepFn?, timeoutMs? });

await client.auth.signin({ email, password });
await client.auth.signout();
await client.auth.me();
await client.auth.signup({ email, password, ...extra });

await client.auth.sessions.list();
await client.auth.sessions.get(id);
await client.auth.sessions.update(id, patch);
await client.auth.sessions.revoke(id);

await client.auth.api_keys.list();
await client.auth.api_keys.create({ name, scopes, expires_at? });
await client.auth.api_keys.revoke(id);
await client.auth.api_keys.rotate(id);

client.sessionToken;  // readonly
```

### Parity guarantees vs Python (from 28-01-SUMMARY decisions)

| Binding | Python | TypeScript | Match |
|---|---|---|---|
| Cookie name | `tnt_session` | `SESSION_COOKIE = "tnt_session"` | ✅ |
| Token extraction order | `data.token` → `data.session_token` → `data.session.token` | same 3-step fallback | ✅ |
| Session token storage | on Transport + readable via `client.session_token` | on Transport + readable via `client.sessionToken` | ✅ |
| Signout clears on error | try/finally | try/finally | ✅ |
| Signup stores token | yes (same path as signin) | yes (same path as signin) | ✅ |
| Sub-namespace shape | property returning instance | readonly property returning instance | ✅ |
| Auth header preferred | yes when `api_key` supplied | yes when `apiKey` supplied | ✅ |
| Response dicts, no typed models | dicts | `Record<string, unknown>` | ✅ (pending 29-xx) |

### Retry policy (bound by Python)

- Retryable: network error + HTTP `502 / 503 / 504`
- Backoff: `500ms, 1000ms, 2000ms`
- Max attempts: 4 (1 initial + 3 retries)
- Implementation: `sleepFn` is injectable for tests (defaults to `setTimeout` Promise)

### URL paths

Same as 28-01 — wraps the real FastAPI routes discovered in-codebase:
- `/v1/auth/{signin,signout,me,signup}`
- `/v1/sessions`, `/v1/sessions/{id}`
- `/v1/api-keys`, `/v1/api-keys/{id}`, `/v1/api-keys/{id}/rotate`

## Verification

```bash
cd sdk/typescript
pnpm install
pnpm test:cov
pnpm typecheck
pnpm build
```

Results:
```
Tests:     34 passed (34 total) — transport.test.ts (19) + auth.test.ts (15)
Coverage:  96.66% statements, 81.01% branch, 96.96% funcs
           auth.ts     97.46%   transport.ts 94.06%   errors.ts 100%   client.ts 100%
Typecheck: clean
Build:     dist/ emitted cleanly (ESM + .d.ts)
```

- ≥80% coverage on transport.ts ✅ (94.06%)
- ≥80% coverage on auth.ts ✅ (97.46%)
- All tests pass ✅
- Strict TypeScript ✅

## Files created (10)

| File | Purpose |
|---|---|
| `sdk/typescript/package.json` | pnpm package config |
| `sdk/typescript/tsconfig.json` | strict TS for tests + dev |
| `sdk/typescript/tsconfig.build.json` | narrower build config for `dist/` |
| `sdk/typescript/src/errors.ts` | error hierarchy + `mapError` |
| `sdk/typescript/src/transport.ts` | fetch-based transport with retry + envelope parse |
| `sdk/typescript/src/auth.ts` | `Auth`, `Sessions`, `ApiKeys` classes |
| `sdk/typescript/src/client.ts` | `Tennetctl` entrypoint |
| `sdk/typescript/src/index.ts` | public exports + `VERSION` |
| `sdk/typescript/tests/transport.test.ts` | 19 tests |
| `sdk/typescript/tests/auth.test.ts` | 15 tests |
| `sdk/typescript/README.md` | quickstart + API reference |

## Phase 28 status

- 28-01 Python ✅
- 28-02 TypeScript ✅
- **Phase 28 complete** — ready for 29-01 (flags + iam + audit + notify modules).
