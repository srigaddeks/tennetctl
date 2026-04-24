"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  listSubscriptionFrequencies,
  listSubscriptionPlans,
} from "@/lib/api";
import type {
  SubscriptionFrequency,
  SubscriptionPlan,
  SubscriptionPlanStatus,
} from "@/types/api";

type PlansState =
  | { status: "loading" }
  | { status: "ok"; items: SubscriptionPlan[] }
  | { status: "error"; message: string };

type StatusFilter = SubscriptionPlanStatus | "all";

export default function PlansListPage() {
  const [plans, setPlans] = useState<PlansState>({ status: "loading" });
  const [frequencies, setFrequencies] = useState<SubscriptionFrequency[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [frequencyId, setFrequencyId] = useState<string>("");

  useEffect(() => {
    listSubscriptionFrequencies().then(setFrequencies).catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setPlans({ status: "loading" });
    const freqNum =
      frequencyId === "" ? undefined : Number.parseInt(frequencyId, 10);
    listSubscriptionPlans({
      status: statusFilter === "all" ? undefined : statusFilter,
      frequency_id:
        freqNum !== undefined && Number.isFinite(freqNum) ? freqNum : undefined,
    })
      .then((items) => {
        if (!cancelled) setPlans({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setPlans({
          status: "error",
          message: err instanceof Error ? err.message : "Unknown error",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [statusFilter, frequencyId]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Subscription Plans
          </h1>
        </div>
        <Link
          href="/subscriptions/plans/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Plan
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
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Frequency
          </label>
          <select
            value={frequencyId}
            onChange={(e) => setFrequencyId(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All</option>
            {frequencies.map((f) => (
              <option key={f.id} value={String(f.id)}>
                {f.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {plans.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading plans…</p>
        )}
        {plans.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load plans</p>
            <p className="mt-1 text-sm opacity-80">{plans.message}</p>
          </div>
        )}
        {plans.status === "ok" && plans.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No plans yet.</p>
          </div>
        )}
        {plans.status === "ok" && plans.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Frequency</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Price</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Items</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {plans.items.map((p) => (
                  <tr key={p.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link
                        href={`/subscriptions/plans/${p.id}`}
                        className="hover:underline"
                      >
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{p.frequency_name ?? "—"}</td>
                    <td className="px-4 py-3 font-mono">
                      {p.price_per_delivery !== null
                        ? `${p.currency_code} ${p.price_per_delivery}`
                        : "custom"}
                    </td>
                    <td className="px-4 py-3 text-center font-mono">
                      {p.item_count}
                    </td>
                    <td className="px-4 py-3">
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium ">
                        {p.status}
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
