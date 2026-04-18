/**
 * Typed API client for TennetCTL backend.
 *
 * Envelope-aware fetch wrappers. Automatically parses `{ok, data}` and
 * throws ApiClientError on `{ok:false, error}` responses.
 */

import type {
  ApiResponse,
  ListResult,
  PaginatedResponse,
} from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

export class ApiClientError extends Error {
  code: string;
  statusCode: number;

  constructor(code: string, message: string, statusCode: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

const AUTH_ROUTES = ["/auth/", "/setup", "/"];

/**
 * Soft redirect to signin when the backend returns 401 for a user-interacting
 * call. We skip the redirect when:
 *  - we're already on an auth page (prevents loops)
 *  - we're on the landing / or a public-ish page where a sign-in affordance
 *    already exists (e.g. impersonation banner probe fails harmlessly)
 *  - the failing URL is an opt-out probe (impersonation, me, session.validate)
 *    — these legitimately 401 before sign-in and shouldn't bounce the user.
 */
const OPT_OUT_PROBES = [
  "/v1/iam/impersonation",
  "/v1/auth/me",
  "/v1/auth/session",
];

function redirectToSignin(requestUrl?: string): void {
  if (typeof window === "undefined") return;
  const path = window.location.pathname;
  if (path === "/") return;
  if (AUTH_ROUTES.some((p) => path.startsWith(p))) return;
  if (requestUrl && OPT_OUT_PROBES.some((p) => requestUrl.includes(p))) return;
  const next = encodeURIComponent(path + window.location.search);
  window.location.href = `/auth/signin?next=${next}`;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    redirectToSignin(res.url);
    throw new ApiClientError("UNAUTHORIZED", "Session expired", 401);
  }
  if (res.status === 204) return undefined as T;
  const data: ApiResponse<T> = await res.json();
  if (!data.ok) {
    throw new ApiClientError(
      data.error.code,
      data.error.message,
      res.status
    );
  }
  return data.data;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  return handleResponse<T>(res);
}

export async function apiList<T>(
  path: string,
  options?: RequestInit
): Promise<ListResult<T>> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (res.status === 401) {
    redirectToSignin(res.url);
    throw new ApiClientError("UNAUTHORIZED", "Session expired", 401);
  }
  if (res.status === 204) {
    return { items: [], pagination: { total: 0, limit: 0, offset: 0 } };
  }
  const payload = (await res.json()) as
    | PaginatedResponse<T>
    | { ok: false; error: { code: string; message: string } };
  if (!payload.ok) {
    throw new ApiClientError(
      payload.error.code,
      payload.error.message,
      res.status
    );
  }
  return { items: payload.data, pagination: payload.pagination };
}

export function buildQuery(
  params: Record<string, string | number | boolean | null | undefined>
): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== ""
  );
  if (entries.length === 0) return "";
  const search = new URLSearchParams();
  for (const [k, v] of entries) search.set(k, String(v));
  return `?${search.toString()}`;
}
