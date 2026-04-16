"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { activeFeature, activeSubFeatureHref } from "@/config/features";
import { cn } from "@/lib/cn";

export function Sidebar() {
  const pathname = usePathname();
  const feature = activeFeature(pathname);
  if (feature.subFeatures.length === 0) return null;
  const activeHref = activeSubFeatureHref(pathname, feature);
  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
          Feature
        </div>
        <div className="text-sm font-semibold">{feature.label}</div>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="flex flex-col gap-0.5">
          {feature.subFeatures.map((item) => {
            const active = item.href === activeHref;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  data-testid={item.testId}
                  className={cn(
                    "flex items-center rounded-md px-2 py-1.5 text-sm transition",
                    active
                      ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                      : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900"
                  )}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
