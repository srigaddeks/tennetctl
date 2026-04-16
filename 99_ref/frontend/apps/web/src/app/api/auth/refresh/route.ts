import { NextRequest, NextResponse } from "next/server";

const REFRESH_COOKIE = "kc_refresh";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const REFRESH_TTL_SECONDS = 60 * 60 * 24 * 30;

/**
 * POST /api/auth/refresh
 *
 * Server-side token rotation. Reads refresh token from httpOnly cookie,
 * calls the backend, and:
 * - Returns the new access_token in the JSON body (for memory storage)
 * - Sets the new refresh_token back into the httpOnly cookie (rotation)
 *
 * This endpoint is called by fetchWithAuth on 401 — the browser never
 * exposes the refresh token to client JS.
 */
export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;

  if (!refreshToken) {
    return NextResponse.json({ error: "No refresh token" }, { status: 401 });
  }

  const backendRes = await fetch(`${API_BASE_URL}/api/v1/auth/local/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!backendRes.ok) {
    // Refresh failed — clear cookie and signal logout
    const res = NextResponse.json({ error: "Session expired" }, { status: 401 });
    res.cookies.set(REFRESH_COOKIE, "", { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "strict", path: "/", maxAge: 0 });
    return res;
  }

  const data = await backendRes.json();

  const res = NextResponse.json({ access_token: data.access_token });
  // Rotate the refresh token cookie
  res.cookies.set(REFRESH_COOKIE, data.refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: REFRESH_TTL_SECONDS,
  });
  return res;
}
