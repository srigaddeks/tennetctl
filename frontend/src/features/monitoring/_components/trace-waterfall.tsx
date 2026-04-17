"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { SpanRow } from "@/types/api";

type Props = {
  spans: SpanRow[];
};

type Node = SpanRow & { depth: number; startNs: number; endNs: number };

function hashServiceColor(name: string | null | undefined): string {
  if (!name) return "#94a3b8";
  let h = 0;
  for (let i = 0; i < name.length; i += 1) {
    h = (h * 31 + name.charCodeAt(i)) >>> 0;
  }
  const hue = h % 360;
  return `hsl(${hue}, 65%, 55%)`;
}

function flatten(spans: SpanRow[]): Node[] {
  const byId = new Map<string, SpanRow>();
  const children = new Map<string | null, SpanRow[]>();
  for (const s of spans) {
    byId.set(s.span_id, s);
    const parent = s.parent_span_id ?? null;
    const list = children.get(parent) ?? [];
    list.push(s);
    children.set(parent, list);
  }
  // Sort each child list by recorded_at
  for (const list of children.values()) {
    list.sort((a, b) => (a.recorded_at < b.recorded_at ? -1 : 1));
  }
  // Find roots: parents not in byId
  const roots: SpanRow[] = [];
  for (const s of spans) {
    if (!s.parent_span_id || !byId.has(s.parent_span_id)) roots.push(s);
  }
  roots.sort((a, b) => (a.recorded_at < b.recorded_at ? -1 : 1));

  const out: Node[] = [];
  const walk = (span: SpanRow, depth: number) => {
    const startMs = new Date(span.recorded_at).getTime();
    const durNs = span.duration_ns ?? 0;
    const startNs = startMs * 1_000_000;
    const endNs = startNs + durNs;
    out.push({ ...span, depth, startNs, endNs });
    const kids = children.get(span.span_id) ?? [];
    for (const k of kids) walk(k, depth + 1);
  };
  for (const r of roots) walk(r, 0);
  return out;
}

export function TraceWaterfall({ spans }: Props) {
  const nodes = useMemo(() => flatten(spans), [spans]);
  const [selectedId, setSelectedId] = useState<string | null>(
    nodes[0]?.span_id ?? null,
  );

  const bounds = useMemo(() => {
    if (nodes.length === 0) return { start: 0, end: 1 };
    const start = Math.min(...nodes.map((n) => n.startNs));
    const end = Math.max(...nodes.map((n) => n.endNs));
    return { start, end: end === start ? start + 1 : end };
  }, [nodes]);

  const selected = useMemo(
    () => nodes.find((n) => n.span_id === selectedId) ?? null,
    [nodes, selectedId],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target && (e.target as HTMLElement).tagName === "INPUT") return;
      const idx = nodes.findIndex((n) => n.span_id === selectedId);
      if (e.key === "j" && idx < nodes.length - 1) {
        setSelectedId(nodes[idx + 1].span_id);
      } else if (e.key === "k" && idx > 0) {
        setSelectedId(nodes[idx - 1].span_id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [nodes, selectedId]);

  if (nodes.length === 0) {
    return (
      <EmptyState
        title="No spans"
        description="This trace has no span data."
      />
    );
  }

  const totalMs = (bounds.end - bounds.start) / 1_000_000;

  return (
    <div
      className="grid grid-cols-1 gap-4 lg:grid-cols-[2fr_1fr]"
      data-testid="monitoring-trace-waterfall"
    >
      <div className="overflow-auto rounded-xl border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mb-2 text-[11px] text-zinc-500">
          Total: {totalMs.toFixed(2)} ms · {nodes.length} spans · j/k to navigate
        </div>
        <ul className="flex flex-col gap-1">
          {nodes.map((n) => {
            const offsetPct = ((n.startNs - bounds.start) / (bounds.end - bounds.start)) * 100;
            const widthPct = Math.max(
              0.3,
              ((n.endNs - n.startNs) / (bounds.end - bounds.start)) * 100,
            );
            const color = hashServiceColor(n.service_name);
            const active = n.span_id === selectedId;
            return (
              <li key={n.span_id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(n.span_id)}
                  data-testid={`monitoring-trace-span-${n.span_id}`}
                  className={cn(
                    "flex w-full items-center gap-2 rounded px-2 py-1 text-left text-[11px] transition",
                    active
                      ? "bg-zinc-100 dark:bg-zinc-900"
                      : "hover:bg-zinc-50 dark:hover:bg-zinc-900/60",
                  )}
                >
                  <span
                    className="w-48 shrink-0 truncate font-mono text-[11px] text-zinc-700 dark:text-zinc-300"
                    style={{ paddingLeft: `${n.depth * 12}px` }}
                  >
                    {n.name}
                  </span>
                  <span className="w-20 shrink-0 truncate text-[10px] text-zinc-500">
                    {n.service_name ?? "—"}
                  </span>
                  <div className="relative h-4 flex-1 rounded bg-zinc-100 dark:bg-zinc-900">
                    <div
                      className="absolute top-0 h-full rounded"
                      style={{
                        left: `${offsetPct}%`,
                        width: `${widthPct}%`,
                        background: color,
                      }}
                    />
                  </div>
                  <span className="w-16 shrink-0 text-right font-mono text-[10px] text-zinc-500">
                    {((n.duration_ns ?? 0) / 1_000_000).toFixed(2)}ms
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
      <aside className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
        {selected ? (
          <>
            <h3 className="mb-2 text-sm font-semibold">{selected.name}</h3>
            <dl className="space-y-1 text-[11px]">
              <div>
                <dt className="inline text-zinc-500">span_id:</dt>{" "}
                <dd className="inline font-mono">{selected.span_id}</dd>
              </div>
              <div>
                <dt className="inline text-zinc-500">parent:</dt>{" "}
                <dd className="inline font-mono">
                  {selected.parent_span_id ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="inline text-zinc-500">service:</dt>{" "}
                <dd className="inline">{selected.service_name ?? "—"}</dd>
              </div>
              <div>
                <dt className="inline text-zinc-500">kind:</dt>{" "}
                <dd className="inline">{selected.kind_code ?? "—"}</dd>
              </div>
              <div>
                <dt className="inline text-zinc-500">status:</dt>{" "}
                <dd className="inline">{selected.status_code ?? "—"}</dd>
              </div>
              <div>
                <dt className="inline text-zinc-500">duration:</dt>{" "}
                <dd className="inline">
                  {((selected.duration_ns ?? 0) / 1_000_000).toFixed(3)} ms
                </dd>
              </div>
            </dl>
            <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap break-all rounded-md bg-zinc-900 p-3 text-[11px] text-zinc-100">
              {JSON.stringify(selected, null, 2)}
            </pre>
          </>
        ) : (
          <p className="text-xs text-zinc-500">Select a span to inspect.</p>
        )}
      </aside>
    </div>
  );
}
