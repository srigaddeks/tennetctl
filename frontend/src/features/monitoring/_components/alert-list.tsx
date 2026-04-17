"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";

import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { cn } from "@/lib/cn";
import {
  useAlertEvents,
} from "@/features/monitoring/hooks/use-alerts";
import type { AlertEvent, AlertSeverity, AlertState } from "@/types/api";

import { SilenceDialog } from "./silence-dialog";

const SEVERITIES: AlertSeverity[] = ["info", "warn", "error", "critical"];
const STATES: AlertState[] = ["firing", "resolved"];

function severityTone(
  sev: AlertSeverity | null,
): "blue" | "amber" | "red" | "zinc" {
  if (sev === "critical") return "red";
  if (sev === "error") return "red";
  if (sev === "warn") return "amber";
  if (sev === "info") return "blue";
  return "zinc";
}

function SeverityPill({ severity }: { severity: AlertSeverity | null }) {
  if (!severity) return <Badge tone="zinc">n/a</Badge>;
  return (
    <span
      data-testid={`alert-severity-${severity}`}
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        severity === "info" &&
          "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
        severity === "warn" &&
          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
        severity === "error" &&
          "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
        severity === "critical" &&
          "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
      )}
    >
      {severity}
    </span>
  );
}

function StateBadge({ state, silenced }: { state: string; silenced: boolean }) {
  if (silenced) {
    return (
      <Badge tone="purple" className="uppercase">
        <span data-testid="alert-silenced-badge">silenced</span>
      </Badge>
    );
  }
  if (state === "firing") {
    return (
      <Badge tone="red" className="uppercase">
        firing
      </Badge>
    );
  }
  return (
    <Badge tone="emerald" className="uppercase">
      resolved
    </Badge>
  );
}

export function AlertList() {
  const router = useRouter();
  const [stateFilter, setStateFilter] = useState<AlertState | "all">("all");
  const [sevFilter, setSevFilter] = useState<AlertSeverity | "all">("all");
  const [silenceFor, setSilenceFor] = useState<AlertEvent | null>(null);

  const { data, isLoading, isError, error, refetch } = useAlertEvents(
    stateFilter === "all" ? undefined : stateFilter,
  );

  const rows = useMemo(() => {
    const items = data?.items ?? [];
    if (sevFilter === "all") return items;
    return items.filter((r) => r.severity === sevFilter);
  }, [data, sevFilter]);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
          State
        </span>
        <button
          type="button"
          data-testid="alert-filter-state-all"
          onClick={() => setStateFilter("all")}
          className={cn(
            "rounded-md border px-2.5 py-1 text-xs font-medium",
            stateFilter === "all"
              ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
              : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
          )}
        >
          All
        </button>
        {STATES.map((s) => (
          <button
            key={s}
            type="button"
            data-testid={`alert-filter-state-${s}`}
            onClick={() => setStateFilter(s)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-xs font-medium",
              stateFilter === s
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
            )}
          >
            {s}
          </button>
        ))}
        <span className="ml-4 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
          Severity
        </span>
        <button
          type="button"
          data-testid="alert-filter-sev-all"
          onClick={() => setSevFilter("all")}
          className={cn(
            "rounded-md border px-2.5 py-1 text-xs font-medium",
            sevFilter === "all"
              ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
              : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
          )}
        >
          All
        </button>
        {SEVERITIES.map((s) => (
          <button
            key={s}
            type="button"
            data-testid={`alert-filter-sev-${s}`}
            onClick={() => setSevFilter(s)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-xs font-medium",
              sevFilter === s
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      )}
      {isError && (
        <ErrorState
          message={error instanceof Error ? error.message : "Load failed"}
          retry={() => refetch()}
        />
      )}
      {data && rows.length === 0 && !isLoading && (
        <EmptyState
          title="No alerts"
          description="No alerts match the current filters. When a rule fires, alerts appear here."
        />
      )}
      {rows.length > 0 && (
        <Table>
          <THead>
            <TR>
              <TH>Rule</TH>
              <TH>Severity</TH>
              <TH>State</TH>
              <TH>Value</TH>
              <TH>Threshold</TH>
              <TH>Started</TH>
              <TH>Notifications</TH>
              <TH className="text-right">Actions</TH>
            </TR>
          </THead>
          <TBody>
            {rows.map((r) => (
              <TR
                key={`${r.id}-${r.started_at}`}
                data-testid="alert-row"
                onClick={() => {
                  const qs = new URLSearchParams({ started_at: r.started_at });
                  router.push(
                    `/monitoring/alerts/${encodeURIComponent(r.id)}?${qs.toString()}`,
                  );
                }}
              >
                <TD>
                  <span
                    className="font-medium"
                    data-testid={`alert-rule-name-${r.rule_id}`}
                  >
                    {r.rule_name ?? r.rule_id}
                  </span>
                </TD>
                <TD>
                  <SeverityPill severity={r.severity} />
                </TD>
                <TD>
                  <StateBadge state={r.state} silenced={r.silenced} />
                </TD>
                <TD>{r.value ?? "—"}</TD>
                <TD>{r.threshold ?? "—"}</TD>
                <TD className="text-xs text-zinc-500">
                  {new Date(r.started_at).toLocaleString()}
                </TD>
                <TD>{r.notification_count}</TD>
                <TD className="text-right">
                  <Button
                    size="sm"
                    variant="secondary"
                    data-testid="alert-row-silence"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSilenceFor(r);
                    }}
                  >
                    Silence
                  </Button>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      {silenceFor && (
        <SilenceDialog
          open={silenceFor !== null}
          alertEvent={silenceFor}
          onClose={() => setSilenceFor(null)}
        />
      )}
    </div>
  );
}
