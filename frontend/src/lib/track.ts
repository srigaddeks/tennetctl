/**
 * Tennetctl product analytics — tiny browser SDK.
 *
 * Posts events to /v1/track on the tennetctl backend. distinct_id is stored
 * in localStorage and survives across sessions; auth-context wires it to a
 * tennetctl user via actor_user_id when known.
 *
 * Best-effort: failures swallowed silently — analytics must never break a UX.
 */

const TENNETCTL_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";
const STORAGE_KEY = "tennetctl_distinct_id";
const SESSION_KEY = "tennetctl_session_id";

let cachedDistinctId: string | null = null;
let cachedSessionId: string | null = null;

function safeUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getDistinctId(): string {
  if (cachedDistinctId) return cachedDistinctId;
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = `anon-${safeUuid()}`;
    localStorage.setItem(STORAGE_KEY, id);
  }
  cachedDistinctId = id;
  return id;
}

export function getSessionId(): string {
  if (cachedSessionId) return cachedSessionId;
  if (typeof window === "undefined") return "ssr";
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = `sess-${safeUuid()}`;
    sessionStorage.setItem(SESSION_KEY, id);
  }
  cachedSessionId = id;
  return id;
}

export type TrackOptions = {
  source?: "web" | "mobile" | "server" | "backend" | "other";
  url?: string;
  actor_user_id?: string | null;
  org_id?: string | null;
  workspace_id?: string | null;
};

export function track(
  event: string,
  properties: Record<string, unknown> = {},
  opts: TrackOptions = {},
): void {
  if (typeof window === "undefined") return;
  const body = {
    event,
    distinct_id: getDistinctId(),
    session_id: getSessionId(),
    source: opts.source ?? "web",
    url: opts.url ?? window.location.pathname + window.location.search,
    properties,
    actor_user_id: opts.actor_user_id ?? null,
    org_id: opts.org_id ?? null,
    workspace_id: opts.workspace_id ?? null,
  };
  // Use sendBeacon when available — survives page unload.
  try {
    const json = JSON.stringify(body);
    if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
      const blob = new Blob([json], { type: "application/json" });
      const ok = navigator.sendBeacon(`${TENNETCTL_BASE}/v1/track`, blob);
      if (ok) return;
    }
    void fetch(`${TENNETCTL_BASE}/v1/track`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json,
      keepalive: true,
      credentials: "omit",
    }).catch(() => {});
  } catch {
    /* swallow */
  }
}

/**
 * Identify the current user. Persists actor_user_id locally so future events
 * carry it without callers having to thread it through every call site.
 */
const IDENTITY_KEY = "tennetctl_identity";

export function identify(
  actor_user_id: string | null,
  org_id: string | null = null,
  workspace_id: string | null = null,
): void {
  if (typeof window === "undefined") return;
  try {
    if (actor_user_id) {
      localStorage.setItem(
        IDENTITY_KEY,
        JSON.stringify({ actor_user_id, org_id, workspace_id }),
      );
    } else {
      localStorage.removeItem(IDENTITY_KEY);
    }
  } catch {
    /* swallow */
  }
}

function readIdentity(): {
  actor_user_id: string | null;
  org_id: string | null;
  workspace_id: string | null;
} {
  if (typeof window === "undefined")
    return { actor_user_id: null, org_id: null, workspace_id: null };
  try {
    const raw = localStorage.getItem(IDENTITY_KEY);
    if (!raw) return { actor_user_id: null, org_id: null, workspace_id: null };
    return JSON.parse(raw);
  } catch {
    return { actor_user_id: null, org_id: null, workspace_id: null };
  }
}

/**
 * Same as track() but auto-attaches the persisted identity. Use this from
 * components that don't have access to the auth hook.
 */
export function trackWithIdentity(
  event: string,
  properties: Record<string, unknown> = {},
  opts: TrackOptions = {},
): void {
  const id = readIdentity();
  track(event, properties, { ...id, ...opts });
}
