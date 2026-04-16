"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { FEATURES, activeFeature } from "@/config/features";
import { cn } from "@/lib/cn";

export function TopBar() {
  const pathname = usePathname();
  const current = activeFeature(pathname);
  return (
    <header className="flex h-14 shrink-0 items-center gap-6 border-b border-zinc-200 bg-white px-5 dark:border-zinc-800 dark:bg-zinc-950">
      <Link href="/" className="flex items-center gap-2" data-testid="topbar-logo">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-900 text-xs font-bold text-white dark:bg-zinc-100 dark:text-zinc-900">
          T
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">TennetCTL</div>
          <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
            v0.1 · self-hosted
          </div>
        </div>
      </Link>
      <nav className="flex items-center gap-1">
        {FEATURES.map((f) => {
          const active = f.key === current.key;
          const landing = f.subFeatures[0]?.href ?? f.basePath;
          return (
            <Link
              key={f.key}
              href={landing}
              data-testid={f.testId}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm transition",
                active
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900"
              )}
            >
              {f.label}
            </Link>
          );
        })}
      </nav>
      <div className="ml-auto text-[10px] text-zinc-500 dark:text-zinc-400">
        AGPL-3 · self-hostable
      </div>
    </header>
  );
}
