"use client";

import Link from "next/link";
import { useState } from "react";

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

export default function MonitoringSavedQueriesPage() {
  const [target, setTarget] = useState<"" | QueryTarget>("");
  const list = useSavedQueries(target || undefined);
  const remove = useDeleteSavedQuery();

  const items = list.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Saved Queries"
        description="Persisted Monitoring Query DSL snippets — logs, metrics, traces. Share with the org or keep private."
        testId="heading-monitoring-saved-queries"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="saved-queries-body">
        <div className="mb-4 flex items-center gap-2">
          <label className="text-xs text-zinc-500">Filter</label>
          <Select
            value={target}
            onChange={(e) => setTarget(e.target.value as "" | QueryTarget)}
            className="w-48"
            data-testid="saved-queries-target-filter"
          >
            {TARGET_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
          <span className="ml-auto text-xs text-zinc-500">
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
                <TH>Shared</TH>
                <TH>Updated</TH>
                <TH></TH>
              </tr>
            </THead>
            <TBody>
              {items.map((q) => (
                <TR key={q.id} data-testid={`saved-query-row-${q.id}`}>
                  <TD>
                    <Link
                      href={`${TARGET_HREF[q.target]}?saved=${encodeURIComponent(q.id)}`}
                      className="text-sm font-medium text-zinc-900 hover:underline dark:text-zinc-100"
                    >
                      {q.name}
                    </Link>
                    {!q.is_active && (
                      <Badge tone="zinc" className="ml-2">
                        inactive
                      </Badge>
                    )}
                  </TD>
                  <TD>
                    <Badge tone={TARGET_TONE[q.target]}>{q.target}</Badge>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
                      {q.description ?? "—"}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone={q.shared ? "emerald" : "zinc"}>
                      {q.shared ? "org" : "private"}
                    </Badge>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
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
                      className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}

        <p className="mt-6 text-xs text-zinc-500">
          Create queries by hitting Save from the{" "}
          <Link href="/monitoring/logs" className="underline">Logs</Link>,{" "}
          <Link href="/monitoring/metrics" className="underline">Metrics</Link>,
          or{" "}
          <Link href="/monitoring/traces" className="underline">Traces</Link>{" "}
          explorer.
        </p>
      </div>
    </>
  );
}
