"use client";

import Link from "next/link";
import { useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  EmptyState,
  ErrorState,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useDeleteSavedQuery,
  useSavedQueries,
} from "@/features/monitoring/hooks/use-saved-queries";
import type { QueryTarget } from "@/types/api";

const TARGET_OPTIONS: { value: "" | QueryTarget; label: string }[] = [
  { value: "", label: "All targets" },
  { value: "logs", label: "Logs" },
  { value: "metrics", label: "Metrics" },
  { value: "traces", label: "Traces" },
];

const TARGET_TONE: Record<QueryTarget, "blue" | "emerald" | "purple"> = {
  logs: "blue",
  metrics: "emerald",
  traces: "purple",
};

const TARGET_HREF: Record<QueryTarget, string> = {
  logs: "/monitoring/logs",
  metrics: "/monitoring/metrics",
  traces: "/monitoring/traces",
};

const TARGET_ICON: Record<QueryTarget, string> = {
  logs: "≡",
  metrics: "∿",
  traces: "⋯",
};

export default function MonitoringSavedQueriesPage() {
  const [target, setTarget] = useState<"" | QueryTarget>("");
  const [appFilter, setAppFilter] = useState<string | null>(null);
  const list = useSavedQueries(target || undefined);
  const remove = useDeleteSavedQuery();

  const items = list.data?.items ?? [];
  const logCount = items.filter((q) => q.target === "logs").length;
  const metricCount = items.filter((q) => q.target === "metrics").length;
  const traceCount = items.filter((q) => q.target === "traces").length;

  return (
    <>
      <PageHeader
        title="Saved Queries"
        description="Persisted Monitoring Query DSL snippets — logs, metrics, traces. Share with the org or keep private."
        testId="heading-monitoring-saved-queries"
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in" data-testid="saved-queries-body">
        <div className="flex flex-col gap-5">

          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Queries for application"
          />

          {/* Stats strip */}
          {!list.isLoading && items.length > 0 && (
            <div
              className="flex items-center gap-5 rounded border px-4 py-3"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div className="flex items-center gap-2">
                <span className="label-caps" style={{ color: "var(--text-muted)" }}>All</span>
                <span className="font-mono-data text-[20px] font-semibold" style={{ color: "var(--text-primary)" }}>
                  {items.length}
                </span>
              </div>
              <span className="h-4 w-px" style={{ background: "var(--border)" }} />
              <div className="flex items-center gap-2">
                <Badge tone="blue">logs</Badge>
                <span className="font-mono-data text-[14px] font-semibold" style={{ color: "var(--accent-hover)" }}>{logCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="emerald">metrics</Badge>
                <span className="font-mono-data text-[14px] font-semibold" style={{ color: "var(--success)" }}>{metricCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="purple">traces</Badge>
                <span className="font-mono-data text-[14px] font-semibold" style={{ color: "#9d6ef8" }}>{traceCount}</span>
              </div>
            </div>
          )}

          {/* Filter bar */}
          <div className="flex items-center gap-3">
            <span
              className="label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              Filter by target
            </span>
            <Select
              value={target}
              onChange={(e) => setTarget(e.target.value as "" | QueryTarget)}
              className="w-44"
              data-testid="saved-queries-target-filter"
            >
              {TARGET_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
            <span
              className="ml-auto font-mono-data text-[12px]"
              style={{ color: "var(--text-muted)" }}
            >
              {items.length} {items.length === 1 ? "query" : "queries"}
            </span>
          </div>

          {list.isLoading && <Skeleton className="h-40 w-full" />}

          {list.isError && (
            <ErrorState
              message={
                list.error instanceof Error ? list.error.message : "Load failed"
              }
              retry={() => list.refetch()}
            />
          )}

          {!list.isLoading && items.length === 0 && (
            <EmptyState
              title="No saved queries yet"
              description="Save a query from the Logs, Metrics, or Traces explorer to revisit it later."
            />
          )}

          {items.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Name</TH>
                  <TH>Target</TH>
                  <TH>Description</TH>
                  <TH>Visibility</TH>
                  <TH>Last updated</TH>
                  <TH></TH>
                </tr>
              </THead>
              <TBody>
                {items.map((q) => (
                  <TR key={q.id} data-testid={`saved-query-row-${q.id}`}>
                    <TD>
                      <div className="flex items-center gap-2">
                        <span
                          className="font-mono-data text-[14px]"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {TARGET_ICON[q.target]}
                        </span>
                        <div className="flex flex-col gap-0.5">
                          <Link
                            href={`${TARGET_HREF[q.target]}?saved=${encodeURIComponent(q.id)}`}
                            className="text-[13px] font-medium transition-colors hover:underline"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {q.name}
                          </Link>
                          {!q.is_active && (
                            <Badge tone="default" className="self-start">inactive</Badge>
                          )}
                        </div>
                      </div>
                    </TD>
                    <TD>
                      <Badge tone={TARGET_TONE[q.target]}>{q.target}</Badge>
                    </TD>
                    <TD>
                      <span
                        className="text-[12px]"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {q.description ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={q.shared ? "emerald" : "default"}>
                        {q.shared ? "org-wide" : "private"}
                      </Badge>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-[11px]"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {q.updated_at.slice(0, 10)}
                      </span>
                    </TD>
                    <TD>
                      <button
                        type="button"
                        data-testid={`saved-query-delete-${q.id}`}
                        disabled={remove.isPending}
                        onClick={() => {
                          if (confirm(`Delete saved query "${q.name}"?`)) {
                            remove.mutate(q.id);
                          }
                        }}
                        className="text-[12px] transition-colors disabled:opacity-40"
                        style={{ color: "var(--danger)" }}
                        onMouseEnter={(e) => {
                          (e.currentTarget as HTMLButtonElement).style.opacity = "0.7";
                        }}
                        onMouseLeave={(e) => {
                          (e.currentTarget as HTMLButtonElement).style.opacity = "1";
                        }}
                      >
                        Delete
                      </button>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}

          <p
            className="text-[12px]"
            style={{ color: "var(--text-muted)" }}
          >
            Create queries by hitting Save from the{" "}
            <Link
              href="/monitoring/logs"
              className="hover:underline"
              style={{ color: "var(--accent-hover)" }}
            >
              Logs
            </Link>
            ,{" "}
            <Link
              href="/monitoring/metrics"
              className="hover:underline"
              style={{ color: "var(--success)" }}
            >
              Metrics
            </Link>
            , or{" "}
            <Link
              href="/monitoring/traces"
              className="hover:underline"
              style={{ color: "#9d6ef8" }}
            >
              Traces
            </Link>{" "}
            explorer.
          </p>
        </div>
      </div>
    </>
  );
}
