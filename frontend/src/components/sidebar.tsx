"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import {
  activeFeature,
  activeSubFeatureHref,
  type SubFeatureNav,
} from "@/config/features";
import { cn } from "@/lib/cn";

type GroupedEntry =
  | { kind: "item"; item: SubFeatureNav }
  | { kind: "group"; label: string; items: SubFeatureNav[] };

function groupItems(subFeatures: SubFeatureNav[]): GroupedEntry[] {
  const out: GroupedEntry[] = [];
  let currentGroup: string | null = null;
  let buffer: SubFeatureNav[] = [];

  function flush() {
    if (buffer.length > 0 && currentGroup !== null) {
      out.push({ kind: "group", label: currentGroup, items: buffer });
    }
    currentGroup = null;
    buffer = [];
  }

  for (const item of subFeatures) {
    if (!item.group) {
      flush();
      out.push({ kind: "item", item });
    } else if (item.group === currentGroup) {
      buffer.push(item);
    } else {
      flush();
      currentGroup = item.group;
      buffer = [item];
    }
  }
  flush();
  return out;
}

export function Sidebar() {
  const pathname = usePathname();
  const feature = activeFeature(pathname);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (feature.subFeatures.length === 0) return null;
  const activeHref = activeSubFeatureHref(pathname, feature);
  const grouped = groupItems(feature.subFeatures);

  const nav = (
    <nav className="flex-1 overflow-y-auto px-2 py-3">
      <ul className="flex flex-col gap-px">
        {grouped.map((entry, idx) =>
          entry.kind === "item" ? (
            <NavLink
              key={entry.item.href}
              item={entry.item}
              active={entry.item.href === activeHref}
            />
          ) : (
            <li key={`${entry.label}-${idx}`} className="mt-4 first:mt-0">
              <div
                className="px-2 pb-1.5 text-[9px] font-semibold uppercase tracking-[0.1em]"
                style={{ color: "var(--text-muted)" }}
              >
                {entry.label}
              </div>
              <ul className="flex flex-col gap-px">
                {entry.items.map((item) => (
                  <NavLink
                    key={item.href}
                    item={item}
                    active={item.href === activeHref}
                  />
                ))}
              </ul>
            </li>
          ),
        )}
      </ul>
    </nav>
  );

  const header = (
    <div
      className="px-4 py-3 border-b"
      style={{ borderColor: "var(--border)" }}
    >
      <div
        className="text-[9px] font-semibold uppercase tracking-[0.1em] mb-0.5"
        style={{ color: "var(--text-muted)" }}
      >
        Module
      </div>
      <div
        className="text-[13px] font-semibold tracking-wide"
        style={{ color: "var(--text-primary)" }}
      >
        {feature.label}
      </div>
    </div>
  );

  const sidebarStyle = {
    background: "var(--bg-surface)",
    borderColor: "var(--border)",
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation"
        className="fixed bottom-4 left-4 z-30 flex h-10 w-10 items-center justify-center rounded border text-[var(--text-secondary)] shadow-lg md:hidden transition-colors hover:text-[var(--text-primary)]"
        style={sidebarStyle}
        data-testid="sidebar-mobile-open"
      >
        <span className="font-mono text-base">≡</span>
      </button>

      {/* Desktop sidebar */}
      <aside
        className="hidden w-48 shrink-0 flex-col border-r md:flex"
        style={sidebarStyle}
      >
        {header}
        {nav}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 flex md:hidden"
          data-testid="sidebar-mobile-drawer"
        >
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            aria-hidden
          />
          <aside
            className="relative flex w-56 max-w-[80vw] flex-col border-r"
            style={sidebarStyle}
          >
            <div
              className="flex items-center justify-between border-b px-4 py-3"
              style={{ borderColor: "var(--border)" }}
            >
              <div>
                <div
                  className="text-[9px] font-semibold uppercase tracking-[0.1em] mb-0.5"
                  style={{ color: "var(--text-muted)" }}
                >
                  Module
                </div>
                <div
                  className="text-[13px] font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {feature.label}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label="Close navigation"
                className="flex h-7 w-7 items-center justify-center rounded border transition-colors"
                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
              >
                ✕
              </button>
            </div>
            {nav}
          </aside>
        </div>
      )}
    </>
  );
}

function NavLink({ item, active }: { item: SubFeatureNav; active: boolean }) {
  return (
    <li className="relative">
      <Link
        href={item.href}
        data-testid={item.testId}
        className={cn(
          "relative flex items-center rounded px-2.5 py-1.5 text-[12.5px] transition-all duration-100",
          active
            ? "font-medium"
            : "font-normal hover:bg-[var(--bg-elevated)]",
        )}
        style={
          active
            ? {
                background: "var(--accent-muted)",
                color: "var(--accent-hover)",
                borderLeft: "2px solid var(--accent)",
                paddingLeft: "calc(0.625rem - 2px)",
              }
            : {
                color: "var(--text-secondary)",
              }
        }
      >
        {item.label}
      </Link>
    </li>
  );
}
