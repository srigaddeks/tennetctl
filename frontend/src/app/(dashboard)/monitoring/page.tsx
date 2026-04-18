"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui";
import { useLogsQuery } from "@/features/monitoring/hooks/use-logs-query";
import type { LogsQuery } from "@/types/api";

const STATS_NAV = [
  {
    href: "/monitoring/logs",
    label: "Logs",
    description: "Structured log search + live tail.",
    tone: "bg-sky-300 dark:bg-sky-700",
  },
  {
    href: "/monitoring/metrics",
    label: "Metrics",
    description: "Counters, gauges, histograms — charted.",
    tone: "bg-emerald-300 dark:bg-emerald-700",
  },
  {
    href: "/monitoring/traces",
    label: "Traces",
    description: "Distributed traces + span waterfall.",
    tone: "bg-amber-300 dark:bg-amber-700",
  },
  {
    href: "/monitoring/dashboards",
    label: "Dashboards",
    description: "Grid-layout panels of queries.",
    tone: "bg-purple-300 dark:bg-purple-700",
  },
  {
    href: "/monitoring/alerts",
    label: "Alerts",
    description: "Active + recent alerts · rules · silences.",
    tone: "bg-red-300 dark:bg-red-700",
  },
  {
    href: "/monitoring/saved-queries",
    label: "Saved Queries",
    description: "Persisted DSL snippets across logs / metrics / traces.",
    tone: "bg-indigo-300 dark:bg-indigo-700",
  },
];

function StatCard({
  title,
  value,
  hint,
  loading,
}: {
  title: string;
  value: string;
  hint?: string;
  loading?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
        {title}
      </span>
      {loading ? (
        <Skeleton className="h-8 w-24" />
      ) : (
        <span className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          {value}
        </span>
      )}
      {hint && <span className="text-[11px] text-zinc-500">{hint}</span>}
    </div>
  );
}

export default function MonitoringOverview() {
  const baseDsl: LogsQuery = {
    target: "logs",
    timerange: { last: "1h" },
    limit: 500,
  };
  const errorDsl: LogsQuery = {
    target: "logs",
    timerange: { last: "1h" },
    severity_min: 17,
    limit: 500,
  };
  const logs = useLogsQuery(baseDsl);
  const errors = useLogsQuery(errorDsl);

  const total = logs.data?.items.length ?? 0;
  const errorCount = errors.data?.items.length ?? 0;
  const ratePerSec = (total / 3600).toFixed(2);
  const errorPct = total > 0 ? ((errorCount / total) * 100).toFixed(1) : "0.0";
  const services = new Set(
    (logs.data?.items ?? []).map((r) => r.service_name).filter(Boolean),
  );

  return (
    <>
      <PageHeader
        title="Monitoring"
        description="Logs, metrics, traces, and dashboards — unified under one Query DSL."
        testId="heading-monitoring"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Logs (1h)"
            value={total.toLocaleString()}
            hint="Sampled from recent window."
            loading={logs.isLoading}
          />
          <StatCard
            title="Log rate"
            value={`${ratePerSec}/s`}
            hint="Approx logs per second (last 1h)."
            loading={logs.isLoading}
          />
          <StatCard
            title="Error rate"
            value={`${errorPct}%`}
            hint="Severity ≥ error over total (1h)."
            loading={logs.isLoading || errors.isLoading}
          />
          <StatCard
            title="Active services"
            value={String(services.size)}
            hint="Distinct service_name in recent logs."
            loading={logs.isLoading}
          />
        </div>

        <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STATS_NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              data-testid={`monitoring-nav-${n.label.toLowerCase()}`}
              className="group flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-5 transition hover:border-zinc-900 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-100"
            >
              <div className={`h-1 w-10 rounded-full ${n.tone}`} />
              <span className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                {n.label}
              </span>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                {n.description}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
