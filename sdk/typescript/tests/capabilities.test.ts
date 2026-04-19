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

// ---------------------------------------------------------------- flags

describe("flags", () => {
  it("evaluate posts and caches within TTL", async () => {
    let n = 0;
    const { client } = harness(() => {
      n++;
      return jsonResponse({ ok: true, data: { value: true, source: "rule" } });
    });
    const r1 = await client.flags.evaluate("f", { entity: "u1" });
    const r2 = await client.flags.evaluate("f", { entity: "u1" });
    expect(r1).toEqual(r2);
    expect(n).toBe(1);
  });

  it("evaluate misses cache for different entity", async () => {
    let n = 0;
    const { client } = harness(() => {
      n++;
      return jsonResponse({ ok: true, data: { value: n } });
    });
    await client.flags.evaluate("f", { entity: "u1" });
    await client.flags.evaluate("f", { entity: "u2" });
    expect(n).toBe(2);
  });

  it("evaluate forwards context", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { value: "x" } }),
    );
    await client.flags.evaluate("f", { entity: "u", context: { country: "US" } });
    expect(calls[0]!.init.body as string).toContain("US");
  });

  it("invalidate clears cache", async () => {
    let n = 0;
    const { client } = harness(() => {
      n++;
      return jsonResponse({ ok: true, data: { value: "v" } });
    });
    await client.flags.evaluate("f", { entity: "u" });
    client.flags.invalidate("f");
    await client.flags.evaluate("f", { entity: "u" });
    expect(n).toBe(2);
  });

  it("evaluate bulk posts array", async () => {
    const { client } = harness(() =>
      jsonResponse({ ok: true, data: [{ value: 1 }, { value: 2 }] }),
    );
    const rows = await client.flags.evaluateBulk([
      { key: "a", entity: "u" },
      { key: "b", entity: "u" },
    ]);
    expect(rows).toHaveLength(2);
  });
});

// ---------------------------------------------------------------- iam

describe("iam", () => {
  for (const [resource, path] of [
    ["users", "/v1/users"],
    ["orgs", "/v1/orgs"],
    ["workspaces", "/v1/workspaces"],
    ["roles", "/v1/roles"],
    ["groups", "/v1/groups"],
  ] as const) {
    it(`${resource}.list hits ${path}`, async () => {
      const { client, calls } = harness(() =>
        jsonResponse({ ok: true, data: [{ id: "x" }] }),
      );
      await (client.iam as any)[resource].list();
      expect(calls[0]!.url).toContain(path);
    });
  }

  it("list forwards filters as query params", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: [] }),
    );
    await client.iam.orgs.list({ status: "active", limit: 50 });
    expect(calls[0]!.url).toContain("status=active");
    expect(calls[0]!.url).toContain("limit=50");
  });

  it("get hits /{id}", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { id: "u1" } }),
    );
    await client.iam.users.get("u1");
    expect(calls[0]!.url).toContain("/v1/users/u1");
  });
});

// ---------------------------------------------------------------- audit

describe("audit", () => {
  it("has no emit method", () => {
    const { client } = harness(() => jsonResponse({ ok: true, data: {} }));
    expect((client.audit as any).emit).toBeUndefined();
    expect((client.audit.events as any).emit).toBeUndefined();
  });

  it("events.list hits /v1/audit-events", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { events: [] } }),
    );
    await client.audit.events.list({ category: "iam" });
    expect(calls[0]!.url).toContain("/v1/audit-events");
    expect(calls[0]!.url).toContain("category=iam");
  });

  it("events.get hits /{id}", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { id: "e1" } }),
    );
    await client.audit.events.get("e1");
    expect(calls[0]!.url).toContain("/v1/audit-events/e1");
  });

  it("events.funnel posts body", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { steps: [] } }),
    );
    await client.audit.events.funnel({ steps: [{ key: "a" }] });
    expect(calls[0]!.init.method).toBe("POST");
    expect(calls[0]!.url).toContain("/funnel");
  });

  it("events.eventKeys", async () => {
    const { client } = harness(() =>
      jsonResponse({ ok: true, data: [{ key: "iam.x" }] }),
    );
    const keys = await client.audit.events.eventKeys();
    expect(keys).toHaveLength(1);
  });
});

// ---------------------------------------------------------------- notify

describe("notify", () => {
  it("send posts body", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { delivery_id: "d1" } }, 201),
    );
    await client.notify.send({ template_key: "t", recipient_user_id: "u" });
    expect(calls[0]!.url).toContain("/v1/notify/send");
    expect(calls[0]!.init.method).toBe("POST");
    expect(calls[0]!.init.body as string).toContain("recipient_user_id");
  });

  it("send forwards Idempotency-Key header", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { delivery_id: "d1" } }, 201),
    );
    await client.notify.send({
      template_key: "t",
      recipient_user_id: "u",
      idempotency_key: "abc",
    });
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers["Idempotency-Key"]).toBe("abc");
  });

  it("send omits optional fields when not set", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { delivery_id: "d1" } }, 201),
    );
    await client.notify.send({ template_key: "t", recipient_user_id: "u" });
    const body = calls[0]!.init.body as string;
    expect(body).not.toContain("variables");
    expect(body).not.toContain("channel");
  });

  it("send forwards channel override", async () => {
    const { client, calls } = harness(() =>
      jsonResponse({ ok: true, data: { delivery_id: "d1" } }, 201),
    );
    await client.notify.send({
      template_key: "t",
      recipient_user_id: "u",
      channel: "webpush",
    });
    expect(calls[0]!.init.body as string).toContain("webpush");
  });
});
