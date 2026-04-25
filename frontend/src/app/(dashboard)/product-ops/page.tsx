"use client";

import { useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useProductCounts,
  useProductEventKeys,
  useProductEvents,
  useInvalidateProductOps,
} from "@/features/product-ops/hooks/use-product-events";
import type { ProductEventFilter, ProductEventRow } from "@/types/api";

const REFRESH_INTERVAL_MS = 2000;

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

function PropertiesCell({ row }: { row: ProductEventRow }) {
  const keys = Object.keys(row.properties);
  if (keys.length === 0) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const text = JSON.stringify(row.properties);
  const display = text.length > 80 ? `${text.slice(0, 80)}…` : text;
  return (
    <span
      className="font-mono-data text-[11px]"
      style={{ color: "var(--text-secondary)" }}
      title={text}
    >
      {display}
    </span>
  );
}

export default function ProductOpsExplorerPage() {
  const [filter, setFilter] = useState<ProductEventFilter>({});
  const [live, setLive] = useState(true);
  const [draftDistinct, setDraftDistinct] = useState("");

  const events = useProductEvents(filter, {
    limit: 100,
    refetchIntervalMs: live ? REFRESH_INTERVAL_MS : 0,
  });
  const counts = useProductCounts({
    refetchIntervalMs: live ? REFRESH_INTERVAL_MS * 2 : 0,
  });
  const keys = useProductEventKeys();
  const invalidate = useInvalidateProductOps();

  const items = useMemo(() => events.data?.items ?? [], [events.data]);

  const onApplyDistinct = () => {
    setFilter((f) => ({ ...f, distinct_id: draftDistinct.trim() || null }));
  };

  return (
    <div className="flex flex-col">
      <PageHeader
        title="Product Ops · Explorer"
        description="Live event stream + daily counts. Drop /v1/track from any frontend or backend; distinct_id groups everything."
        actions={
          <div className="flex items-center gap-2">
            <Badge tone={live ? "success" : "default"}>
              {live ? "● live" : "paused"}
            </Badge>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setLive((l) => !l)}
            >
              {live ? "Pause" : "Resume"}
            </Button>
            <Button size="sm" variant="secondary" onClick={() => invalidate()}>
              Refresh
            </Button>
          </div>
        }
      />

      <div className="px-6 py-4 flex flex-col gap-5">
        {/* Counts panel */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {counts.isLoading ? (
            <>
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </>
          ) : counts.isError ? (
            <div className="col-span-4">
              <ErrorState
                message={String(counts.error)}
                retry={() => {
                  void counts.refetch();
                }}
              />
            </div>
          ) : counts.data ? (
            <>
              <StatCard
                label="Events today"
                value={counts.data.events_today.toLocaleString()}
                accent="blue"
              />
              <StatCard
                label="Events 24h"
                value={counts.data.events_24h.toLocaleString()}
                accent="blue"
              />
              <StatCard
                label="DAU (today)"
                value={counts.data.dau.toLocaleString()}
                sub="distinct_ids seen today"
                accent="green"
              />
              <StatCard
                label="Distinct IDs 24h"
                value={counts.data.distinct_ids_24h.toLocaleString()}
                accent="green"
              />
            </>
          ) : null}
        </div>

        {/* Top events */}
        <div
          className="rounded border"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <div
            className="px-4 py-3 border-b flex items-center justify-between"
            style={{ borderColor: "var(--border)" }}
          >
            <span className="label-caps">Top events · 24h</span>
            <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
              {counts.data?.top_events_24h.length ?? 0} keys
            </span>
          </div>
          <div className="px-4 py-3">
            {counts.data && counts.data.top_events_24h.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {counts.data.top_events_24h.map((e) => (
                  <button
                    key={e.event_name}
                    type="button"
                    onClick={() =>
                      setFilter((f) => ({
                        ...f,
                        event_name:
                          f.event_name === e.event_name ? null : e.event_name,
                      }))
                    }
                    className="rounded border px-2.5 py-1 text-[11px] font-mono-data"
                    style={{
                      borderColor:
                        filter.event_name === e.event_name
                          ? "var(--accent)"
                          : "var(--border)",
                      background:
                        filter.event_name === e.event_name
                          ? "var(--accent-soft)"
                          : "var(--bg-base)",
                      color: "var(--text-primary)",
                    }}
                  >
                    {e.event_name}
                    <span
                      className="ml-2"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {e.count}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>
                No events yet — POST to /v1/track to see them here.
              </span>
            )}
          </div>
        </div>

        {/* Filters */}
        <div
          className="rounded border px-4 py-3 grid grid-cols-1 sm:grid-cols-3 gap-3"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <Field label="Event">
            <Select
              value={filter.event_name ?? ""}
              onChange={(e) =>
                setFilter((f) => ({
                  ...f,
                  event_name: e.target.value || null,
                }))
              }
            >
              <option value="">All events</option>
              {keys.data?.items.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="distinct_id">
            <div className="flex gap-2">
              <Input
                value={draftDistinct}
                placeholder="anon-… or user uuid"
                onChange={(e) => setDraftDistinct(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") onApplyDistinct();
                }}
              />
              <Button size="sm" variant="secondary" onClick={onApplyDistinct}>
                Apply
              </Button>
              {filter.distinct_id && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setDraftDistinct("");
                    setFilter((f) => ({ ...f, distinct_id: null }));
                  }}
                >
                  Clear
                </Button>
              )}
            </div>
          </Field>
          <Field label="Source">
            <Select
              value={filter.source ?? ""}
              onChange={(e) =>
                setFilter((f) => ({
                  ...f,
                  source: e.target.value || null,
                }))
              }
            >
              <option value="">All sources</option>
              <option value="web">web</option>
              <option value="mobile">mobile</option>
              <option value="server">server</option>
              <option value="backend">backend</option>
              <option value="other">other</option>
            </Select>
          </Field>
        </div>

        {/* Event stream */}
        <div
          className="rounded border"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <div
            className="px-4 py-3 border-b flex items-center justify-between"
            style={{ borderColor: "var(--border)" }}
          >
            <span className="label-caps">Event stream</span>
            <span
              className="text-[11px] font-mono-data"
              style={{ color: "var(--text-muted)" }}
            >
              {items.length} rows · {live ? "auto-refresh 2s" : "paused"}
            </span>
          </div>

          {events.isLoading ? (
            <div className="p-4 flex flex-col gap-2">
              <Skeleton className="h-6" />
              <Skeleton className="h-6" />
              <Skeleton className="h-6" />
            </div>
          ) : events.isError ? (
            <div className="p-4">
              <ErrorState
                message={String(events.error)}
                retry={() => {
                  void events.refetch();
                }}
              />
            </div>
          ) : items.length === 0 ? (
            <EmptyState
              title="No events yet"
              description="POST to /v1/track to start ingesting. Events appear here within 2s."
            />
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Time</TH>
                  <TH>Event</TH>
                  <TH>distinct_id</TH>
                  <TH>Source</TH>
                  <TH>URL</TH>
                  <TH>Properties</TH>
                </TR>
              </THead>
              <TBody>
                {items.map((row) => (
                  <TR key={row.id}>
                    <TD>
                      <span
                        className="font-mono-data text-[11px]"
                        style={{ color: "var(--text-secondary)" }}
                        title={row.created_at}
                      >
                        {formatTime(row.created_at)}
                      </span>
                      <span
                        className="ml-1 text-[10px]"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {formatDate(row.created_at)}
                      </span>
                    </TD>
                    <TD>
                      <button
                        type="button"
                        className="font-mono-data text-[12px]"
                        style={{ color: "var(--accent)" }}
                        onClick={() =>
                          setFilter((f) => ({ ...f, event_name: row.event_name }))
                        }
                      >
                        {row.event_name}
                      </button>
                    </TD>
                    <TD>
                      <button
                        type="button"
                        className="font-mono-data text-[11px]"
                        style={{ color: "var(--text-secondary)" }}
                        onClick={() => {
                          setDraftDistinct(row.distinct_id);
                          setFilter((f) => ({
                            ...f,
                            distinct_id: row.distinct_id,
                          }));
                        }}
                      >
                        {row.distinct_id}
                      </button>
                    </TD>
                    <TD>
                      <Badge tone="default">{row.source}</Badge>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-[11px]"
                        style={{ color: "var(--text-secondary)" }}
                        title={row.url ?? undefined}
                      >
                        {row.url ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <PropertiesCell row={row} />
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </div>

        {/* Quick start snippet */}
        <div
          className="rounded border px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <div className="label-caps mb-2">Track an event</div>
          <pre
            className="font-mono-data text-[11px] overflow-x-auto p-3 rounded"
            style={{
              background: "var(--bg-base)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
            }}
          >
{`fetch('/v1/track', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    event: 'page.viewed',
    distinct_id: 'anon-' + crypto.randomUUID(),
    url: location.pathname,
    properties: { referrer: document.referrer }
  })
})`}
          </pre>
        </div>
      </div>
    </div>
  );
}
