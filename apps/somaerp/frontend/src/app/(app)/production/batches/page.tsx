"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listBatches, listKitchens } from "@/lib/api";
import type {
  Kitchen,
  ProductionBatch,
  ProductionBatchStatus,
} from "@/types/api";

type LoadState =
  | { status: "loading" }
  | { status: "ok"; items: ProductionBatch[] }
  | { status: "error"; message: string };

const STATUS_COLORS: Record<ProductionBatchStatus, string> = {
  planned: "bg-slate-100 ",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-rose-100 text-rose-800",
};

export default function BatchesListPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [kitchenFilter, setKitchenFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  useEffect(() => {
    void listKitchens().then(setKitchens).catch(() => setKitchens([]));
  }, []);

  const load = useMemo(
    () => async () => {
      setState({ status: "loading" });
      try {
        const items = await listBatches({
          kitchen_id: kitchenFilter || undefined,
          status: (statusFilter || undefined) as ProductionBatchStatus | undefined,
          run_date_from: dateFrom || undefined,
          run_date_to: dateTo || undefined,
          limit: 200,
        });
        setState({ status: "ok", items });
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Unknown error";
        setState({ status: "error", message });
      }
    },
    [kitchenFilter, statusFilter, dateFrom, dateTo]
  );

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <Link
          href="/production"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Production
        </Link>
        <div className="mt-2 flex items-center justify-between gap-3">
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Batches</h1>
          <Link
            href="/production/batches/new"
            className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            + New Batch
          </Link>
        </div>
      </div>

      <div className="mb-5 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="text-sm">
          <span className="mb-1 block font-medium ">Kitchen</span>
          <select
            value={kitchenFilter}
            onChange={(e) => setKitchenFilter(e.target.value)}
            className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All kitchens</option>
            {kitchens.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium ">Status</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All statuses</option>
            <option value="planned">Planned</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium ">From</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium ">To</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </label>
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading batches…</p>
      )}
      {state.status === "error" && (
        <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      )}
      {state.status === "ok" && state.items.length === 0 && (
        <div className="rounded border border-slate-200 bg-white p-6 text-center shadow-sm">
          <p className="">No batches match the filters.</p>
          <Link
            href="/production/batches/new"
            className="mt-3 inline-block rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            Plan your first batch
          </Link>
        </div>
      )}
      {state.status === "ok" && state.items.length > 0 && (
        <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <table className="min-w-full text-sm">
            <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Date</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Product</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Planned</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Actual</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody >
              {state.items.map((b) => (
                <tr key={b.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                  <td className="px-3 py-2 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{b.run_date}</td>
                  <td className="px-3 py-2">{b.kitchen_name ?? "—"}</td>
                  <td className="px-3 py-2">{b.product_name ?? "—"}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[b.status]}`}
                    >
                      {b.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {b.planned_qty}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {b.actual_qty ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Link
                      href={`/production/batches/${b.id}`}
                      className="text-amber-700 hover:underline"
                    >
                      Open →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
