"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Button, ErrorState, Skeleton } from "@/components/ui";
import { EventDetailDrawer } from "@/features/audit-analytics/_components/event-detail-drawer";
import { EventsTable } from "@/features/audit-analytics/_components/events-table";
import { FilterBar } from "@/features/audit-analytics/_components/filter-bar";
import { FunnelBuilder } from "@/features/audit-analytics/_components/funnel-builder";
import { RetentionGrid } from "@/features/audit-analytics/_components/retention-grid";
import { SavedViewsPanel } from "@/features/audit-analytics/_components/saved-views-panel";
import { StatsPanel } from "@/features/audit-analytics/_components/stats-panel";
import {
  useAuditEventStats,
  useAuditEvents,
  useAuditTailPoll,
  useLoadMore,
  useOutboxCursor,
} from "@/features/audit-analytics/hooks/use-audit-events";
import type { AuditBucket, AuditEventFilter, AuditEventRow } from "@/types/api";

const EMPTY_FILTER: AuditEventFilter = {};
const LIVE_INTERVAL_MS = 3000;

type Tab = "explorer" | "analytics";

function buildCsvUrl(filter: AuditEventFilter): string {
  const params = new URLSearchParams();
  params.set("format", "csv");
  if (filter.event_key) params.set("event_key", filter.event_key);
  if (filter.category_code) params.set("category_code", filter.category_code);
  if (filter.outcome) params.set("outcome", filter.outcome);
  if (filter.actor_user_id) params.set("actor_user_id", filter.actor_user_id);
  if (filter.since) params.set("since", filter.since);
  if (filter.until) params.set("until", filter.until);
  if (filter.q) params.set("q", filter.q);
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";
  return `${base}/v1/audit-events?${params.toString()}`;
}

