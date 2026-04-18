"use client";

/**
 * Command palette — ⌘K / Ctrl+K opens a fuzzy-match list of every nav entry
 * across all features, plus quick actions. Keyboard-first.
 */

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { FEATURES } from "@/config/features";
import { cn } from "@/lib/cn";

type Item = {
  id: string;
  label: string;
  group: string;
  href: string;
};

function collectItems(): Item[] {
  const out: Item[] = [];
  for (const f of FEATURES) {
    if (f.subFeatures.length === 0) {
      out.push({
        id: `feature-${f.key}`,
        label: f.label,
        group: "Features",
        href: f.basePath,
      });
      continue;
    }
    for (const sf of f.subFeatures) {
      const groupLabel = sf.group
        ? `${f.label} · ${sf.group}`
        : f.label;
      out.push({
        id: sf.href,
        label: sf.label,
        group: groupLabel,
        href: sf.href,
      });
    }
  }
  return out;
}

const ALL_ITEMS = collectItems();

function match(q: string, item: Item): boolean {
  if (!q) return true;
  const needle = q.toLowerCase();
  return (
    item.label.toLowerCase().includes(needle) ||
    item.group.toLowerCase().includes(needle) ||
    item.href.toLowerCase().includes(needle)
  );
}

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    setQuery("");
    setActiveIdx(0);
  }, []);

  // Global ⌘K / Ctrl+K toggle + Escape close
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery("");
        setActiveIdx(0);
      } else if (e.key === "Escape" && open) {
        close();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  // Focus input when opened
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const filtered = useMemo(() => {
    const hits = ALL_ITEMS.filter((i) => match(query, i));
    // Group-preserving order
    return hits.slice(0, 30);
  }, [query]);

  const grouped = useMemo(() => {
    const m = new Map<string, Item[]>();
    for (const item of filtered) {
      const arr = m.get(item.group) ?? [];
      arr.push(item);
      m.set(item.group, arr);
    }
    return Array.from(m.entries());
  }, [filtered]);

  // Reset cursor when filter changes
  useEffect(() => {
    setActiveIdx(0);
  }, [query]);

  const navigate = useCallback(
    (item: Item) => {
      close();
      router.push(item.href);
    },
    [close, router],
  );

  function onKeyDownInput(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pick = filtered[activeIdx];
      if (pick) navigate(pick);
    }
  }

  // Scroll active row into view
  useEffect(() => {
    if (!listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-active="true"]`,
    );
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIdx, filtered]);

  if (!open) return null;

  let linearIdx = -1;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center bg-black/40 pt-24 backdrop-blur-sm"
      onClick={close}
      data-testid="command-palette-backdrop"
    >
      <div
        className="w-full max-w-xl overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
        onClick={(e) => e.stopPropagation()}
        data-testid="command-palette"
      >
        <div className="flex items-center gap-3 border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
          <span className="text-xs text-zinc-400">⌘K</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDownInput}
            placeholder="Jump to any page…"
            className="w-full border-0 bg-transparent text-sm outline-none placeholder:text-zinc-400 dark:text-zinc-50"
            data-testid="command-palette-input"
          />
          <button
            type="button"
            onClick={close}
            className="text-xs text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
          >
            Esc
          </button>
        </div>

        <ul
          ref={listRef}
          className="max-h-96 divide-y divide-zinc-100 overflow-y-auto dark:divide-zinc-900"
        >
          {grouped.length === 0 && (
            <li className="px-4 py-8 text-center text-sm text-zinc-400">
              No matches.
            </li>
          )}
          {grouped.map(([group, items]) => (
            <li key={group} className="px-2 py-2">
              <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                {group}
              </div>
              <ul className="flex flex-col gap-0.5">
                {items.map((item) => {
                  linearIdx += 1;
                  const active = linearIdx === activeIdx;
                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => navigate(item)}
                        onMouseEnter={() => setActiveIdx(linearIdx)}
                        data-active={active}
                        className={cn(
                          "flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition",
                          active
                            ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                            : "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900",
                        )}
                      >
                        <span>{item.label}</span>
                        <span
                          className={cn(
                            "font-mono text-[10px]",
                            active
                              ? "text-white/70 dark:text-zinc-600"
                              : "text-zinc-400",
                          )}
                        >
                          {item.href}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-3 border-t border-zinc-200 px-4 py-2 text-[10px] text-zinc-400 dark:border-zinc-800">
          <span>↑↓ navigate</span>
          <span>↵ open</span>
          <span>esc close</span>
        </div>
      </div>
    </div>
  );
}
