"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listDeliveryRoutes } from "@/lib/api";
import type { DeliveryRoute, RouteStatus } from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; items: DeliveryRoute[] }
  | { status: "error"; message: string };

const STATUS_LABELS: Record<RouteStatus, string> = {
  active: "Active",
  paused: "Paused",
  decommissioned: "Decommissioned",
};

export default function RoutesListPage() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [statusFilter, setStatusFilter] = useState<RouteStatus | "all">("all");
  const [q, setQ] = useState("");

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    listDeliveryRoutes({
      status: statusFilter === "all" ? undefined : statusFilter,
      q: q || undefined,
    })
      .then((items) => {
        if (!cancelled) setState({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          });
      });
    return () => {
      cancelled = true;
    };
  }, [statusFilter, q]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Routes</h1>
        </div>
        <Link
          href="/delivery/routes/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Route
        </Link>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as RouteStatus | "all")
            }
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="decommissioned">Decommissioned</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Search (name / area / slug)
          </label>
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. KPHB"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading routes…</p>
        )}
        {state.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load routes</p>
            <p className="mt-1 text-sm opacity-80">{state.message}</p>
          </div>
        )}
        {state.status === "ok" && state.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No routes yet. Create one.</p>
          </div>
        )}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Area</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Window</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Customers</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {state.items.map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link
                        href={`/delivery/routes/${r.id}`}
                        className="hover:underline"
                      >
                        {r.name}
                      </Link>
                      <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>{r.slug}</div>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.kitchen_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.area ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                      {r.target_window_start ?? "—"} →{" "}
                      {r.target_window_end ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-center font-mono ">
                      {r.customer_count}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium ">
                        {STATUS_LABELS[r.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
