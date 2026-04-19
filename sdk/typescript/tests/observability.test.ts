import { describe, expect, it } from "vitest";
import { Tennetctl, type TennetctlOptions } from "../src/index.js";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function harness(
  responder: (url: string, init: RequestInit) => Response,
  opts: TennetctlOptions = {},
) {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const fetchFn: typeof fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : (input as Request).url;
    calls.push({ url, init });
    return responder(url, init);
  };
  const client = new Tennetctl("http://testserver", {
    apiKey: "nk.x",
    fetchFn,
    sleepFn: async () => {},
    ...opts,
  });
  return { client, calls };
}

// ------------------------------------------------------------- metrics

describe("metrics", () => {
  it("increment posts value + labels to /{key}/increment", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { accepted: true } }, 201),
    );
    await client.metrics.increment("http_requests_total", { value: 1, labels: { route: "/x" } });
    expect(calls[0]!.url).toContain("/v1/monitoring/metrics/http_requests_total/increment");
    expect(calls[0]!.init.body as string).toContain("route");
  });

  it("set posts to /{key}/set", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { accepted: true } }, 201),
    );
    await client.metrics.set("queue_depth", { value: 42 });
    expect(calls[0]!.url).toContain("/queue_depth/set");
  });

  it("observe posts to /{key}/observe", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { accepted: true } }, 201),
    );
    await client.metrics.observe("latency_ms", { value: 123 });
    expect(calls[0]!.url).toContain("/latency_ms/observe");
  });

  it("register posts to metrics root", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { id: 1 } }, 201),
    );
    await client.metrics.register({ key: "x", kind: "counter", description: "d" });
    expect(calls[0]!.url).toContain("/v1/monitoring/metrics");
    expect(calls[0]!.init.body as string).toContain("counter");
  });

  it("list + get + query", async () => {
    const { client } = harness(() =>
      jsonResponse({ ok: true, data: [{ key: "a" }] }),
    );
    expect(await client.metrics.list()).toHaveLength(1);

    const { client: c2 } = harness(() =>
      jsonResponse({ ok: true, data: { key: "a" } }),
    );
    expect((await c2.metrics.get("a")).key).toBe("a");

    const { client: c3 } = harness(() =>
      jsonResponse({ ok: true, data: { series: [] } }),
    );
    expect(await c3.metrics.query({ key: "a" })).toHaveProperty("series");
  });
});

// ------------------------------------------------------------- logs

describe("logs", () => {
  it("emit wraps OTLP JSON", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { partialSuccess: {} } }),
    );
    await client.logs.emit({
      severity: "INFO",
      body: "hello",
      attributes: { user_id: "u1", count: 3, ok: true },
      service_name: "svc",
    });
    const body = calls[0]!.init.body as string;
    expect(body).toContain("resourceLogs");
    expect(body).toContain("service.name");
    expect(body).toContain("hello");
  });

  it("query posts", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { logs: [] } }),
    );
    await client.logs.query({ severity: "ERROR" });
    expect(calls[0]!.url).toContain("/v1/monitoring/logs/query");
  });

  it("tail gets", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { logs: [] } }),
    );
    await client.logs.tail({ severity: "ERROR" });
    expect(calls[0]!.url).toContain("/v1/monitoring/logs/tail");
    expect(calls[0]!.url).toContain("severity=ERROR");
  });
});

// ------------------------------------------------------------- traces

describe("traces", () => {
  it("emitBatch wraps resourceSpans", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { partialSuccess: {} } }),
    );
    await client.traces.emitBatch([
      {
        resource: { attributes: [] },
        scopeSpans: [{ spans: [{ traceId: "t", spanId: "s", name: "op" }] }],
      },
    ]);
    expect(calls[0]!.url).toContain("/v1/monitoring/otlp/v1/traces");
    expect(calls[0]!.init.body as string).toContain("resourceSpans");
  });

  it("get by trace id", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { trace_id: "t", spans: [] } }),
    );
    const t = await client.traces.get("t");
    expect(calls[0]!.url).toContain("/v1/monitoring/traces/t");
    expect(t.trace_id).toBe("t");
  });

  it("query posts", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { traces: [] } }),
    );
    await client.traces.query({ service: "x" });
    expect(calls[0]!.url).toContain("/v1/monitoring/traces/query");
  });
});

// ------------------------------------------------------------- vault

describe("vault.secrets", () => {
  it("list + get", async () => {
    const { client } = harness(() =>
      jsonResponse({ ok: true, data: [{ key: "k1" }] }),
    );
    expect(await client.vault.secrets.list()).toHaveLength(1);

    const { client: c2 } = harness(() =>
      jsonResponse({ ok: true, data: { key: "k1", value: "***" } }),
    );
    expect((await c2.vault.secrets.get("k1")).key).toBe("k1");
  });

  it("create + rotate + delete", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { key: "k" } }, 201),
    );
    await client.vault.secrets.create({ key: "k", value: "v", description: "d" });
    expect(calls[0]!.init.body as string).toContain("v");

    const { client: c2, calls: c2calls } = harness(() =>
      jsonResponse({ ok: true, data: { key: "k", rotated_at: "t" } }),
    );
    await c2.vault.secrets.rotate("k", { value: "new" });
    expect(c2calls[0]!.url).toContain("/v1/vault/k/rotate");

    const { client: c3, calls: c3calls } = harness(
      () => new Response(null, { status: 204 }),
    );
    await c3.vault.secrets.delete("k");
    expect(c3calls[0]!.init.method).toBe("DELETE");
  });
});

describe("vault.configs", () => {
  it("full CRUD", async () => {
    const { client } = harness(() =>
      jsonResponse({ ok: true, data: [{ id: "c1" }] }),
    );
    expect(await client.vault.configs.list()).toHaveLength(1);

    const { client: c2 } = harness(() =>
      jsonResponse({ ok: true, data: { id: "c1" } }),
    );
    expect((await c2.vault.configs.get("c1")).id).toBe("c1");

    const { client: c3 } = harness(() =>
      jsonResponse({ ok: true, data: { id: "c2" } }, 201),
    );
    expect((await c3.vault.configs.create({ key: "x" })).id).toBe("c2");

    const { client: c4 } = harness(() =>
      jsonResponse({ ok: true, data: { id: "c1", v: "new" } }),
    );
    expect((await c4.vault.configs.update("c1", { v: "new" })).v).toBe("new");

    const { client: c5, calls } = harness(
      () => new Response(null, { status: 204 }),
    );
    await c5.vault.configs.delete("c1");
    expect(calls[0]!.init.method).toBe("DELETE");
  });
});

// ------------------------------------------------------------- catalog

describe("catalog", () => {
  it("listNodes", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: [{ key: "iam.users.get", kind: "control" }] }),
    );
    const rows = await client.catalog.listNodes({ feature: "iam" });
    expect(rows).toHaveLength(1);
    expect(calls[0]!.url).toContain("feature=iam");
  });

  it("listFeatures + listSubFeatures + getFlow", async () => {
    const { client: c1 } = harness(() =>
      jsonResponse({ ok: true, data: [] }),
    );
    expect(await c1.catalog.listFeatures()).toEqual([]);

    const { client: c2 } = harness(() =>
      jsonResponse({ ok: true, data: [] }),
    );
    expect(await c2.catalog.listSubFeatures("iam")).toEqual([]);

    const { client: c3 } = harness(() =>
      jsonResponse({ ok: true, data: { key: "f1" } }),
    );
    expect((await c3.catalog.getFlow("f1")).key).toBe("f1");
  });
});
