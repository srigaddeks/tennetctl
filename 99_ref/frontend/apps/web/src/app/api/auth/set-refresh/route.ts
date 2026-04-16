import { NextRequest, NextResponse } from "next/server";

const REFRESH_COOKIE = "kc_refresh";
const REFRESH_TTL_SECONDS = 60 * 60 * 24 * 30; // 30 days — matches backend

/**
 * POST /api/auth/set-refresh
 * Body: { refresh_token: string }
 *
 * Stores the refresh token in an httpOnly, Secure, SameSite=Strict cookie.
 * The browser JS layer never touches the refresh token directly after this point.
 */
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const refreshToken: string | undefined = body?.refresh_token;

  if (!refreshToken || typeof refreshToken !== "string") {
    return NextResponse.json({ error: "Missing refresh_token" }, { status: 400 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(REFRESH_COOKIE, refreshToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: REFRESH_TTL_SECONDS,
  });
  return res;
}

/**
 * DELETE /api/auth/set-refresh
 * Clears the refresh token cookie (logout path).
 */
export async function DELETE(_req: NextRequest) {
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
