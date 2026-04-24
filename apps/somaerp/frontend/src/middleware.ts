import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("somaerp_token")?.value;
  const { pathname } = request.nextUrl;

  // Allow auth pages through
  if (pathname.startsWith("/login") || pathname.startsWith("/signup")) {
    // If already authenticated, redirect to home
    if (token) return NextResponse.redirect(new URL("/", request.url));
    return NextResponse.next();
  }

  // All other pages require token
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
