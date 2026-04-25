"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getMe, setToken } from "@/lib/api";

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    void getMe().then((me) => {
      setName(me?.user.display_name ?? null);
    });
  }, [pathname]);

  function signOut() {
    setToken(null);
    setName(null);
    router.push("/signin");
  }

  return (
    <header
      className="border-b"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
        height: "var(--topbar-height)",
      }}
    >
      <div
        className="mx-auto h-full flex items-center justify-between px-6"
        style={{ maxWidth: "var(--content-max)" }}
      >
        <Link href="/" className="font-heading text-xl font-bold tracking-tight">
          Soma Delights
        </Link>
        <nav className="hidden md:flex gap-8 text-sm">
          <Link
            href="/"
            style={{
              color: pathname === "/" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            Home
          </Link>
          <Link
            href="/products"
            style={{
              color: pathname === "/products" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            Products
          </Link>
          <Link
            href="/orders"
            style={{
              color: pathname === "/orders" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            Orders
          </Link>
        </nav>
        {name ? (
          <div className="flex items-center gap-3 text-sm">
            <span style={{ color: "var(--text-muted)" }}>{name}</span>
            <button onClick={signOut} className="btn btn-ghost" style={{ padding: "4px 12px", fontSize: 12 }}>
              Sign out
            </button>
          </div>
        ) : (
          <Link href="/signin" className="btn btn-primary" style={{ padding: "6px 14px", fontSize: 13 }}>
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
