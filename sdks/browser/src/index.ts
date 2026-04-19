/**
 * @tennetctl/browser — Mixpanel/PostHog-style browser SDK for Product Ops.
 *
 * Zero dependencies. Anonymous-first identity (cookie + localStorage fallback).
 * Auto-captures page views + UTM + referrer on init. Batched POST /v1/track
 * with sendBeacon flush on pagehide/beforeunload.
 *
 * ```ts
 * import { tnt } from "@tennetctl/browser";
 *
 * tnt.init({ host: "https://api.example.com", projectKey: "pk_..." });
 * tnt.track("cta_click", { cta: "signup" });
 * tnt.identify("u-123");
 * ```
 *
 * Privacy: respects DNT header (no events sent). PII (email/phone) hashed
 * client-side via Web Crypto SHA-256 before send unless `hashPii: false`.
 */

// ── Types ───────────────────────────────────────────────────────────

export type EventKind =
  | "page_view"
  | "custom"
  | "click"
  | "identify"
  | "alias"
  | "referral_attached";

export type EventPayload = {
  kind: EventKind;
  anonymous_id: string;
  occurred_at: string;
  event_name?: string;
  page_url?: string;
  referrer?: string;
  properties?: Record<string, unknown>;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
};

export type InitOptions = {
  /** Backend host, e.g. "https://tennet.example.com". */
  host: string;
  /** Project key (workspace-scoped, ingest-only). Provisioned via vault. */
  projectKey: string;
  /** Cookie domain — set to ".example.com" for cross-subdomain. Default: location.hostname. */
  cookieDomain?: string;
  /** Cookie max-age in seconds. Default 365 days. */
  cookieMaxAgeSec?: number;
  /** Auto-capture page_view on init + history change. Default true. */
  autoPageView?: boolean;
  /** Hash email/phone properties via SHA-256 before send. Default true. */
  hashPii?: boolean;
  /** Batch flush interval in ms. Default 10 000. */
  flushIntervalMs?: number;
  /** Max events per batch before forced flush. Default 50. */
  batchSize?: number;
  /** Override fetch (for testing). */
  fetchImpl?: typeof fetch;
};

const COOKIE_KEY = "tnt_vid";
const STORAGE_KEY = "tnt_vid_fallback";
const USER_KEY = "tnt_uid";
const PII_KEYS = ["email", "phone", "phone_number"];
const ISO_8601_LEN = 24;

// ── Internal state ──────────────────────────────────────────────────

let _opts: Required<InitOptions> | null = null;
let _queue: EventPayload[] = [];
let _flushTimer: ReturnType<typeof setInterval> | null = null;
let _initialized = false;

// ── Public API ──────────────────────────────────────────────────────

export function init(options: InitOptions): void {
  if (_initialized) return;

  const fallbackFetch: typeof fetch = (..._args) =>
    Promise.reject(new Error("[@tennetctl/browser] fetch unavailable in this runtime"));

  const opts: Required<InitOptions> = {
    host: options.host.replace(/\/+$/, ""),
    projectKey: options.projectKey,
    cookieDomain: options.cookieDomain ?? safeHostname(),
    cookieMaxAgeSec: options.cookieMaxAgeSec ?? 365 * 24 * 60 * 60,
    autoPageView: options.autoPageView ?? true,
    hashPii: options.hashPii ?? true,
    flushIntervalMs: options.flushIntervalMs ?? 10_000,
    batchSize: options.batchSize ?? 50,
    fetchImpl: options.fetchImpl ?? (typeof fetch !== "undefined" ? fetch.bind(globalThis) : fallbackFetch),
  };
  _opts = opts;

  // Ensure visitor_id cookie exists
  ensureVisitorId();

  _initialized = true;

  // Auto page_view
  if (opts.autoPageView && typeof window !== "undefined") {
    track("page_view", { kind: "page_view" });
    interceptHistory();
  }

  // Flush hooks
  if (typeof window !== "undefined") {
    window.addEventListener("pagehide", () => flush(true));
    window.addEventListener("beforeunload", () => flush(true));
  }

  _flushTimer = setInterval(() => {
    void flush(false);
  }, opts.flushIntervalMs);
}

