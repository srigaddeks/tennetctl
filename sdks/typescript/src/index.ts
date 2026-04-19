/**
 * @tennetctl/sdk — thin TypeScript client for TennetCTL feature flags.
 *
 * Zero dependencies. Uses native fetch (available in Node 18+, Deno, Bun,
 * modern browsers, Cloudflare Workers).
 *
 * ```ts
 * import { FlagsClient } from "@tennetctl/sdk";
 *
 * const flags = new FlagsClient({
 *   baseUrl: "http://localhost:51734",
 *   apiKey: "nk_...",
 *   environment: "prod",
 * });
 *
 * const isOn = await flags.evaluate("new_checkout_flow", {
 *   userId: "u-123",
 *   orgId: "o-456",
 * });
 * ```
 */

export type Environment = "dev" | "staging" | "prod" | "test";

export type EvalReason =
  | "user_override"
  | "org_override"
  | "application_override"
  | "rule_match"
  | "default_env"
  | "default_flag"
  | "flag_disabled_in_env"
  | "flag_not_found"
  | "flag_inactive";

export type EvalContext = {
  userId?: string | null;
  orgId?: string | null;
  workspaceId?: string | null;
  applicationId?: string | null;
  attrs?: Record<string, unknown>;
};

export type EvalResult = {
  value: unknown;
  reason: EvalReason | string;
  flagId: string | null;
  flagScope: string | null;
  ruleId: string | null;
  overrideId: string | null;
};

export type FlagsClientOptions = {
  baseUrl: string;
  apiKey?: string;
  environment?: Environment;
  /** SWR cache TTL in milliseconds. Default 60 000. */
  cacheTtlMs?: number;
  /** Request timeout in milliseconds. Default 3 000. */
  timeoutMs?: number;
  /** Override fetch (for tests). */
  fetch?: typeof fetch;
};

type CacheEntry = {
  result: EvalResult;
  expiresAt: number;
};

function cacheKey(flagKey: string, env: string, ctx: EvalContext): string {
  return JSON.stringify([flagKey, env, ctx]);
}

/** Evaluate feature flags against the TennetCTL API. */
export class FlagsClient {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;
  private readonly environment: Environment;
  private readonly cacheTtlMs: number;
  private readonly timeoutMs: number;
  private readonly cache = new Map<string, CacheEntry>();
  private readonly fetchImpl: typeof fetch;

  constructor(opts: FlagsClientOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/+$/, "");
    this.environment = opts.environment ?? "prod";
    this.cacheTtlMs = opts.cacheTtlMs ?? 60_000;
    this.timeoutMs = opts.timeoutMs ?? 3_000;
    this.fetchImpl = opts.fetch ?? fetch;
    this.headers = { "content-type": "application/json" };
    if (opts.apiKey) {
      this.headers.authorization = `Bearer ${opts.apiKey}`;
    }
  }

  /**
   * Evaluate a single flag. Returns the resolved value or `defaultValue`
   * if the flag doesn't exist or the call fails.
   */
  async evaluate<T = unknown>(
    flagKey: string,
    context: EvalContext = {},
    defaultValue?: T,
  ): Promise<T | unknown> {
    const result = await this.evaluateDetailed(flagKey, context);
    if (result === null || result.reason === "flag_not_found") {
      return defaultValue ?? null;
    }
    return result.value;
  }

  /**
   * Evaluate a flag and return the full detail (value + reason + trace).
   * Returns null on network error.
   */
  async evaluateDetailed(
    flagKey: string,
    context: EvalContext = {},
  ): Promise<EvalResult | null> {
    const key = cacheKey(flagKey, this.environment, context);
    const now = Date.now();

    const cached = this.cache.get(key);
    if (cached && cached.expiresAt > now) {
      return cached.result;
    }

    const body = {
      flag_key: flagKey,
      environment: this.environment,
      context: {
        user_id: context.userId ?? null,
        org_id: context.orgId ?? null,
        workspace_id: context.workspaceId ?? null,
        application_id: context.applicationId ?? null,
        attrs: context.attrs ?? {},
      },
    };

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const res = await this.fetchImpl(`${this.baseUrl}/v1/evaluate`, {
        method: "POST",
        headers: this.headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) return null;

      const payload = (await res.json()) as {
        ok?: boolean;
        data?: {
          value: unknown;
          reason: string;
          flag_id: string | null;
          flag_scope: string | null;
          rule_id: string | null;
          override_id: string | null;
        };
      };
      if (!payload.ok || !payload.data) return null;

      const result: EvalResult = {
        value: payload.data.value,
        reason: payload.data.reason,
        flagId: payload.data.flag_id,
        flagScope: payload.data.flag_scope,
        ruleId: payload.data.rule_id,
        overrideId: payload.data.override_id,
      };
      this.cache.set(key, {
        result,
        expiresAt: now + this.cacheTtlMs,
      });
      return result;
    } catch {
      return null;
    } finally {
      clearTimeout(timer);
    }
  }

  /** Evaluate many flags against the same context. */
  async evaluateBulk(
    flagKeys: string[],
    context: EvalContext = {},
  ): Promise<Record<string, unknown>> {
    const entries = await Promise.all(
      flagKeys.map(async (k) => [k, await this.evaluate(k, context)] as const),
    );
    return Object.fromEntries(entries);
  }

  /** Clear the in-process cache. */
  invalidateCache(): void {
    this.cache.clear();
  }
}

export default FlagsClient;

// ── Product Ops (server-side track) ────────────────────────────────

export type ProductTrackOptions = {
  baseUrl: string;
  projectKey: string;
  /** Request timeout in ms. Default 5 000. */
  timeoutMs?: number;
};

export type TrackEventInput = {
  kind?: "page_view" | "custom" | "click" | "identify" | "alias" | "referral_attached";
  anonymous_id: string;
  event_name?: string;
  occurred_at?: string;
  page_url?: string;
  referrer?: string;
  properties?: Record<string, unknown>;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

/**
 * Server-side Product Ops client. Mirrors @tennetctl/browser's track/identify
 * but for backend services (e.g. emit "order.completed" from a webhook handler).
 *
 * Anonymous browser ingest is NOT this client's job — use @tennetctl/browser
 * in the browser, ProductOpsClient in the backend.
 */
export class ProductOpsClient {
  private baseUrl: string;
  private projectKey: string;
  private timeoutMs: number;

  constructor(opts: ProductTrackOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/+$/, "");
    this.projectKey = opts.projectKey;
    this.timeoutMs = opts.timeoutMs ?? 5_000;
  }

  async track(eventName: string, input: Omit<TrackEventInput, "kind" | "event_name">): Promise<void> {
    await this.trackBatch([
      { ...input, kind: "custom", event_name: eventName, occurred_at: input.occurred_at ?? new Date().toISOString() },
    ]);
  }

  async identify(anonymousId: string, userId: string, traits: Record<string, unknown> = {}): Promise<void> {
    await this.trackBatch([
      {
        kind: "identify",
        anonymous_id: anonymousId,
        occurred_at: new Date().toISOString(),
        properties: { user_id: userId, traits },
      },
    ]);
  }

  async trackBatch(events: TrackEventInput[]): Promise<void> {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.timeoutMs);
    try {
      const res = await fetch(`${this.baseUrl}/v1/track`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_key: this.projectKey, events }),
        signal: ctrl.signal,
      });
      if (res.status >= 400) {
        throw new Error(`product_ops track failed: HTTP ${res.status}`);
      }
    } finally {
      clearTimeout(timer);
    }
  }
}
