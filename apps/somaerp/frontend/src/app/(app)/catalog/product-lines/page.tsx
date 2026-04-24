"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listProductLines } from "@/lib/api";
import type { ProductLine, ProductLineStatus } from "@/types/api";

type LoadState = { status: "loading" } | { status: "ok"; items: ProductLine[] } | { status: "error"; message: string };

export default function ProductLinesListPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    listProductLines()
      .then((items) => { if (!cancelled) setState({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setState({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Product Lines</h1>
        <Link href="/catalog/product-lines/new" className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
          + New Product Line
        </Link>
      </div>
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading product lines…</p>}
        {state.status === "error" && <ErrBox msg={state.message} label="Failed to load product lines" />}
        {state.status === "ok" && state.items.length === 0 && <EmptyBox msg="No product lines yet." />}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <Thead cols={["Name", "Slug", "Category", "Status", "Created"]} />
              <tbody>
                {state.items.map((line, idx) => (
                  <Tr key={line.id} idx={idx}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{line.name}</td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{line.slug}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{line.category_name}</td>
                    <td className="px-4 py-2.5"><StatusPill status={line.status} /></td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-muted)" }}>{fmtDate(line.created_at)}</td>
                  </Tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: ProductLineStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : status === "paused"
    ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
    : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}

function Thead({ cols }: { cols: string[] }) {
  return (
    <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
      <tr>
        {cols.map((h) => <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>)}
      </tr>
    </thead>
  );
}

function Tr({ children, idx }: { children: React.ReactNode; idx: number }) {
  return (
    <tr style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
      {children}
    </tr>
  );
}

function ErrBox({ msg, label }: { msg: string; label: string }) {
  return (
    <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
      <span className="font-semibold">{label}</span> <span className="opacity-80">{msg}</span>
    </div>
  );
}

function EmptyBox({ msg }: { msg: string }) {
  return <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>{msg}</div>;
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}
