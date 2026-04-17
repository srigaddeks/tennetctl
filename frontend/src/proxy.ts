import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE = "tennetctl_session";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

const PUBLIC_PREFIXES = ["/auth/", "/_next", "/favicon"];
const SETUP_PATH = "/setup";

function isPublic(path: string): boolean {
  if (path === "/auth") return true;
  if (path === SETUP_PATH) return true;
  return PUBLIC_PREFIXES.some((p) => path.startsWith(p));
}

export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const session = request.cookies.get(SESSION_COOKIE)?.value;

  // Step 1: check setup mode (before auth checks).
  // Skip the setup check on the /setup page itself to avoid redirect loop.
  if (pathname !== SETUP_PATH) {
    try {
      const res = await fetch(`${API_BASE}/v1/setup/status`, {
        signal: AbortSignal.timeout(3000),
        headers: { "Cache-Control": "no-cache" },
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
      // Backend unreachable — let the page handle the error gracefully.
    }
  }

  // Step 2: auth guard.
  if (!session && !isPublic(pathname)) {
    const url = new URL("/auth/signin", request.url);
    if (pathname !== "/") {
      url.searchParams.set("next", pathname + search);
    }
    return NextResponse.redirect(url);
  }
  if (session && (pathname === "/auth/signin" || pathname === "/auth/signup")) {
    return NextResponse.redirect(new URL("/", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
