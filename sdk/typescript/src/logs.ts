import type { Transport } from "./transport.js";

type OtlpValue =
  | { stringValue: string }
  | { boolValue: boolean }
  | { intValue: string }
  | { doubleValue: number };

function otlpValue(v: unknown): OtlpValue {
  if (typeof v === "boolean") return { boolValue: v };
  if (typeof v === "number") {
    if (Number.isInteger(v)) return { intValue: String(v) };
    return { doubleValue: v };
  }
  return { stringValue: String(v) };
}

export class Logs {
  constructor(private readonly t: Transport) {}

  async emit(args: {
    severity: string;
    body: string;
    attributes?: Record<string, unknown>;
    service_name?: string;
    trace_id?: string;
    span_id?: string;
  }): Promise<Record<string, unknown>> {
    const resourceAttrs: Array<{ key: string; value: OtlpValue }> = [];
    if (args.service_name) resourceAttrs.push({ key: "service.name", value: otlpValue(args.service_name) });

    const logRecord: Record<string, unknown> = {
      severityText: args.severity,
      body: { stringValue: args.body },
    };
    if (args.attributes) {
      logRecord.attributes = Object.entries(args.attributes).map(([k, v]) => ({
        key: k,
        value: otlpValue(v),
      }));
    }
    if (args.trace_id) logRecord.traceId = args.trace_id;
    if (args.span_id) logRecord.spanId = args.span_id;

    return this.t.request("POST", "/v1/monitoring/otlp/v1/logs", {
      body: {
        resourceLogs: [
          {
            resource: { attributes: resourceAttrs },
            scopeLogs: [{ logRecords: [logRecord] }],
          },
        ],
      },
    });
  }

  async emitBatch(records: Array<Record<string, unknown>>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/monitoring/otlp/v1/logs", {
      body: { resourceLogs: records },
    });
  }

  async query(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.t.request("POST", "/v1/monitoring/logs/query", { body });
  }

  async tail(
    filters: Record<string, string | number | boolean | undefined> = {},
  ): Promise<Record<string, unknown>> {
    const params: Record<string, string | number | boolean | undefined> = {};
    for (const [k, v] of Object.entries(filters)) if (v !== undefined) params[k] = v;
    return this.t.request("GET", "/v1/monitoring/logs/tail", {
      params: Object.keys(params).length ? params : undefined,
    });
  }
}
