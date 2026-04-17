"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";

import { Badge, Button, EmptyState, TBody, TD, TH, THead, TR, Table } from "@/components/ui";
import { useLiveTail } from "@/features/monitoring/hooks/use-live-tail";
import { cn } from "@/lib/cn";
import type { Filter, LogRow } from "@/types/api";

import { DslFilterBuilder, rowsToFilter } from "./dsl-filter-builder";

type Row = { field: string; op: "eq" | "ne" | "contains" | "in"; value: string };

function severityTone(sev: number) {
  if (sev >= 17) return "red" as const;
  if (sev >= 13) return "amber" as const;
  if (sev >= 9) return "blue" as const;
  return "zinc" as const;
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

export function LogLiveTail() {
  const [rows, setRows] = useState<Row[]>([]);
  const filter: Filter | null = useMemo(
    () => rowsToFilter(rows) ?? null,
    [rows],
  );
  const { logs, paused, connected, pause, resume, clear } = useLiveTail(filter);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!paused) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [logs, paused]);

  return (
    <div className="flex flex-col gap-4" data-testid="monitoring-log-live-tail">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "relative flex h-2 w-2 rounded-full",
              connected ? "bg-green-500" : "bg-zinc-400",
            )}
          >
            {connected && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            )}
          </span>
          <span className="text-xs text-zinc-600 dark:text-zinc-400">
            {connected ? "Connected" : "Disconnected"}
            {paused && " · Paused"}
          </span>
          <span className="text-xs text-zinc-400">· {logs.length} events</span>
        </div>
        <div className="flex gap-2">
          {paused ? (
            <Button
              size="sm"
              variant="primary"
              onClick={resume}
              data-testid="monitoring-livetail-resume"
            >
              Resume
            </Button>
          ) : (
            <Button
              size="sm"
              variant="secondary"
              onClick={pause}
              data-testid="monitoring-livetail-pause"
            >
              Pause
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={clear}
            data-testid="monitoring-livetail-clear"
          >
            Clear
          </Button>
        </div>
      </div>

      <DslFilterBuilder target="logs" rows={rows} onChange={setRows} />

      {logs.length === 0 ? (
        <EmptyState
          title="Waiting for logs"
          description="Live tail is active. New logs will appear here as they are ingested."
        />
      ) : (
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
            {logs.map((r) => (
              <TR key={r.id} data-testid={`monitoring-livetail-row-${r.id}`}>
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
                  <span className="text-xs">{r.body}</span>
                </TD>
                <TD>
                  {r.trace_id ? (
                    <Link
                      href={`/monitoring/traces/${r.trace_id}`}
                      className="font-mono text-[11px] text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {r.trace_id.slice(0, 8)}…
                    </Link>
                  ) : (
                    <span className="text-xs text-zinc-400">—</span>
                  )}
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
