import type { Transport } from "./transport.js";

export const DEFAULT_FLAGS_TTL_SECONDS = 60;

function cacheKey(key: string, entity: unknown, context: unknown): string {
  return JSON.stringify({ k: key, e: entity, c: context });
}

export interface FlagResult {
  value: unknown;
  source?: string;
  matched_rule_id?: string;
  [key: string]: unknown;
}

export class Flags {
  private readonly cache = new Map<string, { at: number; value: FlagResult }>();

  constructor(
    private readonly t: Transport,
    private readonly ttlSeconds: number = DEFAULT_FLAGS_TTL_SECONDS,
  ) {}

  async evaluate(
    key: string,
    args: { entity: unknown; context?: unknown },
  ): Promise<FlagResult> {
    const ck = cacheKey(key, args.entity, args.context);
    const now = Date.now();
    const hit = this.cache.get(ck);
    if (hit && (now - hit.at) / 1000 < this.ttlSeconds) {
      return hit.value;
    }

    const body: Record<string, unknown> = { key, entity: args.entity };
    if (args.context !== undefined) body.context = args.context;
    const result = await this.t.request<FlagResult>("POST", "/v1/evaluate", { body });
    this.cache.set(ck, { at: now, value: result });
    return result;
  }

  async evaluateBulk(evaluations: Array<Record<string, unknown>>): Promise<FlagResult[]> {
    const result = await this.t.request<FlagResult[]>("POST", "/v1/evaluate/bulk", {
      body: { evaluations },
    });
    return Array.isArray(result) ? result : [];
  }

  clearCache(): void {
    this.cache.clear();
  }

  invalidate(_key?: string): void {
    // v0.2.1: cache key is a hash — wipe everything. Better index in v0.2.2.
    this.clearCache();
  }
}
