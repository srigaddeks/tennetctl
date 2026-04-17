"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Input,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useLogsQuery,
  useLogsQueryMore,
} from "@/features/monitoring/hooks/use-logs-query";
import { cn } from "@/lib/cn";
import type { Filter, LogRow, LogsQuery, Timerange } from "@/types/api";

import {
  DslFilterBuilder,
  rowsToFilter,
} from "./dsl-filter-builder";
import { TimerangePicker } from "./timerange-picker";

type Row = { field: string; op: "eq" | "ne" | "contains" | "in"; value: string };
type SeverityLabel = "debug" | "info" | "warn" | "error" | "fatal";

const SEVERITIES: { label: SeverityLabel; min: number }[] = [
  { label: "debug", min: 5 },
  { label: "info", min: 9 },
  { label: "warn", min: 13 },
  { label: "error", min: 17 },
  { label: "fatal", min: 21 },
];

function severityTone(
  sev: number,
): "zinc" | "blue" | "amber" | "red" {
  if (sev >= 17) return "red";
  if (sev >= 13) return "amber";
  if (sev >= 9) return "blue";
  return "zinc";
}

function severityLabel(row: LogRow): string {
  if (row.severity_code) return row.severity_code;
  const s = row.severity_id;
  if (s >= 21) return "fatal";
  if (s >= 17) return "error";
  if (s >= 13) return "warn";
  if (s >= 9) return "info";
  return "debug";
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return `${s.slice(0, n)}…`;
}

export function LogExplorer() {
  const [timerange, setTimerange] = useState<Timerange>({ last: "1h" });
  const [sevMinSet, setSevMinSet] = useState<Set<SeverityLabel>>(new Set());
  const [body, setBody] = useState("");
  const [debouncedBody, setDebouncedBody] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [pagination, setPagination] = useState<{
    key: string;
    extra: LogRow[];
    nextCursor: string | null;
  }>({ key: "", extra: [], nextCursor: null });

  useEffect(() => {
    const t = setTimeout(() => setDebouncedBody(body), 300);
    return () => clearTimeout(t);
  }, [body]);

  const filter: Filter | undefined = useMemo(() => rowsToFilter(rows), [rows]);
  const severityMin = useMemo(() => {
    let min: number | undefined;
    for (const s of sevMinSet) {
      const row = SEVERITIES.find((x) => x.label === s);
      if (row && (min === undefined || row.min < min)) min = row.min;
    }
    return min;
  }, [sevMinSet]);

  const dsl: LogsQuery = useMemo(
    () => ({
      target: "logs",
      timerange,
      filter,
      body_contains: debouncedBody || undefined,
      severity_min: severityMin,
      limit: 100,
    }),
    [timerange, filter, debouncedBody, severityMin],
  );

  const dslKey = useMemo(() => JSON.stringify(dsl), [dsl]);

  const { data, isLoading, isError, error, refetch } = useLogsQuery(dsl);
  const loadMore = useLogsQueryMore();

  // Reset pagination when dsl changes — idiomatic React "derived state from props" pattern.
  if (pagination.key !== dslKey) {
    setPagination({ key: dslKey, extra: [], nextCursor: null });
  }

  const items: LogRow[] = useMemo(() => {
    const base = data?.items ?? [];
    const ids = new Set(base.map((r) => r.id));
    const extraFiltered =
      pagination.key === dslKey
        ? pagination.extra.filter((r) => !ids.has(r.id))
        : [];
    return [...base, ...extraFiltered];
  }, [data, pagination, dslKey]);

  const effectiveCursor =
    (pagination.key === dslKey ? pagination.nextCursor : null) ??
    data?.next_cursor ??
    null;

  const toggleSev = (s: SeverityLabel) => {
    setSevMinSet((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-4" data-testid="monitoring-log-explorer">
      <TimerangePicker value={timerange} onChange={setTimerange} />

      <div className="flex flex-wrap gap-2 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
          Severity
        </span>
        {SEVERITIES.map((s) => (
          <button
            key={s.label}
            type="button"
            onClick={() => toggleSev(s.label)}
            data-testid={`monitoring-log-sev-${s.label}`}
            className={cn(
              "rounded-full border px-2 py-0.5 text-[11px] font-medium",
              sevMinSet.has(s.label)
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      <Input
        placeholder="Search log body…"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        data-testid="monitoring-log-body-search"
      />

      <DslFilterBuilder target="logs" rows={rows} onChange={setRows} />

      {isLoading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      )}
      {isError && (
        <ErrorState
          message={error instanceof Error ? error.message : "Query failed"}
          retry={() => refetch()}
        />
      )}
      {data && items.length === 0 && (
        <EmptyState
          title="No logs"
          description="No logs yet — push one via POST /v1/monitoring/otlp/v1/logs"
        />
      )}
      {items.length > 0 && (
        <>
          <Table>
            <THead>
              <tr>
                <TH>Time</TH>
                <TH>Severity</TH>
                <TH>Service</TH>
                <TH>Body</TH>
                <TH>Trace</TH>
              </tr>
            </THead>
            <TBody>
              {items.map((r) => (
                <Fragment key={r.id}>
                  <TR
                    onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                    data-testid={`monitoring-log-row-${r.id}`}
                  >
                    <TD>
                      <span className="font-mono text-[11px] text-zinc-500">
                        {new Date(r.recorded_at).toLocaleTimeString()}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={severityTone(r.severity_id)}>
                        {severityLabel(r)}
                      </Badge>
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">
                        {r.service_name ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span className="text-xs">{truncate(r.body, 140)}</span>
                    </TD>
                    <TD>
                      {r.trace_id ? (
                        <Link
                          href={`/monitoring/traces/${r.trace_id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="font-mono text-[11px] text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {r.trace_id.slice(0, 8)}…
                        </Link>
                      ) : (
                        <span className="text-xs text-zinc-400">—</span>
                      )}
                    </TD>
                  </TR>
                  {expanded === r.id && (
                    <tr className="bg-zinc-50 dark:bg-zinc-900/60">
                      <td colSpan={5} className="px-4 py-3">
                        <pre className="overflow-x-auto whitespace-pre-wrap break-all rounded-md bg-zinc-900 p-3 text-[11px] text-zinc-100">
                          {JSON.stringify(r.attributes ?? {}, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </TBody>
          </Table>
          {effectiveCursor && (
            <div className="flex justify-center py-2">
              <Button
                variant="secondary"
                size="sm"
                loading={loadMore.isPending}
                data-testid="monitoring-log-load-more"
                onClick={async () => {
                  const res = await loadMore.mutateAsync({
                    ...dsl,
                    cursor: effectiveCursor,
                  });
                  setPagination((prev) => {
                    const base = prev.key === dslKey ? prev.extra : [];
                    const ids = new Set(base.map((r) => r.id));
                    return {
                      key: dslKey,
                      extra: [
                        ...base,
                        ...res.items.filter((r) => !ids.has(r.id)),
                      ],
                      nextCursor: res.next_cursor ?? null,
                    };
                  });
                }}
              >
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
