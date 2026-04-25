"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getMe, setToken } from "@/lib/api";
import { readCart } from "@/lib/cart";
import { PageViewTracker } from "@/lib/track-router";
import { identify, track } from "@/lib/track";

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [name, setName] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [cartPlan, setCartPlanState] = useState<string | null>(null);

  useEffect(() => {
    void getMe().then((me) => {
      setName(me?.user.display_name ?? null);
      setUserId(me?.user.id ?? null);
    });
    setCartPlanState(readCart().plan_slug);
  }, [pathname]);

  function signOut() {
    track("auth.signed_out", {}, { actor_user_id: userId });
    identify(null);
    setToken(null);
    setName(null);
    setUserId(null);
    router.push("/signin");
  }

  const cartHref = cartPlan ? `/checkout?plan=${cartPlan}` : "/products";
  const cartLabel = cartPlan ? `Cart · 1` : null;

  return (
    <header
      className="border-b"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
        height: "var(--topbar-height)",
      }}
    >
      <PageViewTracker actorUserId={userId} />
      <div
        className="mx-auto h-full flex items-center justify-between px-6"
        style={{ maxWidth: "var(--content-max)" }}
      >
        <Link
          href="/"
          className="font-heading text-xl font-bold tracking-tight"
        >
          Soma Delights
        </Link>
        <nav className="hidden md:flex gap-8 text-sm">
          <Link
            href="/"
            style={{
              color:
                pathname === "/"
                  ? "var(--text-primary)"
                  : "var(--text-muted)",
            }}
          >
            Home
          </Link>
          <Link
            href="/products"
            style={{
              color:
                pathname?.startsWith("/products")
                  ? "var(--text-primary)"
                  : "var(--text-muted)",
            }}
          >
            Menu
          </Link>
          <Link
            href="/orders"
            style={{
              color:
                pathname === "/orders"
                  ? "var(--text-primary)"
                  : "var(--text-muted)",
            }}
          >
            Orders
          </Link>
          <Link
            href="/profile"
            style={{
              color:
                pathname === "/profile"
                  ? "var(--text-primary)"
                  : "var(--text-muted)",
            }}
          >
            Profile
          </Link>
        </nav>
        <div className="flex items-center gap-3 text-sm">
          {cartLabel && (
            <Link
              href={cartHref}
              className="text-xs uppercase tracking-widest font-semibold px-3 py-1 rounded"
              style={{
                background: "var(--bg-inverse)",
                color: "var(--text-on-inverse)",
              }}
            >
              {cartLabel}
            </Link>
          )}
          {name ? (
            <>
              <span
                className="hidden sm:inline"
                style={{ color: "var(--text-muted)" }}
              >
                {name}
              </span>
              <button
                onClick={signOut}
                className="btn btn-ghost"
                style={{ padding: "4px 12px", fontSize: 12 }}
              >
                Sign out
              </button>
            </>
          ) : (
            <Link
              href="/signin"
              className="btn btn-primary"
              style={{ padding: "6px 14px", fontSize: 13 }}
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
