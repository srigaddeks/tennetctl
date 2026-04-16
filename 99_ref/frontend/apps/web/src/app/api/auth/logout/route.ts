import { NextRequest, NextResponse } from "next/server";

const REFRESH_COOKIE = "kc_refresh";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * POST /api/auth/logout
 *
 * Server-side logout. Reads the httpOnly refresh token cookie, calls the
 * backend to revoke the session, then clears the cookie.
 * Always clears the cookie regardless of backend response.
 */
export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;
  const authHeader = req.headers.get("Authorization");

  // Best-effort backend session revocation
  if (refreshToken) {
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/local/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Continue with cookie cleanup regardless
    }
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(REFRESH_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return res;
}
