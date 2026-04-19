import { describe, expect, it } from "vitest";
import {
  AuthError,
  ConflictError,
  NetworkError,
  NotFoundError,
  RateLimitError,
  ServerError,
  Tennetctl,
  TennetctlError,
  ValidationError,
} from "../src/index.js";

type FetchCall = { url: string; init: RequestInit };

function mockFetch(impl: (call: FetchCall) => Promise<Response> | Response) {
  const calls: FetchCall[] = [];
  const fn: typeof fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : (input as Request).url;
    const call: FetchCall = { url, init };
    calls.push(call);
    return impl(call);
  };
  return { fn, calls };
}

function makeClient(fetchFn: typeof fetch, opts: { apiKey?: string; sessionToken?: string } = { apiKey: "nk_test.secret" }) {
  return new Tennetctl("http://testserver", {
    ...opts,
    fetchFn,
    sleepFn: async () => {}, // no-op — avoids real timers in tests
  });
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("Transport — envelope parsing", () => {
  it("returns data from ok:true envelope", async () => {
    const { fn } = mockFetch(() => jsonResponse({ ok: true, data: { pong: 1 } }));
    const c = makeClient(fn);
    const result = await c._transport.request<{ pong: number }>("GET", "/v1/ping");
    expect(result).toEqual({ pong: 1 });
  });

  it("returns undefined on 204", async () => {
    const { fn } = mockFetch(() => new Response(null, { status: 204 }));
    const c = makeClient(fn);
    expect(await c._transport.request("DELETE", "/v1/x")).toBeUndefined();
  });

  it("sets Authorization header with api key", async () => {
    const { fn, calls } = mockFetch(() => jsonResponse({ ok: true, data: {} }));
    const c = makeClient(fn);
    await c._transport.request("GET", "/v1/ping");
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer nk_test.secret");
  });

  it("omits Authorization when no api key", async () => {
    const { fn, calls } = mockFetch(() => jsonResponse({ ok: true, data: {} }));
    const c = makeClient(fn, {});
    await c._transport.request("GET", "/v1/ping");
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers["Authorization"]).toBeUndefined();
  });
});

describe("Transport — error mapping", () => {
  const cases: Array<[number, typeof TennetctlError]> = [
    [400, ValidationError],
    [401, AuthError],
    [403, AuthError],
    [404, NotFoundError],
    [409, ConflictError],
    [422, ValidationError],
    [429, RateLimitError],
    [500, ServerError],
  ];

  for (const [status, ctor] of cases) {
    it(`${status} → ${ctor.name}`, async () => {
      const { fn } = mockFetch(() =>
        jsonResponse({ ok: false, error: { code: "X", message: "nope" } }, status),
      );
      const c = makeClient(fn, { sessionToken: "tok" });
      // For 5xx we avoid retries by using only one attempt worth of status
      await expect(c._transport.request("GET", "/v1/err")).rejects.toBeInstanceOf(ctor);
    });
  }

  it("unmapped status falls back to TennetctlError base", async () => {
    const { fn } = mockFetch(() =>
      jsonResponse({ ok: false, error: { code: "TEAPOT", message: "short" } }, 418),
    );
    const c = makeClient(fn);
    try {
      await c._transport.request("GET", "/v1/teapot");
      throw new Error("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(TennetctlError);
      expect((e as TennetctlError).code).toBe("TEAPOT");
      expect((e as TennetctlError).status).toBe(418);
    }
  });

  it("non-JSON error body still raises", async () => {
    const { fn } = mockFetch(() => new Response("boom", { status: 500 }));
    const c = makeClient(fn);
    await expect(c._transport.request("GET", "/v1/err")).rejects.toBeInstanceOf(ServerError);
  });
});

describe("Transport — retry policy", () => {
  it("retries on 503 until success", async () => {
    let n = 0;
    const { fn } = mockFetch(() => {
      n++;
      if (n < 3) return jsonResponse({ ok: false, error: { code: "U", message: "" } }, 503);
      return jsonResponse({ ok: true, data: { fine: true } });
    });
    const c = makeClient(fn);
    const result = await c._transport.request<{ fine: boolean }>("GET", "/v1/flaky");
    expect(result).toEqual({ fine: true });
    expect(n).toBe(3);
  });

  it("retry exhaustion throws ServerError after 4 attempts", async () => {
    let n = 0;
    const { fn } = mockFetch(() => {
      n++;
      return jsonResponse({ ok: false, error: { code: "DOWN", message: "" } }, 503);
    });
    const c = makeClient(fn);
    await expect(c._transport.request("GET", "/v1/down")).rejects.toBeInstanceOf(ServerError);
    expect(n).toBe(4);
  });

  it("does NOT retry on 400", async () => {
    let n = 0;
    const { fn } = mockFetch(() => {
      n++;
      return jsonResponse({ ok: false, error: { code: "BAD", message: "" } }, 400);
    });
    const c = makeClient(fn);
    await expect(c._transport.request("POST", "/v1/bad", { body: { x: 1 } })).rejects.toBeInstanceOf(
      ValidationError,
    );
    expect(n).toBe(1);
  });

  it("throws NetworkError after retry exhaustion on fetch failure", async () => {
    let n = 0;
    const fn: typeof fetch = async () => {
      n++;
      throw new TypeError("fetch failed");
    };
    const c = makeClient(fn);
    await expect(c._transport.request("GET", "/v1/netfail")).rejects.toBeInstanceOf(NetworkError);
    expect(n).toBe(4);
  });
});

describe("Transport — session token", () => {
  it("get/set/clear session token", () => {
    const { fn } = mockFetch(() => jsonResponse({ ok: true, data: {} }));
    const c = makeClient(fn, {});
    expect(c.sessionToken).toBeUndefined();
    c._transport.setSessionToken("abc");
    expect(c.sessionToken).toBe("abc");
    c._transport.setSessionToken(undefined);
    expect(c.sessionToken).toBeUndefined();
  });
});
