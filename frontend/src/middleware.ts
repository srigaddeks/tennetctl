import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

const SETUP_PATH = "/setup";
const PUBLIC_PATHS = new Set([
  "/setup",
  "/_next",
  "/favicon.ico",
  "/public",
]);

function isPublicPath(pathname: string): boolean {
  if (pathname === SETUP_PATH) return true;
  for (const prefix of PUBLIC_PATHS) {
    if (pathname.startsWith(prefix)) return true;
  }
  return false;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Do not intercept static assets or the setup page itself.
  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  try {
    const res = await fetch(`${API_BASE}/v1/setup/status`, {
      headers: { "Cache-Control": "no-cache" },
      // Short timeout to avoid blocking page renders.
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const body = await res.json();
      if (body?.data?.setup_required === true) {
        const url = request.nextUrl.clone();
        url.pathname = SETUP_PATH;
        return NextResponse.redirect(url);
      }
    }
  } catch {
    // If the backend is unreachable, let the page handle the error.
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
