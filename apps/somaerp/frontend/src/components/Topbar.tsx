"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type HealthState = "loading" | "ok" | "error";

function useBackendHealth(): HealthState {
  const [state, setState] = useState<HealthState>("loading");

  useEffect(() => {
    let cancelled = false;
    apiFetch("/v1/somaerp/health")
      .then(() => {
        if (!cancelled) setState("ok");
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

function buildBreadcrumbs(pathname: string): Array<{ label: string; href: string }> {
  const crumbs: Array<{ label: string; href: string }> = [
    { label: "somaerp", href: "/" },
  ];
  const segments = pathname.split("/").filter(Boolean);
  let accumulated = "";
  for (const seg of segments) {
    accumulated += "/" + seg;
    const label = seg
      .replace(/-/g, " ")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    crumbs.push({ label, href: accumulated });
  }
  return crumbs;
}

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const health = useBackendHealth();
  const crumbs = buildBreadcrumbs(pathname);

  function handleSignOut() {
    if (typeof window !== "undefined") {
      try {
        window.localStorage.removeItem("somaerp_token");
      } catch {
        // ignore
      }
    }
    document.cookie = "somaerp_token=; path=/; max-age=0; SameSite=Lax";
    router.push("/login");
  }

  return (
    <header
      className="fixed flex items-center justify-between px-5"
      style={{
        left: "var(--sidebar-width)",
        top: 0,
        right: 0,
        height: "var(--topbar-height)",
        backgroundColor: "var(--bg-topbar)",
        borderBottom: "1px solid var(--border)",
        zIndex: 10,
        fontFamily: "var(--font-ui)",
      }}
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1">
            {i > 0 && (
              <span style={{ color: "var(--text-muted)", margin: "0 2px", fontSize: 13 }} className="select-none">
                /
              </span>
            )}
            {i === crumbs.length - 1 ? (
              <span
                style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: 13, fontFamily: "var(--font-ui)" }}
              >
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="transition-colors hover:underline"
                style={{ color: "var(--text-secondary)", fontSize: 13, fontFamily: "var(--font-ui)" }}
              >
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right: status + user */}
      <div className="flex items-center gap-3">
        {/* Backend status dot */}
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{
              backgroundColor:
                health === "ok"
                  ? "var(--status-active)"
                  : health === "error"
                  ? "var(--status-error)"
                  : "var(--text-muted)",
              boxShadow: health === "ok" ? "0 0 0 2px rgba(5,150,105,0.2)" : undefined,
            }}
            title={
              health === "ok"
                ? "Backend connected"
                : health === "error"
                ? "Backend unreachable"
                : "Checking…"
            }
          />
          <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-ui)" }}>
            {health === "ok" ? "connected" : health === "error" ? "offline" : "…"}
          </span>
        </div>

        <div
          className="h-4"
          style={{ borderLeft: "1px solid var(--border)" }}
        />

        <span style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "var(--font-ui)" }}>
          admin@example.com
        </span>

        <div
          className="h-4"
          style={{ borderLeft: "1px solid var(--border)" }}
        />

        <button
          onClick={handleSignOut}
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: "var(--text-muted)",
            background: "none",
            border: "none",
            padding: "3px 0",
            cursor: "pointer",
            transition: "color 0.15s",
            fontFamily: "var(--font-ui)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--status-error)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--text-muted)";
          }}
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
