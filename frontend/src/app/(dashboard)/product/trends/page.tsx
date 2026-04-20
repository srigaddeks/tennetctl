"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  EmptyState, ErrorState, Field, Input, Select, Skeleton,
  Table, TBody, TD, TH, THead, TR,
} from "@/components/ui";
import { useEventNames, useTrend } from "@/features/product-ops/hooks/use-trends";

type Bucket = "hour" | "day" | "week" | "month";

export default function TrendsPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>();
  const [eventName, setEventName] = useState<string>("");
  const [days, setDays] = useState(30);
  const [bucket, setBucket] = useState<Bucket>("day");
  const [groupBy, setGroupBy] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const ws = new URLSearchParams(window.location.search).get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const facets = useEventNames(workspaceId, days);
  const trend = useTrend({ workspace_id: workspaceId, event_name: eventName || undefined, days, bucket, group_by: groupBy || undefined });

  // Pivot points → time-series with one column per group
  const pivot = useMemo(() => {
    if (!trend.data) return null;
    const buckets = new Set<string>();
    const groups = new Set<string>();
    for (const p of trend.data.points) {
      buckets.add(p.bucket); groups.add(p.group ?? "(all)");
    }
    const bucketList = Array.from(buckets).sort();
    const groupList = Array.from(groups).sort();
    const matrix: Record<string, Record<string, number>> = {};
    for (const b of bucketList) matrix[b] = {};
    let max = 0;
    for (const p of trend.data.points) {
      const b = p.bucket;
      const g = p.group ?? "(all)";
      const safeBucket = matrix[b];
      if (!safeBucket) continue;
      safeBucket[g] = p.count;
      if (p.count > max) max = p.count;
    }
    return { bucketList, groupList, matrix, max };
  }, [trend.data]);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Trends"
        description="Time-series count of any event over a window. Group by any property in metadata to slice by acquisition channel, plan, etc."
      />

      {!workspaceId && <EmptyState title="No workspace selected" description="Append ?workspace_id=… to view trends." />}

      {workspaceId && (
        <section className="grid grid-cols-4 gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <Field label="Event name" htmlFor="trend-event">
            <Select id="trend-event" value={eventName} onChange={e => setEventName(e.target.value)} data-testid="trend-event-select">
              <option value="">— select event —</option>
              {facets.data?.event_names.map(f => (
                <option key={f.event_name} value={f.event_name}>{f.event_name} ({f.count})</option>
              ))}
            </Select>
          </Field>
          <Field label="Window (days)" htmlFor="trend-days">
            <Input id="trend-days" type="number" min={1} max={365} value={String(days)} onChange={e => setDays(Math.max(1, Number(e.target.value) || 30))} />
          </Field>
          <Field label="Bucket" htmlFor="trend-bucket">
            <Select id="trend-bucket" value={bucket} onChange={e => setBucket(e.target.value as Bucket)}>
              <option value="hour">Hour</option>
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
            </Select>
          </Field>
          <Field label="Group by (metadata key, optional)" htmlFor="trend-group">
            <Input id="trend-group" value={groupBy} onChange={e => setGroupBy(e.target.value)} placeholder="utm_source" />
          </Field>
        </section>
      )}

      {workspaceId && eventName && trend.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && eventName && trend.isError && (
        <ErrorState
          message={trend.error instanceof Error ? trend.error.message : "Failed"}
          retry={() => { void trend.refetch(); }}
        />
      )}

      {workspaceId && eventName && pivot && pivot.bucketList.length === 0 && (
        <EmptyState title="No data" description="No events match the current filter window." />
      )}

      {workspaceId && eventName && pivot && pivot.bucketList.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Bucket</TH>
                {pivot.groupList.map(g => <TH key={g}>{g}</TH>)}
              </TR>
            </THead>
            <TBody>
              {pivot.bucketList.map(b => (
                <TR key={b}>
                  <TD className="text-xs">{b.replace("T00:00:00", "")}</TD>
                  {pivot.groupList.map(g => {
                    const v = pivot.matrix[b]?.[g] ?? 0;
                    const pct = pivot.max > 0 ? (v / pivot.max) * 100 : 0;
                    return (
                      <TD key={g}>
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-32 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div className="h-full rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="text-xs tabular-nums">{v.toLocaleString()}</span>
                        </div>
                      </TD>
                    );
                  })}
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}
