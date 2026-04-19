import { describe, expect, it } from "vitest";
import { Tennetctl } from "../src/index.js";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function makeClient(
  responder: (url: string, init: RequestInit) => Response,
  opts: { apiKey?: string } = {},
) {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const fetchFn: typeof fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : (input as Request).url;
    calls.push({ url, init });
    return responder(url, init);
  };
  const client = new Tennetctl("http://testserver", {
    ...opts,
    fetchFn,
    sleepFn: async () => {},
  });
  return { client, calls };
}

describe("Auth — signin / signout / me / signup", () => {
  it("signin stores session token from top-level token field", async () => {
    const { client } = makeClient(() =>
      jsonResponse({
        ok: true,
        data: {
          token: "sess_abc",
          user: { id: "u1", email: "a@b.c" },
          session: { id: "s1", expires_at: "2099-01-01T00:00:00Z" },
        },
      }),
    );
    const data = await client.auth.signin({ email: "a@b.c", password: "pw" });
    expect((data.user as { email: string }).email).toBe("a@b.c");
    expect(client.sessionToken).toBe("sess_abc");
  });

  it("signin reads token from nested session object", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: { user: { id: "u1" }, session: { id: "s1", token: "nested" } } }),
    );
    await client.auth.signin({ email: "a@b.c", password: "pw" });
    expect(client.sessionToken).toBe("nested");
  });

  it("signout clears session token", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: { signed_out: true } }),
    );
    client._transport.setSessionToken("existing");
    await client.auth.signout();
    expect(client.sessionToken).toBeUndefined();
  });

  it("signout clears session token even on server error", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: false, error: { code: "BOOM", message: "" } }, 500),
    );
    client._transport.setSessionToken("tok");
    await expect(client.auth.signout()).rejects.toThrow();
    expect(client.sessionToken).toBeUndefined();
  });

  it("me returns user", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: { id: "u1", email: "a@b.c" } }),
    );
    const user = await client.auth.me();
    expect((user as { email: string }).email).toBe("a@b.c");
  });

  it("signup stores session token", async () => {
    const { client } = makeClient(() =>
      jsonResponse(
        { ok: true, data: { token: "new_tok", user: { id: "u2" }, session: { id: "s2" } } },
        201,
      ),
    );
    const data = await client.auth.signup({ email: "x@y.z", password: "pw", display_name: "X" });
    expect((data.user as { id: string }).id).toBe("u2");
    expect(client.sessionToken).toBe("new_tok");
  });
});

describe("Auth — sessions", () => {
  it("list", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: [{ id: "s1" }, { id: "s2" }] }),
    );
    const rows = await client.auth.sessions.list();
    expect(rows).toHaveLength(2);
  });

  it("get", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: { id: "s1", ua: "test" } }),
    );
    const row = await client.auth.sessions.get("s1");
    expect((row as { id: string }).id).toBe("s1");
  });

  it("revoke sends DELETE", async () => {
    const { client, calls } = makeClient((url, init) => {
      expect(init.method).toBe("DELETE");
      expect(url).toContain("/v1/sessions/s1");
      return new Response(null, { status: 204 });
    });
    const result = await client.auth.sessions.revoke("s1");
    expect(result).toBeUndefined();
    expect(calls).toHaveLength(1);
  });

  it("update sends PATCH", async () => {
    const { client } = makeClient((url, init) => {
      expect(init.method).toBe("PATCH");
      expect(url).toContain("/v1/sessions/s1");
      return jsonResponse({ ok: true, data: { id: "s1", label: "laptop" } });
    });
    const row = await client.auth.sessions.update("s1", { label: "laptop" });
    expect((row as { label: string }).label).toBe("laptop");
  });
});

describe("Auth — api_keys", () => {
  it("list", async () => {
    const { client } = makeClient(() => jsonResponse({ ok: true, data: [{ id: "k1" }] }));
    const rows = await client.auth.api_keys.list();
    expect(rows).toHaveLength(1);
  });

  it("create returns one-time token", async () => {
    const { client, calls } = makeClient(() =>
      jsonResponse(
        {
          ok: true,
          data: { id: "k1", token: "nk_k1.secret", name: "ci", scopes: ["audit:read"] },
        },
        201,
      ),
    );
    const result = await client.auth.api_keys.create({
      name: "ci",
      scopes: ["audit:read"],
    });
    expect((result as { token: string }).token).toBe("nk_k1.secret");
    const body = calls[0]!.init.body as string;
    expect(body).toContain("ci");
    expect(body).toContain("audit:read");
  });

  it("create passes expires_at when supplied", async () => {
    const { client, calls } = makeClient(() =>
      jsonResponse({ ok: true, data: { id: "k1", token: "nk.x" } }, 201),
    );
    await client.auth.api_keys.create({
      name: "ci",
      scopes: ["s"],
      expires_at: "2027-01-01T00:00:00Z",
    });
    expect(calls[0]!.init.body as string).toContain("2027-01-01");
  });

  it("revoke sends DELETE", async () => {
    const { client } = makeClient((_url, init) => {
      expect(init.method).toBe("DELETE");
      return new Response(null, { status: 204 });
    });
    const result = await client.auth.api_keys.revoke("k1");
    expect(result).toBeUndefined();
  });

  it("rotate returns new token", async () => {
    const { client } = makeClient(() =>
      jsonResponse({ ok: true, data: { id: "k1", token: "nk_k1.new" } }),
    );
    const r = await client.auth.api_keys.rotate("k1");
    expect((r as { token: string }).token).toBe("nk_k1.new");
  });
});
