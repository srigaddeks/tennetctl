"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listRiderRoles, listRiders } from "@/lib/api";
import type { Rider, RiderRole, RiderStatus } from "@/types/api";

type State =
  | { status: "loading" }
  | { status: "ok"; items: Rider[] }
  | { status: "error"; message: string };

const STATUS_LABELS: Record<RiderStatus, string> = {
  active: "Active",
  inactive: "Inactive",
  suspended: "Suspended",
};

export default function RidersListPage() {
  const [state, setState] = useState<State>({ status: "loading" });
  const [roles, setRoles] = useState<RiderRole[]>([]);
  const [statusFilter, setStatusFilter] = useState<RiderStatus | "all">("all");
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [q, setQ] = useState("");

  useEffect(() => {
    listRiderRoles().then(setRoles).catch(() => setRoles([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    listRiders({
      status: statusFilter === "all" ? undefined : statusFilter,
      role_id: roleFilter ? Number(roleFilter) : undefined,
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
  }, [statusFilter, roleFilter, q]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Riders</h1>
        </div>
        <Link
          href="/delivery/riders/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Rider
        </Link>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as RiderStatus | "all")
            }
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Role
          </label>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Search (name / phone)
          </label>
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. Sri"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading riders…</p>
        )}
        {state.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load riders</p>
            <p className="mt-1 text-sm opacity-80">{state.message}</p>
          </div>
        )}
        {state.status === "ok" && state.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No riders yet. Add one.</p>
          </div>
        )}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Phone</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Role</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Vehicle</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {state.items.map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      {r.name}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                      {r.phone ?? "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.role_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.vehicle_type ?? "—"}
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
