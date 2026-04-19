import type { Transport } from "./transport.js";

export class AuditEvents {
  constructor(private readonly t: Transport) {}

  async list(filters: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/audit-events", { params: stringParams(filters) });
  }

  async get(id: string): Promise<Record<string, unknown>> {
    return this.t.request("GET", `/v1/audit-events/${id}`);
  }

  async stats(filters: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/audit-events/stats", { params: stringParams(filters) });
  }

  async tail(filters: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/audit-events/tail", { params: stringParams(filters) });
  }

  async funnel(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/audit-events/funnel", { body });
  }

  async retention(filters: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/audit-events/retention", { params: stringParams(filters) });
  }

  async outboxCursor(): Promise<Record<string, unknown>> {
    return this.t.request("GET", "/v1/audit-events/outbox-cursor");
  }

  async eventKeys(): Promise<Array<Record<string, unknown>>> {
    const data = await this.t.request<Array<Record<string, unknown>>>(
      "GET",
      "/v1/audit-event-keys",
    );
    return Array.isArray(data) ? data : [];
  }
}

function stringParams(
  filters: Record<string, unknown>,
): Record<string, string | number | boolean | undefined> | undefined {
  const out: Record<string, string | number | boolean | undefined> = {};
  for (const [k, v] of Object.entries(filters)) {
    if (v !== undefined && v !== null) {
      if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
        out[k] = v;
      } else {
        out[k] = JSON.stringify(v);
      }
    }
  }
  return Object.keys(out).length ? out : undefined;
}

export class Audit {
  readonly events: AuditEvents;
  constructor(t: Transport) {
    this.events = new AuditEvents(t);
  }
  // No emit() — audit emission is backend-only via nodes.
}
