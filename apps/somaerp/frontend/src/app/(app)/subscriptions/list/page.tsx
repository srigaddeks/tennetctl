"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  listSubscriptionPlans,
  listSubscriptions,
} from "@/lib/api";
import type {
  Subscription,
  SubscriptionPlan,
  SubscriptionStatus,
} from "@/types/api";

type SubsState =
  | { status: "loading" }
  | { status: "ok"; items: Subscription[] }
  | { status: "error"; message: string };

type StatusFilter = SubscriptionStatus | "all";

export default function SubscriptionsListPage() {
  const [subs, setSubs] = useState<SubsState>({ status: "loading" });
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [planId, setPlanId] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    listSubscriptionPlans().then(setPlans).catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSubs({ status: "loading" });
    listSubscriptions({
      plan_id: planId || undefined,
      status: statusFilter === "all" ? undefined : statusFilter,
    })
      .then((items) => {
        if (!cancelled) setSubs({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setSubs({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [planId, statusFilter]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Customer Subscriptions
          </h1>
        </div>
        <Link
          href="/subscriptions/list/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Subscription
        </Link>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-2" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
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
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="cancelled">Cancelled</option>
            <option value="ended">Ended</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Plan
          </label>
          <select
            value={planId}
            onChange={(e) => setPlanId(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All plans</option>
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {subs.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading subscriptions…</p>
        )}
        {subs.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">
              Failed to load subscriptions
            </p>
            <p className="mt-1 text-sm opacity-80">{subs.message}</p>
          </div>
        )}
        {subs.status === "ok" && subs.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No subscriptions match the current filters.</p>
          </div>
        )}
        {subs.status === "ok" && subs.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Plan</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Frequency</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Start</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Zone</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {subs.items.map((s) => (
                  <tr key={s.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link
                        href={`/subscriptions/list/${s.id}`}
                        className="hover:underline"
                      >
                        {s.customer_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{s.plan_name}</td>
                    <td className="px-4 py-3">{s.frequency_name ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {s.start_date}
                    </td>
                    <td className="px-4 py-3">{s.service_zone_name ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium ">
                        {s.status}
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
