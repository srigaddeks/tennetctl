"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatCard, Skeleton } from "@/components/ui";
import { useLogsQuery } from "@/features/monitoring/hooks/use-logs-query";
import type { LogsQuery } from "@/types/api";

const PURPLE = "#9d6ef8";

const SUB_MODULES = [
  {
    href: "/monitoring/logs",
    label: "Logs",
    description: "Structured log search with full-text filtering, severity bucketing, and live tail over SSE.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="3" width="16" height="2" rx="1" fill={PURPLE} opacity=".9" />
        <rect x="2" y="7" width="12" height="2" rx="1" fill={PURPLE} opacity=".6" />
        <rect x="2" y="11" width="14" height="2" rx="1" fill={PURPLE} opacity=".9" />
        <rect x="2" y="15" width="9" height="2" rx="1" fill={PURPLE} opacity=".5" />
      </svg>
    ),
    stat: null as string | null,
  },
  {
    href: "/monitoring/metrics",
    label: "Metrics",
    description: "Counter, gauge, and histogram time-series. Query via DSL and pin to dashboards.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <polyline points="2,16 6,10 9,13 13,6 18,8" stroke={PURPLE} strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="18" cy="8" r="1.5" fill={PURPLE} />
      </svg>
    ),
    stat: null,
  },
  {
    href: "/monitoring/traces",
    label: "Traces",
    description: "Distributed traces with span waterfall, latency histograms, and service topology.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="5" width="7" height="2.5" rx="1" fill={PURPLE} opacity=".9" />
        <rect x="5" y="9" width="10" height="2.5" rx="1" fill={PURPLE} opacity=".7" />
        <rect x="8" y="13" width="6" height="2.5" rx="1" fill={PURPLE} opacity=".5" />
      </svg>
    ),
    stat: null,
  },
  {
    href: "/monitoring/dashboards",
    label: "Dashboards",
    description: "Grid-layout panels backed by any DSL query — timeseries, stat, table, log stream.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="2" width="7" height="7" rx="1.5" stroke={PURPLE} strokeWidth="1.5" />
        <rect x="11" y="2" width="7" height="7" rx="1.5" stroke={PURPLE} strokeWidth="1.5" opacity=".7" />
        <rect x="2" y="11" width="7" height="7" rx="1.5" stroke={PURPLE} strokeWidth="1.5" opacity=".7" />
        <rect x="11" y="11" width="7" height="7" rx="1.5" stroke={PURPLE} strokeWidth="1.5" opacity=".5" />
      </svg>
    ),
    stat: null,
  },
  {
    href: "/monitoring/alerts",
    label: "Alerts",
    description: "Threshold rules evaluated on a schedule. Firing, pending, silenced — full lifecycle.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2L3 16h14L10 2z" stroke={PURPLE} strokeWidth="1.5" fill="none" strokeLinejoin="round" />
        <line x1="10" y1="8" x2="10" y2="12" stroke={PURPLE} strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="10" cy="14.5" r="0.8" fill={PURPLE} />
      </svg>
    ),
    stat: null,
  },
  {
    href: "/monitoring/saved-queries",
    label: "Saved Queries",
    description: "Persisted DSL snippets across logs, metrics, and traces. Share org-wide or keep private.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="3" y="2" width="14" height="16" rx="2" stroke={PURPLE} strokeWidth="1.5" fill="none" />
        <line x1="7" y1="7" x2="13" y2="7" stroke={PURPLE} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="7" y1="10" x2="11" y2="10" stroke={PURPLE} strokeWidth="1.5" strokeLinecap="round" opacity=".7" />
        <line x1="7" y1="13" x2="12" y2="13" stroke={PURPLE} strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
      </svg>
    ),
    stat: null,
  },
];

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
  const ratePerSec = total > 0 ? (total / 3600).toFixed(2) : "—";
  const errorPct = total > 0 ? ((errorCount / total) * 100).toFixed(1) : "—";
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
      <div className="flex-1 overflow-y-auto px-6 py-6 animate-fade-in">

        {/* Stat strip */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 mb-8">
          {logs.isLoading ? (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </>
          ) : (
            <>
              <StatCard
                label="Log entries (1h)"
                value={total.toLocaleString()}
                sub="Sampled from recent window"
                accent="blue"
              />
              <StatCard
                label="Log rate"
                value={ratePerSec === "—" ? "—" : `${ratePerSec}/s`}
                sub="Approx logs per second"
                accent="blue"
              />
              <StatCard
                label="Error rate"
                value={errorPct === "—" ? "—" : `${errorPct}%`}
                sub="Severity ≥ error over total"
                accent={parseFloat(errorPct) > 5 ? "red" : "green"}
              />
              <StatCard
                label="Active services"
                value={String(services.size)}
                sub="Distinct service_name"
                accent="green"
              />
            </>
          )}
        </div>

        {/* Section label */}
        <div className="mb-3 flex items-center gap-2">
          <span
            className="h-px flex-1"
            style={{ background: "var(--border)" }}
          />
          <span
            className="label-caps px-2"
            style={{ color: "var(--text-muted)" }}
          >
            Sub-modules
          </span>
          <span
            className="h-px flex-1"
            style={{ background: "var(--border)" }}
          />
        </div>

        {/* Module grid */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 animate-slide-up">
          {SUB_MODULES.map((mod) => (
            <Link
              key={mod.href}
              href={mod.href}
              data-testid={`monitoring-nav-${mod.label.toLowerCase().replace(/\s+/g, "-")}`}
              className="group"
            >
              <div
                className="relative flex flex-col gap-3 rounded border p-5 transition-all duration-200 hover:shadow-[0_0_0_1px_rgba(157,110,248,0.4)]"
                style={{
                  background: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(157,110,248,0.5)";
                  (e.currentTarget as HTMLDivElement).style.background = "var(--bg-elevated)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
                  (e.currentTarget as HTMLDivElement).style.background = "var(--bg-surface)";
                }}
              >
                {/* Top accent bar */}
                <div
                  className="absolute top-0 left-0 right-0 h-px rounded-t"
                  style={{ background: `linear-gradient(90deg, ${PURPLE}80, transparent)` }}
                />

                <div className="flex items-start justify-between gap-3">
                  <div
                    className="flex h-9 w-9 items-center justify-center rounded"
                    style={{
                      background: "rgba(157,110,248,0.08)",
                      border: "1px solid rgba(157,110,248,0.2)",
                    }}
                  >
                    {mod.icon}
                  </div>
                  <svg
                    className="mt-1 opacity-0 transition-opacity group-hover:opacity-100"
                    width="14"
                    height="14"
                    viewBox="0 0 14 14"
                    fill="none"
                    style={{ color: PURPLE }}
                  >
                    <path d="M2 7h10M7 2l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>

                <div>
                  <div
                    className="mb-1 text-[14px] font-semibold tracking-wide"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {mod.label}
                  </div>
                  <p
                    className="text-[12px] leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {mod.description}
                  </p>
                </div>

                {mod.stat && (
                  <div
                    className="font-mono-data text-xs"
                    style={{ color: PURPLE }}
                  >
                    {mod.stat}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
