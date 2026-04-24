"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getDashboardToday } from "@/lib/api";
import type { DashboardToday } from "@/types/api";

type LoadState =
  | { status: "loading" }
  | { status: "ok"; data: DashboardToday; fetchedAt: Date }
  | { status: "error"; message: string };

const REFRESH_MS = 30_000;

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

export default function TodaysDashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      getDashboardToday()
        .then((data) => {
          if (!cancelled) {
            setState({ status: "ok", data, fetchedAt: new Date() });
          }
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          const message = err instanceof Error ? err.message : "Unknown error";
          setState({ status: "error", message });
        });
    };
    load();
    const t = window.setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, []);

  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Today&apos;s Dashboard
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Auto-refreshes every 30 seconds.
        </p>
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading KPIs…</p>
      )}

      {state.status === "error" && (
        <div className="rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          <p className="font-semibold">Failed to load dashboard</p>
          <p className="mt-1 text-red-700">{state.message}</p>
        </div>
      )}

      {state.status === "ok" && (
        <>
          <div className="mb-4 text-sm text-sm" style={{ color: "var(--text-muted)" }}>
            As of <span className="font-mono">{state.data.date}</span> · last
            refresh{" "}
            <span className="font-mono">
              {state.fetchedAt.toLocaleTimeString()}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <Kpi label="Active Batches" value={state.data.active_batches} />
            <Kpi
              label="Completed Batches"
              value={state.data.completed_batches}
            />
            <Kpi label="In-Transit Runs" value={state.data.in_transit_runs} />
            <Kpi label="Completed Runs" value={state.data.completed_runs} />
            <Kpi
              label="Scheduled Deliveries"
              value={state.data.scheduled_deliveries}
            />
            <Kpi
              label="Completed Deliveries"
              value={state.data.completed_deliveries}
            />
            <Kpi
              label="Active Subscriptions"
              value={state.data.active_subscriptions}
            />
          </div>
        </>
      )}
    </div>
  );
}
