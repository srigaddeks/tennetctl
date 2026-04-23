"use client";

import Link from "next/link";

import { cn } from "@/lib/cn";

export type BreadcrumbItem = {
  label: string;
  href?: string;
};

export function Breadcrumb({
  items,
  className,
}: {
  items: BreadcrumbItem[];
  className?: string;
}) {
  if (items.length === 0) return null;
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center gap-1 text-[11px]", className)}
      style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
      data-testid="breadcrumb"
    >
      {items.map((item, i) => {
        const last = i === items.length - 1;
        return (
          <span
            key={`${item.label}-${i}`}
            className="flex items-center gap-1"
          >
            {item.href && !last ? (
              <Link
                href={item.href}
                className="transition-colors duration-100 hover:text-[var(--text-primary)]"
              >
                {item.label}
              </Link>
            ) : (
              <span
                aria-current={last ? "page" : undefined}
                style={last ? { color: "var(--text-secondary)" } : undefined}
              >
                {item.label}
              </span>
            )}
            {!last && (
              <span
                aria-hidden
                style={{ color: "var(--border-bright)" }}
                className="text-[10px]"
              >
                /
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
