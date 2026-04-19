import type { Transport } from "./transport.js";

export class Traces {
  constructor(private readonly t: Transport) {}

  async emitBatch(resourceSpans: Array<Record<string, unknown>>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/monitoring/otlp/v1/traces", {
      body: { resourceSpans },
    });
  }

  async query(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/monitoring/traces/query", { body });
  }

  async get(traceId: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/monitoring/traces/${traceId}`);
  }
}
