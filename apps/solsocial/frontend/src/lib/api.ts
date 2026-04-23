// Thin fetch client. Auth rules:
//  - Auth endpoints (signup/signin/setup) go to tennetctl directly.
//  - All app endpoints (posts, channels, queues, ideas) go to solsocial,
//    which forwards the user's Bearer token to tennetctl for identity.

import type { Envelope } from "@/types/api";

export const TENNETCTL_URL = process.env.NEXT_PUBLIC_TENNETCTL_URL ?? "http://localhost:51734";
export const SOLSOCIAL_URL = process.env.NEXT_PUBLIC_SOLSOCIAL_URL ?? "http://localhost:51834";

const TOKEN_KEY = "solsocial:token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null): void {
  if (typeof window === "undefined") return;
  if (t) window.localStorage.setItem(TOKEN_KEY, t);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(base: string, path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const body = (await res.json()) as Envelope<T>;
  if (!body.ok) throw new Error(body.error?.message || `${res.status}`);
  return body.data;
}

export const tc = {
  get: <T,>(p: string) => request<T>(TENNETCTL_URL, p),
  post: <T,>(p: string, body?: unknown) => request<T>(TENNETCTL_URL, p, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export const ss = {
  get: <T,>(p: string) => request<T>(SOLSOCIAL_URL, p),
  post: <T,>(p: string, body?: unknown) => request<T>(SOLSOCIAL_URL, p, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T,>(p: string, body?: unknown) => request<T>(SOLSOCIAL_URL, p, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  put: <T,>(p: string, body?: unknown) => request<T>(SOLSOCIAL_URL, p, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  del: <T = void,>(p: string) => request<T>(SOLSOCIAL_URL, p, { method: "DELETE" }),
};
