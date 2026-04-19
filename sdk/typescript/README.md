# @tennetctl/sdk

Unified TypeScript SDK for the [TennetCTL](https://github.com/) platform. Zero runtime dependencies — native `fetch`, works in browsers + Node ≥18 + Deno + Bun.

**Status:** early preview. Ships `client.auth` only. Flags + IAM + audit + notify land in 29-02; observability modules in v0.2.2; vault + catalog in v0.2.3.

## Install

From the repo root:

```bash
cd sdk/typescript && pnpm install && pnpm build
# or, once published:
pnpm add @tennetctl/sdk
```

## Quickstart

```typescript
import { Tennetctl, AuthError } from "@tennetctl/sdk";

const client = new Tennetctl("http://localhost:51734");

// Signin — stores session token on the client
await client.auth.signin({ email: "admin@example.com", password: "hunter2" });

// Read current user
const me = await client.auth.me();
console.log(`Signed in as ${(me as any).email}`);

// Create an API key (shown exactly once)
const key = await client.auth.api_keys.create({
  name: "local-dev",
  scopes: ["audit:read", "flags:read"],
});
console.log(`New key: ${(key as any).token}`);

// List sessions
for (const s of await client.auth.sessions.list()) {
  console.log(s.id, s.user_agent);
}

await client.auth.signout();
```

Or with an API key:

```typescript
const client = new Tennetctl("http://localhost:51734", { apiKey: "nk_xxxx.yyyy" });
```

## Error handling

Every failure throws a subclass of `TennetctlError`:

| Exception | HTTP status |
|---|---|
| `AuthError` | 401 / 403 |
| `ValidationError` | 400 / 422 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |
| `NetworkError` | connection / timeout |

```typescript
import { AuthError } from "@tennetctl/sdk";

try {
  await client.auth.signin({ email: "a@b.c", password: "wrong" });
} catch (e) {
  if (e instanceof AuthError) {
    console.log(e.code, e.status, e.message);
  }
}
```

## Retry policy

Transient errors (network + `502/503/504`) retry with exponential backoff: **500ms, 1s, 2s** (max 3 retries, 4 attempts total). Non-transient 4xx errors fail immediately.

## Injecting fetch (tests, custom transport)

```typescript
const client = new Tennetctl("http://api", {
  apiKey: "nk.x",
  fetchFn: myFetch,            // default: globalThis.fetch
  sleepFn: async () => {},     // bypass backoff in tests
});
```

## License

AGPL-3.0-or-later.
