/**
 * somashop product analytics — posts to tennetctl /v1/track.
 *
 * Same shape as tennetctl frontend's track.ts. distinct_id is per-browser
 * (localStorage), session_id is per-tab (sessionStorage). Best-effort —
 * failures swallowed silently.
 */

const TENNETCTL_BASE =
  process.env.NEXT_PUBLIC_TENNETCTL_API_URL ?? "http://localhost:51734";
const STORAGE_KEY = "somashop_distinct_id";
const SESSION_KEY = "somashop_session_id";
const IDENTITY_KEY = "somashop_identity";

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
    properties: { ...properties, app: "somashop" },
    actor_user_id: opts.actor_user_id ?? null,
    org_id: opts.org_id ?? null,
    workspace_id: opts.workspace_id ?? null,
  };
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

export function trackWithIdentity(
  event: string,
  properties: Record<string, unknown> = {},
  opts: TrackOptions = {},
): void {
  const id = readIdentity();
  track(event, properties, { ...id, ...opts });
}
