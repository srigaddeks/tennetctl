"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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
  if (feature.subFeatures.length === 0) return null;
  const activeHref = activeSubFeatureHref(pathname, feature);
  const grouped = groupItems(feature.subFeatures);

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
          {grouped.map((entry, idx) =>
            entry.kind === "item" ? (
              <NavLink
                key={entry.item.href}
                item={entry.item}
                active={entry.item.href === activeHref}
              />
            ) : (
              <li key={`${entry.label}-${idx}`} className="mt-3 first:mt-0">
                <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-600">
                  {entry.label}
                </div>
                <ul className="flex flex-col gap-0.5">
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
    </aside>
  );
}

function NavLink({ item, active }: { item: SubFeatureNav; active: boolean }) {
  return (
    <li>
      <Link
        href={item.href}
        data-testid={item.testId}
        className={cn(
          "flex items-center rounded-md px-2 py-1.5 text-sm transition",
          active
            ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
            : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900",
        )}
      >
        {item.label}
      </Link>
    </li>
  );
}
