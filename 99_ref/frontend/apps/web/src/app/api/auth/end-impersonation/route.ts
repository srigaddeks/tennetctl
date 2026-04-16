import { NextRequest, NextResponse } from "next/server";

const REFRESH_COOKIE = "kc_refresh";
const ADMIN_REFRESH_COOKIE = "kc_admin_refresh";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * POST /api/auth/end-impersonation
 *
 * 1. Revokes the impersonation session on the backend (using current kc_refresh = impersonation token)
 * 2. Restores kc_refresh from kc_admin_refresh (the saved admin session)
 * 3. Clears kc_admin_refresh
 */
export async function POST(req: NextRequest) {
  const authHeader = req.headers.get("Authorization");
  const impersonationRefreshToken = req.cookies.get(REFRESH_COOKIE)?.value;
  const adminRefreshToken = req.cookies.get(ADMIN_REFRESH_COOKIE)?.value;

  // Best-effort: revoke the impersonation session on the backend
  if (impersonationRefreshToken) {
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/local/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
        body: JSON.stringify({ refresh_token: impersonationRefreshToken }),
      });
    } catch {}
  }

  const res = NextResponse.json({ ok: true });

  if (adminRefreshToken) {
    // Restore admin's original session
    res.cookies.set(REFRESH_COOKIE, adminRefreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
    // Clear the saved admin session cookie
    res.cookies.set(ADMIN_REFRESH_COOKIE, "", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 0,
    });
  } else {
    // No saved admin session — clear everything, redirect to login
    res.cookies.set(REFRESH_COOKIE, "", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: 0,
    });
  }

  return res;
}