export default function AuditExplorerPage() {
  const [tab, setTab] = useState<Tab>("explorer");
  const [filter, setFilter] = useState<AuditEventFilter>(EMPTY_FILTER);
  const [bucket, setBucket] = useState<AuditBucket>("hour");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [accumulated, setAccumulated] = useState<AuditEventRow[]>([]);
  const [tailCursor, setTailCursor] = useState<string | null>(null);

  // Live tail state
  const [liveOn, setLiveOn] = useState(false);
  const [liveItems, setLiveItems] = useState<AuditEventRow[]>([]);
  const liveSinceId = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const listKey = useMemo(() => JSON.stringify(filter), [filter]);

  const { data, isLoading, isError, error, refetch, isFetching } = useAuditEvents(filter);
  const stats = useAuditEventStats(filter, bucket);
  const loadMore = useLoadMore();
  const outboxCursor = useOutboxCursor();
  const tailPoll = useAuditTailPoll();

  // Initialise live cursor from outbox on mount
  useEffect(() => {
    if (outboxCursor.data?.last_outbox_id != null) {
      liveSinceId.current = outboxCursor.data.last_outbox_id;
    }
  }, [outboxCursor.data]);

  // Manage polling interval
  useEffect(() => {
    if (liveOn) {
      intervalRef.current = setInterval(async () => {
        try {
          const res = await tailPoll.mutateAsync({
            since_id: liveSinceId.current,
            org_id: filter.org_id ?? null,
          });
          if (res.items.length > 0) {
            liveSinceId.current = res.last_outbox_id;
            setLiveItems((prev) => {
              const ids = new Set(prev.map((r) => r.id));
              const fresh = res.items
                .filter((r) => !ids.has(r.id))
                .map((r) => ({
                  ...r,
                  event_description: undefined,
                  category_label: undefined,
                  actor_session_id: undefined,
                  workspace_id: undefined,
                  span_id: r.trace_id,
                  parent_span_id: undefined,
                } as unknown as AuditEventRow));
              return [...fresh, ...prev].slice(0, 200); // cap display
            });
          }
        } catch {
          // swallow — live tail errors are non-critical
        }
      }, LIVE_INTERVAL_MS);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveOn, filter.org_id]);

  // On filter change, reset pagination + accumulated
  useMemo(() => {
    setAccumulated([]);
    setTailCursor(null);
    setLiveItems([]);
  }, [listKey]);

  /**
   * Client-side filter for live-tail items.
   */
  const matchesFilter = useMemo(
    () => (r: AuditEventRow) => {
      if (filter.event_key) {
        const want = filter.event_key;
        if (want.endsWith(".*")) {
          const prefix = want.slice(0, -2);
          if (!r.event_key?.startsWith(prefix)) return false;
        } else if (r.event_key !== want) {
          return false;
        }
      }
      if (filter.category_code && r.category_code !== filter.category_code) {
        return false;
      }
      if (filter.outcome && r.outcome !== filter.outcome) return false;
      if (filter.actor_user_id && r.actor_user_id !== filter.actor_user_id) {
        return false;
      }
      if (filter.q) {
        const q = filter.q.toLowerCase();
        const hay = JSON.stringify(r.metadata ?? {}).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    },
    [filter.event_key, filter.category_code, filter.outcome, filter.actor_user_id, filter.q],
  );

  const items: AuditEventRow[] = useMemo(() => {
    if (liveOn && liveItems.length > 0) {
      const baseIds = new Set((data?.items ?? []).map((r) => r.id));
      const liveFiltered = liveItems
        .filter((r) => !baseIds.has(r.id))
        .filter(matchesFilter);
      return [...liveFiltered, ...(data?.items ?? [])];
    }
    const firstPage = data?.items ?? [];
    const ids = new Set(firstPage.map((r) => r.id));
    const extras = accumulated.filter((r) => !ids.has(r.id));
    return [...firstPage, ...extras];
  }, [data, accumulated, liveOn, liveItems, matchesFilter]);

  const effectiveCursor = tailCursor ?? data?.next_cursor ?? null;

  return (
    <>
      <PageHeader
        title="Audit Explorer"
        description="Immutable event ledger — every effect, every actor, every tenant."
        testId="heading-audit-explorer"
        actions={
          <div className="flex items-center gap-2">
            <a
              href={buildCsvUrl(filter)}
              download="audit_events.csv"
              data-testid="audit-export-csv"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "6px",
                border: "1px solid var(--border-bright)",
                background: "var(--bg-elevated)",
                color: "var(--text-secondary)",
                fontSize: "12px",
                fontWeight: 500,
                textDecoration: "none",
                transition: "color 0.15s, border-color 0.15s",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLAnchorElement).style.color = "var(--text-primary)";
                (e.currentTarget as HTMLAnchorElement).style.borderColor = "var(--accent)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLAnchorElement).style.color = "var(--text-secondary)";
                (e.currentTarget as HTMLAnchorElement).style.borderColor = "var(--border-bright)";
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M6 1v7M3 5l3 3 3-3M1 9v1a1 1 0 001 1h8a1 1 0 001-1V9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Export CSV
            </a>
            <button
              onClick={() => {
                setLiveOn((v) => !v);
                setLiveItems([]);
                if (outboxCursor.data?.last_outbox_id != null) {
                  liveSinceId.current = outboxCursor.data.last_outbox_id;
                }
              }}
              data-testid="audit-live-toggle"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "6px",
                border: liveOn ? "1px solid var(--success)" : "1px solid var(--border-bright)",
                background: liveOn ? "var(--success-muted)" : "var(--bg-elevated)",
                color: liveOn ? "var(--success)" : "var(--text-secondary)",
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {liveOn && (
                <span style={{ position: "relative", display: "inline-flex", width: 8, height: 8 }}>
                  <span
                    style={{
                      position: "absolute",
                      inset: 0,
                      borderRadius: "50%",
                      background: "var(--success)",
                      opacity: 0.5,
                      animation: "ping 1s cubic-bezier(0, 0, 0.2, 1) infinite",
                    }}
                  />
                  <span
                    style={{
                      position: "relative",
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "var(--success)",
                    }}
                  />
                </span>
              )}
              {liveOn ? "Live" : "Go Live"}
            </button>
            <Button
              data-testid="audit-refresh"
              variant="secondary"
              onClick={() => {
                setAccumulated([]);
                setTailCursor(null);
                setLiveItems([]);
                void refetch();
                void stats.refetch();
              }}
              loading={isFetching || stats.isFetching}
            >
              Refresh
            </Button>
          </div>
        }
      />

      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--border)",
          paddingLeft: 32,
          paddingRight: 32,
          background: "var(--bg-base)",
        }}
      >
        {(["explorer", "analytics"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            data-testid={`audit-tab-${t}`}
            style={{
              padding: "10px 16px",
              fontSize: "13px",
              fontWeight: 500,
              textTransform: "capitalize",
              color: tab === t ? "var(--text-primary)" : "var(--text-muted)",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              background: "none",
              border: "none",
              cursor: "pointer",
              transition: "color 0.15s",
              letterSpacing: "0.01em",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="audit-explorer-body"
      >
        {tab === "explorer" && (
          <div className="flex flex-col gap-5">
            {liveOn && (
              <div
                data-testid="audit-live-banner"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: "1px solid var(--success)",
                  background: "var(--success-muted)",
                  color: "var(--success)",
                  fontSize: 12,
                }}
              >
                <span style={{ position: "relative", display: "inline-flex", width: 8, height: 8 }}>
                  <span
                    style={{
                      position: "absolute",
                      inset: 0,
                      borderRadius: "50%",
                      background: "var(--success)",
                      opacity: 0.5,
                      animation: "ping 1s cubic-bezier(0, 0, 0.2, 1) infinite",
                    }}
                  />
                  <span
                    style={{
                      position: "relative",
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "var(--success)",
                    }}
                  />
                </span>
                <span>
                  Live tail active — polling every {LIVE_INTERVAL_MS / 1000}s.
                  {liveItems.length > 0 && (
                    <span style={{ marginLeft: 4, fontWeight: 600 }}>
                      {liveItems.length} new event{liveItems.length !== 1 ? "s" : ""} received.
                    </span>
                  )}
                </span>
              </div>
            )}

            {/* Immutability notice */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 12px",
                borderRadius: 6,
                background: "var(--accent-muted)",
                border: "1px solid var(--border)",
                fontSize: 11,
                color: "var(--text-muted)",
                letterSpacing: "0.04em",
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
                <path d="M6 1L1 4v3c0 2.5 2.1 4.8 5 5.4C8.9 11.8 11 9.5 11 7V4L6 1z" stroke="var(--accent)" strokeWidth="1.2" fill="none"/>
                <path d="M4 6l1.5 1.5L8 4.5" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              IMMUTABLE RECORD — Events are append-only and cannot be modified or deleted. SHA-256 integrity chain enforced.
            </div>

            <FilterBar
              value={filter}
              bucket={bucket}
              onChange={setFilter}
              onBucketChange={setBucket}
              onReset={() => {
                setFilter(EMPTY_FILTER);
                setBucket("hour");
              }}
            />

            <StatsPanel data={stats.data} isLoading={stats.isLoading} />

            {isLoading && (
              <div className="flex flex-col gap-2">
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </div>
            )}
            {isError && (
              <ErrorState
                message={error instanceof Error ? error.message : "Load failed"}
                retry={() => refetch()}
              />
            )}
            {data && (
              <>
                <EventsTable items={items} onRowClick={setSelectedId} />
                {!liveOn && effectiveCursor && (
                  <div style={{ display: "flex", justifyContent: "center", padding: "8px 0" }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={loadMore.isPending}
                      data-testid="audit-load-more"
                      onClick={async () => {
                        const res = await loadMore.mutateAsync({
                          filters: filter,
                          cursor: effectiveCursor,
                          limit: 50,
                        });
                        setAccumulated((prev) => {
                          const ids = new Set(prev.map((r) => r.id));
                          const newOnes = res.items.filter((r) => !ids.has(r.id));
                          return [...prev, ...newOnes];
                        });
                        setTailCursor(res.next_cursor);
                      }}
                    >
                      {loadMore.isPending ? "Loading…" : "Load more"}
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {tab === "analytics" && (
          <div className="flex flex-col gap-6">
            <SavedViewsPanel
              currentFilter={filter}
              currentBucket={bucket}
              onLoad={(f, b) => {
                setFilter(f);
                setBucket(b);
                setTab("explorer");
              }}
            />
            <FunnelBuilder />
            <RetentionGrid />
          </div>
        )}
      </div>

      <EventDetailDrawer
        eventId={selectedId}
        onClose={() => setSelectedId(null)}
      />
    </>
  );
}
