"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listCustomers, listLocations } from "@/lib/api";
import type { Customer, CustomerStatus, Location } from "@/types/api";

type CustomersState =
  | { status: "loading" }
  | { status: "ok"; items: Customer[] }
  | { status: "error"; message: string };

type LocationsState =
  | { status: "loading" }
  | { status: "ok"; items: Location[] }
  | { status: "error"; message: string };

type StatusFilter = CustomerStatus | "all";

const STATUS_LABELS: Record<CustomerStatus, string> = {
  prospect: "Prospect",
  active: "Active",
  paused: "Paused",
  churned: "Churned",
  blocked: "Blocked",
};

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomersState>({
    status: "loading",
  });
  const [locations, setLocations] = useState<LocationsState>({
    status: "loading",
  });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [locationId, setLocationId] = useState<string>("");
  const [q, setQ] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listLocations()
      .then((items) => {
        if (!cancelled) setLocations({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLocations({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setCustomers({ status: "loading" });
    listCustomers({
      status: statusFilter === "all" ? undefined : statusFilter,
      location_id: locationId || undefined,
      q: q || undefined,
    })
      .then((items) => {
        if (!cancelled) setCustomers({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setCustomers({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [statusFilter, locationId, q]);

  const kpis = useMemo(() => {
    if (customers.status !== "ok") {
      return { active: 0, paused: 0, churned: 0, total: 0 };
    }
    const items = customers.items;
    return {
      active: items.filter((c) => c.status === "active").length,
      paused: items.filter((c) => c.status === "paused").length,
      churned: items.filter((c) => c.status === "churned").length,
      total: items.length,
    };
  }, [customers]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Customers</h1>
        </div>

        <Link
          href="/customers/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Customer
        </Link>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard label="Total" value={kpis.total} />
        <KpiCard label="Active" value={kpis.active} tone="green" />
        <KpiCard label="Paused" value={kpis.paused} tone="yellow" />
        <KpiCard label="Churned" value={kpis.churned} tone="red" />
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="all">All</option>
            <option value="prospect">Prospect</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="churned">Churned</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Location
          </label>
          <select
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All locations</option>
            {locations.status === "ok" &&
              locations.items.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Search (name / email / phone)
          </label>
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. raj or 98765…"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {customers.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading customers…</p>
        )}

        {customers.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">
              Failed to load customers
            </p>
            <p className="mt-1 text-sm opacity-80">{customers.message}</p>
          </div>
        )}

        {customers.status === "ok" && customers.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No customers match the current filters.</p>
          </div>
        )}

        {customers.status === "ok" && customers.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Location</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Subs</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {customers.items.map((c) => (
                  <tr key={c.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link
                        href={`/customers/${c.id}`}
                        className="hover:underline"
                      >
                        {c.name}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                      <div>{c.email ?? "—"}</div>
                      <div>{c.phone ?? "—"}</div>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {c.location_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-center font-mono ">
                      {c.active_subscription_count}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={c.status} />
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

function KpiCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "green" | "yellow" | "red";
}) {
  const toneStyle =
    tone === "green"
      ? "text-green-700"
      : tone === "yellow"
      ? "text-yellow-700"
      : tone === "red"
      ? "text-red-700"
      : "";
  return (
    <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
      <div className="text-xs font-semibold uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className={`mt-1 text-3xl font-bold ${toneStyle}`}>{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: CustomerStatus }) {
  const styles: Record<CustomerStatus, string> = {
    prospect: "bg-blue-100 text-blue-800 border-blue-200",
    active: "bg-green-100 text-green-800 border-green-200",
    paused: "bg-yellow-100 text-yellow-800 border-yellow-200",
    churned: "bg-red-100 text-red-800 border-red-200",
    blocked: "bg-slate-900 text-white border-slate-900",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
