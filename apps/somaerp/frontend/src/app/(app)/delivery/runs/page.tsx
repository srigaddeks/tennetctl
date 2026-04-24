"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listDeliveryRoutes, listDeliveryRuns, listRiders } from "@/lib/api";
import type {
  DeliveryRoute,
  DeliveryRun,
  DeliveryRunStatus,
  Rider,
} from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; items: DeliveryRun[] }
  | { status: "error"; message: string };

const STATUS_STYLES: Record<DeliveryRunStatus, string> = {
  planned: "bg-slate-200 text-slate-800",
  in_transit: "bg-amber-200 text-amber-900",
  completed: "bg-emerald-200 text-emerald-900",
  cancelled: "bg-rose-200 text-rose-900",
};

export default function RunsListPage() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [routes, setRoutes] = useState<DeliveryRoute[]>([]);
  const [riders, setRiders] = useState<Rider[]>([]);
  const [routeFilter, setRouteFilter] = useState("");
  const [riderFilter, setRiderFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<DeliveryRunStatus | "all">(
    "all",
  );
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useEffect(() => {
    listDeliveryRoutes({ limit: 200 })
      .then(setRoutes)
      .catch(() => setRoutes([]));
    listRiders({ limit: 200 })
      .then(setRiders)
      .catch(() => setRiders([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    listDeliveryRuns({
      route_id: routeFilter || undefined,
      rider_id: riderFilter || undefined,
      status: statusFilter === "all" ? undefined : statusFilter,
      run_date_from: dateFrom || undefined,
      run_date_to: dateTo || undefined,
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
  }, [routeFilter, riderFilter, statusFilter, dateFrom, dateTo]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Runs</h1>
        </div>
        <Link
          href="/delivery/runs/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Run
        </Link>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Route
          </label>
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Rider
          </label>
          <select
            value={riderFilter}
            onChange={(e) => setRiderFilter(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All</option>
            {riders.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as DeliveryRunStatus | "all")
            }
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="all">All</option>
            <option value="planned">Planned</option>
            <option value="in_transit">In transit</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            From
          </label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            To
          </label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading runs…</p>
        )}
        {state.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load runs</p>
            <p className="mt-1 text-sm opacity-80">{state.message}</p>
          </div>
        )}
        {state.status === "ok" && state.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No runs match. Create one.</p>
          </div>
        )}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Route</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Rider</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Stops</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {state.items.map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-3 font-mono text-xs">
                      <Link
                        href={`/delivery/runs/${r.id}`}
                        className="hover:underline"
                      >
                        {r.run_date}
                      </Link>
                    </td>
                    <td className="px-4 py-3 ">
                      {r.route_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.rider_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                      {r.completed_stops}/{r.total_stops}
                      {r.missed_stops > 0 && (
                        <span className="ml-1 text-rose-700">
                          ({r.missed_stops} miss)
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[r.status]}`}
                      >
                        {r.status.replace("_", " ")}
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
