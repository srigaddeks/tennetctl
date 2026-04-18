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
      className={cn(
        "flex items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400",
        className,
      )}
      data-testid="breadcrumb"
    >
      {items.map((item, i) => {
        const last = i === items.length - 1;
        return (
          <span key={`${item.label}-${i}`} className="flex items-center gap-1">
            {item.href && !last ? (
              <Link
                href={item.href}
                className="hover:text-zinc-900 dark:hover:text-zinc-100 transition"
              >
                {item.label}
              </Link>
            ) : (
              <span
                aria-current={last ? "page" : undefined}
                className={cn(last && "text-zinc-900 dark:text-zinc-100 font-medium")}
              >
                {item.label}
              </span>
            )}
            {!last && <span aria-hidden>›</span>}
          </span>
        );
      })}
    </nav>
  );
}
