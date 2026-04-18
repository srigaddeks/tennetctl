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
                  // slim row → compatible with AuditEventRow shape
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
   * Client-side filter for live-tail items. The tail endpoint only respects
   * org scoping; remaining filter dimensions (event_key, category, outcome,
   * actor, q) are applied here so live mode obeys the active filter bar.
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
        description="Every effect, every actor, every tenant — queryable."
        testId="heading-audit-explorer"
        actions={
          <div className="flex items-center gap-2">
            <a
              href={buildCsvUrl(filter)}
              download="audit_events.csv"
              className="inline-flex items-center rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
              data-testid="audit-export-csv"
            >
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
              className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium shadow-sm transition-colors ${
                liveOn
                  ? "border-green-300 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300"
                  : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
              }`}
            >
              {liveOn && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
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
      <div className="flex border-b border-zinc-200 px-8 dark:border-zinc-800">
        {(["explorer", "analytics"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            data-testid={`audit-tab-${t}`}
            className={`px-4 py-2.5 text-sm font-medium capitalize transition-colors ${
              tab === t
                ? "border-b-2 border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100"
                : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="audit-explorer-body">
        {tab === "explorer" && (
          <div className="flex flex-col gap-5">
            {liveOn && (
              <div
                className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300"
                data-testid="audit-live-banner"
              >
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
                </span>
                Live tail active — polling every {LIVE_INTERVAL_MS / 1000}s.
                {liveItems.length > 0 && (
                  <span className="ml-1 font-medium">{liveItems.length} new event{liveItems.length !== 1 ? "s" : ""} received.</span>
                )}
              </div>
            )}

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
                  <div className="flex justify-center py-2">
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