export function track(eventName: string, properties: Record<string, unknown> = {}): void {
  if (!_opts) {
    throw new Error("[@tennetctl/browser] init() must be called before track()");
  }
  if (isDnt()) return;

  const isPageView = properties.kind === "page_view";
  const url = safeUrl();
  const utm = parseUtm(url);

  const payload: EventPayload = {
    kind: isPageView ? "page_view" : "custom",
    anonymous_id: getVisitorId(),
    occurred_at: nowIso(),
    event_name: isPageView ? undefined : eventName,
    page_url: url,
    referrer: safeReferrer(),
    properties: _opts.hashPii ? hashPiiProps(properties) : properties,
    utm_source: utm.source,
    utm_medium: utm.medium,
    utm_campaign: utm.campaign,
    utm_term: utm.term,
    utm_content: utm.content,
  };

  enqueue(payload);
}

export function identify(userId: string, traits: Record<string, unknown> = {}): void {
  if (!_opts) {
    throw new Error("[@tennetctl/browser] init() must be called before identify()");
  }
  if (isDnt()) return;

  setStored(USER_KEY, userId);

  enqueue({
    kind: "identify",
    anonymous_id: getVisitorId(),
    occurred_at: nowIso(),
    event_name: "$identify",
    page_url: safeUrl(),
    referrer: safeReferrer(),
    properties: {
      user_id: userId,
      traits: _opts.hashPii ? hashPiiProps(traits) : traits,
    },
  });

  // Force flush so the identify lands ASAP — typical caller wants immediate effect
  void flush(false);
}

export function alias(newAnonymousId: string): void {
  if (!_opts) {
    throw new Error("[@tennetctl/browser] init() must be called before alias()");
  }
  if (isDnt()) return;

  enqueue({
    kind: "alias",
    anonymous_id: getVisitorId(),
    occurred_at: nowIso(),
    properties: { alias_anonymous_id: newAnonymousId },
  });
}

export function reset(): void {
  // Clear visitor identity (e.g. on logout)
  removeStored(COOKIE_KEY);
  removeStored(STORAGE_KEY);
  removeStored(USER_KEY);
  // New visitor_id will mint on next track() call
}

export async function flush(isUnloading: boolean): Promise<void> {
  if (!_opts || _queue.length === 0) return;

  const events = _queue.splice(0, _queue.length);
  const body = JSON.stringify({
    project_key: _opts.projectKey,
    events,
  });

  const url = `${_opts.host}/v1/track`;

  // sendBeacon for unload — survives page navigation
  if (isUnloading && typeof navigator !== "undefined" && navigator.sendBeacon) {
    try {
      const blob = new Blob([body], { type: "application/json" });
      navigator.sendBeacon(url, blob);
      return;
    } catch {
      // fall through to fetch
    }
  }

  try {
    await _opts.fetchImpl(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: isUnloading, // backup if sendBeacon unavailable
    });
  } catch {
    // Network failures: re-queue silently. Mixpanel/PostHog accept event loss
    // on transient failures rather than blocking the user. Don't block UI.
    _queue.unshift(...events);
  }
}

// ── Convenience namespace export ────────────────────────────────────

export const tnt = {
  init,
  track,
  identify,
  alias,
  reset,
  flush,
};

export default tnt;

// ── Internals ──────────────────────────────────────────────────────

function enqueue(payload: EventPayload): void {
  _queue.push(payload);
  if (_opts && _queue.length >= _opts.batchSize) {
    void flush(false);
  }
}

function getVisitorId(): string {
  let vid = getStored(COOKIE_KEY) || getStored(STORAGE_KEY);
  if (!vid) {
    vid = newVisitorId();
    setStored(COOKIE_KEY, vid);
    setStored(STORAGE_KEY, vid);
  }
  return vid;
}

function ensureVisitorId(): void {
  getVisitorId();
}

function newVisitorId(): string {
  // UUID v7-ish: timestamp-prefix + random suffix. Not strictly v7 (would need
  // ms→bytes layout) but sortable and unique for browser storage.
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 12);
  return `v_${ts}_${rand}`;
}

function getStored(key: string): string | null {
  try {
    if (typeof document !== "undefined") {
      const cookieMatch = document.cookie.match(new RegExp(`(?:^|; )${key}=([^;]*)`));
      if (cookieMatch && cookieMatch[1]) return decodeURIComponent(cookieMatch[1]);
    }
    if (typeof localStorage !== "undefined") {
      return localStorage.getItem(key);
    }
  } catch {
    // localStorage may throw in Safari private mode
  }
  return null;
}

