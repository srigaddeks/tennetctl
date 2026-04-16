import { NextRequest, NextResponse } from "next/server";

const REFRESH_COOKIE = "kc_refresh";
const ADMIN_REFRESH_COOKIE = "kc_admin_refresh";

/**
 * POST /api/auth/save-admin-session
 *
 * Copies the current kc_refresh cookie value into kc_admin_refresh,
 * so it can be restored after impersonation ends.
 * Both cookies are httpOnly — JS never sees the token values.
 */
export async function POST(req: NextRequest) {
  const currentRefresh = req.cookies.get(REFRESH_COOKIE)?.value;

  if (!currentRefresh) {
    return NextResponse.json({ error: "No active session" }, { status: 400 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_REFRESH_COOKIE, currentRefresh, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 60 * 60 * 4, // 4h — impersonation sessions are short-lived
  });
  return res;
}

/**
 * DELETE /api/auth/save-admin-session
 * Clears the saved admin refresh cookie.
 */
export async function DELETE(_req: NextRequest) {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_REFRESH_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return res;
}
