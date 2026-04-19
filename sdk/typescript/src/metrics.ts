import type { Transport } from "./transport.js";

export class Metrics {
  constructor(private readonly t: Transport) {}

  async increment(
    key: string,
    args: { value?: number; labels?: Record<string, unknown> } = {},
  ): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { value: args.value ?? 1 };
    if (args.labels !== undefined) body.labels = args.labels;
    return this.t.request("POST", `/v1/monitoring/metrics/${key}/increment`, { body });
  }

  async set(
    key: string,
    args: { value: number; labels?: Record<string, unknown> },
  ): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { value: args.value };
    if (args.labels !== undefined) body.labels = args.labels;
    return this.t.request("POST", `/v1/monitoring/metrics/${key}/set`, { body });
  }

  async observe(
    key: string,
    args: { value: number; labels?: Record<string, unknown> },
  ): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { value: args.value };
    if (args.labels !== undefined) body.labels = args.labels;
    return this.t.request("POST", `/v1/monitoring/metrics/${key}/observe`, { body });
  }

  async register(args: {
    key: string;
    kind: string;
    description?: string;
    buckets?: number[];
    cardinality_limit?: number;
  }): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = { key: args.key, kind: args.kind };
    if (args.description !== undefined) body.description = args.description;
    if (args.buckets !== undefined) body.buckets = args.buckets;
    if (args.cardinality_limit !== undefined) body.cardinality_limit = args.cardinality_limit;
    return this.t.request("POST", "/v1/monitoring/metrics", { body });
  }

  async list(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Array<Record<string, unknown>>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    const data = await this.t.request<Array<Record<string, unknown>>>("GET", "/v1/monitoring/metrics", {
      params: Object.keys(params).length ? params : undefined,
    });
    return Array.isArray(data) ? data : [];
  }

  async get(key: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/monitoring/metrics/${key}`);
  }

  async query(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/monitoring/metrics/query", { body });
  }
}