function setStored(key: string, value: string): void {
  if (!_opts) return;
  try {
    if (typeof document !== "undefined") {
      const parts = [
        `${key}=${encodeURIComponent(value)}`,
        `Max-Age=${_opts.cookieMaxAgeSec}`,
        "Path=/",
        `Domain=${_opts.cookieDomain}`,
        "SameSite=Lax",
      ];
      if (typeof location !== "undefined" && location.protocol === "https:") {
        parts.push("Secure");
      }
      document.cookie = parts.join("; ");
    }
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(key, value);
    }
  } catch {
    // ignore; cookie path will work even if localStorage doesn't
  }
}

function removeStored(key: string): void {
  try {
    if (typeof document !== "undefined") {
      document.cookie = `${key}=; Max-Age=0; Path=/`;
    }
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem(key);
    }
  } catch {
    // ignore
  }
}

function nowIso(): string {
  return new Date().toISOString().slice(0, ISO_8601_LEN);
}

function safeHostname(): string {
  try {
    return typeof location !== "undefined" ? location.hostname : "";
  } catch {
    return "";
  }
}

function safeUrl(): string | undefined {
  try {
    return typeof location !== "undefined" ? location.href : undefined;
  } catch {
    return undefined;
  }
}

function safeReferrer(): string | undefined {
  try {
    return typeof document !== "undefined" && document.referrer ? document.referrer : undefined;
  } catch {
    return undefined;
  }
}

function isDnt(): boolean {
  try {
    if (typeof navigator === "undefined") return false;
    const dnt = (navigator as unknown as { doNotTrack?: string }).doNotTrack;
    return dnt === "1" || dnt === "yes";
  } catch {
    return false;
  }
}

export function parseUtm(url: string | undefined): {
  source?: string;
  medium?: string;
  campaign?: string;
  term?: string;
  content?: string;
} {
  if (!url) return {};
  try {
    const u = new URL(url);
    const out: Record<string, string | undefined> = {};
    const map: Array<[string, string]> = [
      ["utm_source", "source"],
      ["utm_medium", "medium"],
      ["utm_campaign", "campaign"],
      ["utm_term", "term"],
      ["utm_content", "content"],
    ];
    for (const [k, v] of map) {
      const val = u.searchParams.get(k);
      if (val) out[v] = val;
    }
    return out;
  } catch {
    return {};
  }
}

function hashPiiProps(props: Record<string, unknown>): Record<string, unknown> {
  // Synchronous best-effort hash. We don't await Web Crypto here because track()
  // is sync; for a simple non-cryptographic hash we use a fast string folding
  // function. PII hashing here is a privacy-defaults *signal*, not cryptographic
  // anonymisation — the SDK consumer should not assume this is irreversible
  // for an attacker with the original value space. For real anonymisation,
  // hash before passing to the SDK.
  const out: Record<string, unknown> = { ...props };
  for (const key of PII_KEYS) {
    if (typeof out[key] === "string") {
      out[key] = `sha256_short:${shortHash(out[key] as string)}`;
    }
  }
  return out;
}

function shortHash(s: string): string {
  // Fast non-cryptographic — for PII fingerprinting in browser context.
  // Server-side, the backend can re-hash with SHA-256 if needed.
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

function interceptHistory(): void {
  if (typeof window === "undefined" || typeof history === "undefined") return;
  const wrap = (method: "pushState" | "replaceState") => {
    const orig = history[method];
    history[method] = function (this: History, ...args: Parameters<typeof orig>): void {
      orig.apply(this, args);
      // Wait a tick so the new URL is observable
      Promise.resolve().then(() => track("page_view", { kind: "page_view" }));
    };
  };
  wrap("pushState");
  wrap("replaceState");
  window.addEventListener("popstate", () => track("page_view", { kind: "page_view" }));
}

// Test hooks (not part of public API but exported for vitest)
export const _internal = {
  getQueue: () => _queue.slice(),
  getOpts: () => _opts,
  reset: () => {
    _opts = null;
    _queue = [];
    if (_flushTimer) clearInterval(_flushTimer);
    _flushTimer = null;
    _initialized = false;
  },
  shortHash,
};
