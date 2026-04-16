export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://127.0.0.1:3000";

// ─── Org / Workspace Session Store ───────────────────────────────────────────
// Written by OrgWorkspaceContext whenever selection changes.
// Read by GRC API functions to inject org_id/workspace_id into every request.

const SS_ORG_KEY = "kcontrol:session:orgId";
const SS_WS_KEY  = "kcontrol:session:workspaceId";

export function setSessionOrg(orgId: string) {
  if (typeof window !== "undefined") sessionStorage.setItem(SS_ORG_KEY, orgId);
}

export function setSessionWorkspace(wsId: string) {
  if (typeof window !== "undefined") sessionStorage.setItem(SS_WS_KEY, wsId);
}

export function getSessionOrg(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(SS_ORG_KEY) ?? "";
}

export function getSessionWorkspace(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(SS_WS_KEY) ?? "";
}

// ─── In-Memory Token Store ───────────────────────────────────────────────────
// Access token in JS module memory — never localStorage or a readable cookie.
// Lost on hard page reload; transparently re-issued from the httpOnly refresh cookie.

let _accessToken: string | null = null;
let _refreshing: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

export function clearAccessToken() {
  _accessToken = null;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

// ─── Token Refresh ────────────────────────────────────────────────────────────
// Returns null if no valid session — callers handle redirect themselves.

async function refreshAccessToken(): Promise<string | null> {
  if (_refreshing) return _refreshing;

  _refreshing = (async () => {
    try {
      const res = await fetch("/api/auth/refresh", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        _accessToken = data.access_token;
        return _accessToken;
      }
      // No valid cookie — return null, let callers decide what to do
      _accessToken = null;
      return null;
    } catch {
      _accessToken = null;
      return null;
    }
  })().finally(() => {
    _refreshing = null;
  });

  return _refreshing;
}

// ─── fetchWithAuth ────────────────────────────────────────────────────────────

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  // If no token in memory, try to refresh from httpOnly cookie
  if (!_accessToken) {
    await refreshAccessToken();
  }

  // Still no token — return 401 so callers can handle (redirect, show error, etc.)
  if (!_accessToken) return new Response(null, { status: 401 });

  const headers = new Headers(options.headers);
  // Only set Content-Type for non-FormData requests — let browser set multipart boundary for file uploads
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Authorization", `Bearer ${_accessToken}`);

  let response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers, credentials: "include" });

  if (response.status === 401) {
    // Token expired mid-session — rotate once
    _accessToken = null;
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers, credentials: "include" });
    }
  }

  return response;
}
