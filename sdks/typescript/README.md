# @tennetctl/sdk (TypeScript)

Thin TypeScript / JavaScript client for TennetCTL feature flags. Zero dependencies — uses native `fetch`.

Works in Node 18+, Deno, Bun, modern browsers, Cloudflare Workers.

## Install

```sh
npm install @tennetctl/sdk
```

## Usage

```ts
import { FlagsClient } from "@tennetctl/sdk";

const flags = new FlagsClient({
  baseUrl: "http://localhost:51734",
  apiKey: process.env.TENNETCTL_API_KEY,
  environment: "prod",
});

const isOn = await flags.evaluate("new_checkout_flow", {
  userId: "u-123",
  orgId: "o-456",
});

const variant = await flags.evaluate(
  "homepage_variant",
  { userId: "u-123" },
  "control",  // default if flag doesn't exist
);

const all = await flags.evaluateBulk(["a", "b", "c"], {
  userId: "u-123",
});
```

For evaluation detail (including reason / rule_id), use `evaluateDetailed`.

## Cache

The client caches evaluations in-process with a 60s TTL by default. Override via `cacheTtlMs`. Call `invalidateCache()` to clear.
