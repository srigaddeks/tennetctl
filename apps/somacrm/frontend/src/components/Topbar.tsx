"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import type { SearchResult } from "@/types/api";
import { globalSearch } from "@/lib/api";

function buildBreadcrumbs(pathname: string): Array<{ label: string; href: string }> {
  const crumbs: Array<{ label: string; href: string }> = [
    { label: "somacrm", href: "/" },
  ];
  const segments = pathname.split("/").filter(Boolean);
  let accumulated = "";
  for (const seg of segments) {
    accumulated += "/" + seg;
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(seg);
    const label = isUuid
      ? "Detail"
      : seg.replace(/-/g, " ").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    crumbs.push({ label, href: accumulated });
  }
  return crumbs;
}

const ENTITY_ICON: Record<SearchResult["entity_type"], string> = {
  contact: "👤",
  organization: "🏢",
  lead: "🎯",
  deal: "💰",
};

function entityPath(r: SearchResult): string {
  return `/${r.entity_type}s/${r.id}`;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const crumbs = buildBreadcrumbs(pathname);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    let cancelled = false;
    globalSearch(debouncedQuery)
      .then((res) => {
        if (!cancelled) {
          setResults(res.slice(0, 8));
          setOpen(res.length > 0);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setResults([]);
          setOpen(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const handleSelect = useCallback(
    (r: SearchResult) => {
      setOpen(false);
      setQuery("");
      router.push(entityPath(r));
    },
    [router],
  );

  function handleSignOut() {
    if (typeof window !== "undefined") {
      try {
        window.localStorage.removeItem("somacrm_token");
      } catch {
        // ignore
      }
    }
    document.cookie = "somacrm_token=; path=/; max-age=0; SameSite=Lax";
    router.push("/signin");
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

      {/* Right: search + user + signout */}
      <div className="flex items-center gap-3">
        {/* Global search */}
        <div ref={containerRef} style={{ position: "relative" }}>
          <input
            type="text"
            placeholder="Search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              if (results.length > 0) setOpen(true);
            }}
            style={{
              width: 200,
              fontSize: 12,
              padding: "4px 10px",
              border: "1px solid var(--border)",
              borderRadius: 6,
              background: "var(--bg-input, var(--bg-sidebar))",
              color: "var(--text-primary)",
              fontFamily: "var(--font-ui)",
              outline: "none",
            }}
          />
          {open && results.length > 0 && (
            <ul
              style={{
                position: "absolute",
                top: "calc(100% + 4px)",
                right: 0,
                width: 280,
                background: "var(--bg-topbar)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                boxShadow: "0 4px 16px rgba(0,0,0,0.15)",
                listStyle: "none",
                margin: 0,
                padding: "4px 0",
                zIndex: 100,
                maxHeight: 320,
                overflowY: "auto",
              }}
            >
              {results.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => handleSelect(r)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      width: "100%",
                      padding: "6px 12px",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      textAlign: "left",
                      fontFamily: "var(--font-ui)",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover, rgba(0,0,0,0.05))";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.background = "none";
                    }}
                  >
                    <span style={{ fontSize: 14 }}>{ENTITY_ICON[r.entity_type]}</span>
                    <span style={{ flex: 1, overflow: "hidden" }}>
                      <span
                        style={{
                          display: "block",
                          fontSize: 12,
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {r.title}
                      </span>
                      {r.subtitle && (
                        <span
                          style={{
                            display: "block",
                            fontSize: 11,
                            color: "var(--text-muted)",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {r.subtitle}
                        </span>
                      )}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        color: "var(--text-muted)",
                        textTransform: "capitalize",
                        flexShrink: 0,
                      }}
                    >
                      {r.entity_type}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <span style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "var(--font-ui)" }}>
          CRM
        </span>

        <div className="h-4" style={{ borderLeft: "1px solid var(--border)" }} />

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
