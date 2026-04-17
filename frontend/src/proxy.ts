import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE = "tennetctl_session";

const PUBLIC_PREFIXES = ["/auth/", "/_next", "/favicon"];

function isPublic(path: string): boolean {
  if (path === "/auth") return true;
  return PUBLIC_PREFIXES.some((p) => path.startsWith(p));
}

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const session = request.cookies.get(SESSION_COOKIE)?.value;

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
