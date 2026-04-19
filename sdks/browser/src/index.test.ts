import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { _internal, init, track, identify, alias, parseUtm, flush } from "./index";

// jsdom-style stubs (vitest auto-detects jsdom; here we use minimal shims)
const stubLocation = (href: string, hostname = "example.com"): void => {
  Object.defineProperty(globalThis, "location", {
    value: { href, hostname, protocol: "https:" },
    writable: true,
    configurable: true,
  });
};

const stubDocument = (): void => {
  let cookies: Record<string, string> = {};
  Object.defineProperty(globalThis, "document", {
    value: {
      get cookie() {
        return Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join("; ");
      },
      set cookie(val: string) {
        const [pair] = val.split(";");
        if (!pair) return;
        const [k, v] = pair.split("=");
        if (!k) return;
        if (val.includes("Max-Age=0")) {
          delete cookies[k];
        } else {
          cookies[k] = v ?? "";
        }
      },
      referrer: "https://t.co/abc",
    },
    writable: true,
    configurable: true,
  });
  // reset on each test
  return;
};

beforeEach(() => {
  _internal.reset();
  stubLocation("https://example.com/landing?utm_source=twitter&utm_campaign=launch");
  stubDocument();
  // Stub localStorage
  const store: Record<string, string> = {};
  Object.defineProperty(globalThis, "localStorage", {
    value: {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
    },
    writable: true,
    configurable: true,
  });
  Object.defineProperty(globalThis, "navigator", {
    value: { doNotTrack: "0" },
    writable: true,
    configurable: true,
  });
});

afterEach(() => {
  _internal.reset();
});

describe("parseUtm", () => {
  it("extracts the full set", () => {
    const utm = parseUtm("https://x.com/?utm_source=twitter&utm_medium=social&utm_campaign=launch&utm_term=ai&utm_content=hero");
    expect(utm).toEqual({
      source: "twitter",
      medium: "social",
      campaign: "launch",
      term: "ai",
      content: "hero",
    });
  });

  it("returns empty when no UTM", () => {
    expect(parseUtm("https://x.com/")).toEqual({});
  });

  it("handles undefined", () => {
    expect(parseUtm(undefined)).toEqual({});
  });

  it("handles malformed URL", () => {
    expect(parseUtm("not-a-url")).toEqual({});
  });
});

describe("init + track", () => {
  it("init stores opts and creates a visitor cookie", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false });
    const opts = _internal.getOpts();
    expect(opts).not.toBeNull();
    expect(opts?.host).toBe("https://api.example.com");
    // After init, the visitor cookie exists in document
    expect(document.cookie).toContain("tnt_vid=");
  });

  it("track without init throws", () => {
    expect(() => track("foo")).toThrow(/init\(\) must be called/);
  });

  it("track enqueues a custom event with utm extracted from URL", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false });
    track("cta_click", { cta: "signup" });
    const q = _internal.getQueue();
    expect(q).toHaveLength(1);
    const ev = q[0];
    expect(ev?.kind).toBe("custom");
    expect(ev?.event_name).toBe("cta_click");
    expect(ev?.utm_source).toBe("twitter");
    expect(ev?.utm_campaign).toBe("launch");
    expect(ev?.properties?.cta).toBe("signup");
  });

  it("auto page_view captures kind=page_view on init", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: true });
    const q = _internal.getQueue();
    expect(q).toHaveLength(1);
    expect(q[0]?.kind).toBe("page_view");
    expect(q[0]?.event_name).toBeUndefined();
  });

  it("autoPageView=false skips initial event", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false });
    expect(_internal.getQueue()).toHaveLength(0);
  });
});

describe("identify", () => {
  it("enqueues an identify event with user_id", () => {
    const fetchMock = vi.fn(async () => new Response("{}"));
    init({
      host: "https://api.example.com",
      projectKey: "pk_test",
      autoPageView: false,
      fetchImpl: fetchMock as unknown as typeof fetch,
    });
    identify("u-123", { plan: "pro" });
    // identify forces flush, so queue should be empty after; check fetch was called
    expect(fetchMock).toHaveBeenCalled();
    const [, init2] = fetchMock.mock.calls[0]!;
    const body = JSON.parse((init2 as RequestInit).body as string);
    expect(body.events[0].kind).toBe("identify");
    expect(body.events[0].properties.user_id).toBe("u-123");
  });
});

describe("alias", () => {
  it("enqueues an alias event", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false });
    alias("v_other_id");
    const q = _internal.getQueue();
    expect(q).toHaveLength(1);
    expect(q[0]?.kind).toBe("alias");
    expect(q[0]?.properties?.alias_anonymous_id).toBe("v_other_id");
  });
});

describe("DNT", () => {
  it("does not enqueue when navigator.doNotTrack='1'", () => {
    Object.defineProperty(globalThis, "navigator", {
      value: { doNotTrack: "1" },
      writable: true,
      configurable: true,
    });
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: true });
    track("anything");
    expect(_internal.getQueue()).toHaveLength(0);
  });
});

describe("flush", () => {
  it("POSTs the batch with project_key", async () => {
    const fetchMock = vi.fn(async () => new Response("{}"));
    init({
      host: "https://api.example.com",
      projectKey: "pk_test",
      autoPageView: false,
      fetchImpl: fetchMock as unknown as typeof fetch,
    });
    track("a");
    track("b");
    await flush(false);

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init2] = fetchMock.mock.calls[0]!;
    expect(url).toBe("https://api.example.com/v1/track");
    const body = JSON.parse((init2 as RequestInit).body as string);
    expect(body.project_key).toBe("pk_test");
    expect(body.events).toHaveLength(2);
  });

  it("re-queues events on fetch failure", async () => {
    const fetchMock = vi.fn(async () => {
      throw new Error("network down");
    });
    init({
      host: "https://api.example.com",
      projectKey: "pk_test",
      autoPageView: false,
      fetchImpl: fetchMock as unknown as typeof fetch,
    });
    track("a");
    await flush(false);
    // Event should be back in the queue for retry
    expect(_internal.getQueue()).toHaveLength(1);
  });
});

describe("PII hashing", () => {
  it("hashes email and phone props", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false, hashPii: true });
    track("signup", { email: "user@example.com", phone: "+15551234567", name: "Alice" });
    const q = _internal.getQueue();
    const props = q[0]?.properties as Record<string, unknown>;
    expect(props.email).toMatch(/^sha256_short:/);
    expect(props.phone).toMatch(/^sha256_short:/);
    // Non-PII passes through
    expect(props.name).toBe("Alice");
  });

  it("hashPii=false leaves PII untouched", () => {
    init({ host: "https://api.example.com", projectKey: "pk_test", autoPageView: false, hashPii: false });
    track("signup", { email: "user@example.com" });
    const q = _internal.getQueue();
    expect((q[0]?.properties as Record<string, unknown>).email).toBe("user@example.com");
  });
});

describe("shortHash determinism", () => {
  it("same input → same hash", () => {
    expect(_internal.shortHash("hello")).toBe(_internal.shortHash("hello"));
  });

  it("different input → different hash", () => {
    expect(_internal.shortHash("a")).not.toBe(_internal.shortHash("b"));
  });
});
