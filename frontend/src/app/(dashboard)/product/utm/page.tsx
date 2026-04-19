"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { EmptyState, ErrorState, Select, Skeleton, Table, TBody, TD, TH, THead, TR } from "@/components/ui";
import { useUtmAggregate } from "@/features/product-ops/hooks/use-product-events";

const WINDOW_OPTIONS: Array<{ value: number; label: string }> = [
  { value: 1, label: "Last 1 day" },
  { value: 7, label: "Last 7 days" },
  { value: 30, label: "Last 30 days" },
  { value: 90, label: "Last 90 days" },
];

export default function UtmDashboardPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [days, setDays] = useState<number>(30);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const query = useUtmAggregate(workspaceId, days);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="UTM Campaigns"
        description="Top acquisition campaigns by visitor + conversion count. Conversion = any event with metadata.is_conversion = true."
        actions={
          <Select
            value={String(days)}
            onChange={(e) => setDays(Number(e.target.value))}
            data-testid="utm-window-select"
          >
            {WINDOW_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
        }
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view UTM aggregates."
        />
      )}

      {workspaceId && query.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && query.isError && (
        <ErrorState
          message={query.error instanceof Error ? query.error.message : "Failed to load UTM aggregate"}
          retry={() => {
            void query.refetch();
          }}
        />
      )}

      {workspaceId && query.data && query.data.rows.length === 0 && (
        <EmptyState
          title="No campaigns yet"
          description="Send events with utm_source / utm_campaign in their page_url to populate this view."
        />
      )}

      {workspaceId && query.data && query.data.rows.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>UTM Source</TH>
                <TH>Campaign</TH>
                <TH>Visitors</TH>
                <TH>Conversions</TH>
                <TH>CVR</TH>
              </TR>
            </THead>
            <TBody>
              {query.data.rows.map((r) => {
                const cvr = r.visitors > 0 ? (r.conversions / r.visitors) * 100 : 0;
                return (
                  <TR key={`${r.utm_source}|${r.utm_campaign}`}>
                    <TD>{r.utm_source}</TD>
                    <TD>{r.utm_campaign}</TD>
                    <TD>{r.visitors.toLocaleString()}</TD>
                    <TD>{r.conversions.toLocaleString()}</TD>
                    <TD>{cvr.toFixed(2)}%</TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}
