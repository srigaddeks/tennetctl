"use client";

/**
 * AuthZ Audit Explorer — pre-filtered view scoped to authorization, role,
 * flag, SSO/MFA, and session events. Fetches up to 1 000 events client-side
 * and filters locally so every category pill works without a dedicated backend
 * prefix endpoint (the backend event_key param is an exact match, not a prefix).
 *
 * API GAP (TODO): The backend `event_key` query param is an exact match only.
 * Prefix/glob filtering (e.g. "iam.roles.*") is not supported server-side.
 * Workaround: we fetch a broad set (limit 1000) and filter on the client.
 * Once the backend adds event_key_prefix support, replace the broad fetch
 * with targeted calls and remove the AUTHZ_PREFIXES client-side filter pass.
 *
 * API GAP (TODO): `AuditEventFilter.category_code` only accepts the 4 system
 * codes ("system" | "user" | "integration" | "setup"). It cannot filter by
 * domain-level categories like "iam" or "authz". Client-side prefix matching
 * on event_key is the current substitute.
 */

import {
  Flag,
  KeyRound,
  Search,
  ShieldAlert,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { PageHeader } from "@/components/page-header";
import {
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import {
  ALL_AUTHZ_PREFIXES,
  CATEGORIES,
  CATEGORY_META,
  TIME_RANGE_LABELS,
  type CategoryCode,
  type StatCardDef,
  type TimeRange,
  dateGroupLabel,
  deriveCategoryCode,
  matchesPrefixes,
  sinceForRange,
} from "@/features/audit-analytics/_components/authz-constants";
import { DateGroup } from "@/features/audit-analytics/_components/authz-event-row";
import {
  CategoryPill,
  OutcomePill,
  TimeRangePill,
} from "@/features/audit-analytics/_components/authz-pills";
import { StatCards } from "@/features/audit-analytics/_components/authz-stat-cards";
import {
  useAuditEvents,
  useLoadMore,
} from "@/features/audit-analytics/hooks/use-audit-events";
import type { AuditEventRow, AuditOutcome } from "@/types/api";

export default function AuthzAuditExplorerPage() {
  const [category, setCategory] = useState<CategoryCode>("all");
  const [outcome, setOutcome] = useState<"all" | AuditOutcome>("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [search, setSearch] = useState("");
  const [appFilter, setAppFilter] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [accumulated, setAccumulated] = useState<AuditEventRow[]>([]);
  const [tailCursor, setTailCursor] = useState<string | null>(null);

  // Broad fetch — no server-side prefix filter available; apply locally.
  const since = sinceForRange(timeRange);
  const { data, isLoading, isError, error, refetch, isFetching } =
    useAuditEvents({ since, outcome: outcome === "all" ? undefined : outcome }, { limit: 1000 });
  const loadMore = useLoadMore();

  // Reset pagination when filters change
  const resetPagination = () => {
    setAccumulated([]);
    setTailCursor(null);
  };

  // Merge first page + accumulated pages
  const rawItems: AuditEventRow[] = useMemo(() => {
    const first = data?.items ?? [];
    const ids = new Set(first.map((r) => r.id));
    const extras = accumulated.filter((r) => !ids.has(r.id));
    return [...first, ...extras];
  }, [data, accumulated]);

  // Client-side: keep only events whose event_key matches any authz prefix
  const authzItems: AuditEventRow[] = useMemo(
    () =>
      rawItems.filter((r) => matchesPrefixes(r.event_key, ALL_AUTHZ_PREFIXES)),
    [rawItems],
  );

  // Apply category filter
  const categoryFiltered: AuditEventRow[] = useMemo(() => {
    if (category === "all") return authzItems;
    return authzItems.filter((r) =>
      matchesPrefixes(r.event_key, CATEGORY_META[category].prefixes),
    );
  }, [authzItems, category]);

  // Apply search filter
  const displayed: AuditEventRow[] = useMemo(() => {
    if (!search.trim()) return categoryFiltered;
    const q = search.toLowerCase();
    return categoryFiltered.filter(
      (r) =>
        r.event_key.toLowerCase().includes(q) ||
        (r.actor_user_id ?? "").toLowerCase().includes(q) ||
        (r.event_label ?? "").toLowerCase().includes(q),
    );
  }, [categoryFiltered, search]);

  // Stats derived from authzItems (all authz events in range, all outcomes)
  const stats = useMemo(() => {
    const total = authzItems.length;
    const permissions = authzItems.filter((r) =>
      matchesPrefixes(r.event_key, CATEGORY_META.permissions.prefixes),
    ).length;
    const flags = authzItems.filter((r) =>
      matchesPrefixes(r.event_key, CATEGORY_META.flags.prefixes),
    ).length;
    const roles = authzItems.filter((r) =>
      matchesPrefixes(r.event_key, CATEGORY_META.roles.prefixes),
    ).length;
    const failures = authzItems.filter((r) => r.outcome === "failure").length;
    return { total, permissions, flags, roles, failures };
  }, [authzItems]);

  // Category counts for pills (scoped to current outcome filter)
  const categoryCounts = useMemo(() => {
    const base =
      outcome === "all"
        ? authzItems
        : authzItems.filter((r) => r.outcome === outcome);
    const result: Record<CategoryCode, number> = {
      all: base.length,
      permissions: 0,
      flags: 0,
      roles: 0,
      sso_mfa: 0,
      sessions: 0,
    };
    for (const r of base) {
      const cat = deriveCategoryCode(r.event_key);
      if (cat !== "all") result[cat]++;
    }
    return result;
  }, [authzItems, outcome]);

  // Outcome counts for pills (scoped to current category filter)
  const outcomeCounts = useMemo(() => {
    const base =
      category === "all"
        ? authzItems
        : authzItems.filter((r) =>
            matchesPrefixes(r.event_key, CATEGORY_META[category].prefixes),
          );
    return {
      all: base.length,
      success: base.filter((r) => r.outcome === "success").length,
      failure: base.filter((r) => r.outcome === "failure").length,
    };
  }, [authzItems, category]);

  // Group displayed events by date
  const groups: { label: string; events: AuditEventRow[] }[] = useMemo(() => {
    const map = new Map<string, AuditEventRow[]>();
    for (const evt of displayed) {
      const lbl = dateGroupLabel(evt.created_at);
      if (!map.has(lbl)) map.set(lbl, []);
      map.get(lbl)!.push(evt);
    }
    return Array.from(map.entries()).map(([label, events]) => ({
      label,
      events,
    }));
  }, [displayed]);

  function toggleExpanded(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  const statCards: StatCardDef[] = [
    {
      kind: "total",
      label: "Total (time range)",
      value: stats.total,
      icon: ShieldCheck,
      borderCls: "border-l-zinc-900 dark:border-l-zinc-100",
      numCls: "text-zinc-900 dark:text-zinc-50",
    },
    {
      kind: "permissions",
      label: "Permission checks",
      value: stats.permissions,
      icon: KeyRound,
      borderCls: CATEGORY_META.permissions.borderCls,
      numCls: CATEGORY_META.permissions.numCls,
    },
    {
      kind: "flags",
      label: "Flag evaluations",
      value: stats.flags,
      icon: Flag,
      borderCls: CATEGORY_META.flags.borderCls,
      numCls: CATEGORY_META.flags.numCls,
    },
    {
      kind: "roles",
      label: "Role mutations",
      value: stats.roles,
      icon: Users,
      borderCls: CATEGORY_META.roles.borderCls,
      numCls: CATEGORY_META.roles.numCls,
    },
    {
      kind: "failures",
      label: "Failures",
      value: stats.failures,
      icon: ShieldAlert,
      borderCls: "border-l-red-500",
      numCls: "text-red-600 dark:text-red-400",
    },
  ];

  const effectiveCursor = tailCursor ?? data?.next_cursor ?? null;
  const hasMore = effectiveCursor !== null;

  return (
    <>
      <PageHeader
        title="AuthZ Audit Explorer"
        description="Pre-filtered authorization trail — ALLOW/DENY decisions, role mutations, flag evaluations, SSO/MFA, and session events."
        testId="heading-authz-audit-explorer"
        actions={
          <div className="flex items-center gap-2">
            {/* Decision legend */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "4px 12px",
                borderRadius: 6,
                border: "1px solid var(--border)",
                background: "var(--bg-elevated)",
                fontSize: 11,
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "var(--success)",
                    display: "inline-block",
                  }}
                />
                <span style={{ color: "var(--success)", fontWeight: 600, letterSpacing: "0.05em" }}>ALLOW</span>
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: "var(--danger)",
                    display: "inline-block",
                  }}
                />
                <span style={{ color: "var(--danger)", fontWeight: 600, letterSpacing: "0.05em" }}>DENY</span>
              </span>
            </div>
            <Button
              variant="secondary"
              onClick={() => {
                resetPagination();
                void refetch();
              }}
              loading={isFetching}
              data-testid="authz-audit-refresh"
            >
              Refresh
            </Button>
          </div>
        }
      />

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 20 }}
      >
        <ApplicationScopeBar
          appId={appFilter}
          onChange={setAppFilter}
          label="AuthZ decisions for application"
        />

        {/* Stat cards */}
        {!isLoading && !isError && <StatCards cards={statCards} />}
        {isLoading && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        )}

        {/* Filter bar */}
        {!isError && (
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 8,
              padding: "12px 16px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg-surface)",
            }}
          >
            {/* Category pills */}
            {CATEGORIES.map((cat) => (
              <CategoryPill
                key={cat}
                code={cat}
                count={categoryCounts[cat]}
                active={category === cat}
                onClick={() => {
                  setCategory(cat);
                  resetPagination();
                }}
              />
            ))}

            <span
              style={{
                width: 1,
                height: 20,
                background: "var(--border)",
                flexShrink: 0,
              }}
            />

            {/* Outcome pills */}
            {(["all", "success", "failure"] as const).map((o) => (
              <OutcomePill
                key={o}
                value={o}
                active={outcome === o}
                count={outcomeCounts[o]}
                onClick={() => {
                  setOutcome(o);
                  resetPagination();
                }}
              />
            ))}

            <span
              style={{
                width: 1,
                height: 20,
                background: "var(--border)",
                flexShrink: 0,
              }}
            />

            {/* Time range pills */}
            {(["1h", "24h", "7d", "30d"] as TimeRange[]).map((t) => (
              <TimeRangePill
                key={t}
                value={t}
                active={timeRange === t}
                onClick={() => {
                  setTimeRange(t);
                  resetPagination();
                }}
              />
            ))}

            {/* Active filter chips */}
            {category !== "all" && (
              <button
                type="button"
                onClick={() => {
                  setCategory("all");
                  resetPagination();
                }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  padding: "2px 8px",
                  borderRadius: 9999,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                  color: "var(--text-secondary)",
                  fontSize: 11,
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                {CATEGORY_META[category].label}
                <X style={{ width: 10, height: 10 }} />
              </button>
            )}
            {outcome !== "all" && (
              <button
                type="button"
                onClick={() => {
                  setOutcome("all");
                  resetPagination();
                }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  padding: "2px 8px",
                  borderRadius: 9999,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                  color: "var(--text-secondary)",
                  fontSize: 11,
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                outcome: {outcome}
                <X style={{ width: 10, height: 10 }} />
              </button>
            )}

            {/* Search */}
            <div style={{ position: "relative", marginLeft: "auto", width: 224 }}>
              <Search
                style={{
                  position: "absolute",
                  left: 10,
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: 14,
                  height: 14,
                  color: "var(--text-muted)",
                  pointerEvents: "none",
                }}
              />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search event key or actor…"
                data-testid="authz-audit-search"
                style={{
                  height: 28,
                  width: "100%",
                  paddingLeft: 32,
                  paddingRight: search ? 28 : 8,
                  borderRadius: 6,
                  border: "1px solid var(--border-bright)",
                  background: "var(--bg-elevated)",
                  color: "var(--text-primary)",
                  fontSize: 12,
                  outline: "none",
                }}
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  style={{
                    position: "absolute",
                    right: 8,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    background: "none",
                    border: "none",
                    padding: 0,
                  }}
                >
                  <X style={{ width: 12, height: 12 }} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Loading skeleton */}
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-9 w-full rounded-lg" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={
              error instanceof Error ? error.message : "Failed to load events"
            }
            retry={() => refetch()}
          />
        )}

        {/* Event list grouped by date */}
        {data && displayed.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {groups.map(({ label, events }) => (
              <DateGroup
                key={label}
                label={label}
                events={events}
                expandedId={expandedId}
                onToggle={toggleExpanded}
              />
            ))}
          </div>
        )}

        {/* Empty: no authz events at all in range */}
        {data && authzItems.length === 0 && (
          <EmptyState
            title="No AuthZ events"
            description={`No authorization events found in the last ${TIME_RANGE_LABELS[timeRange]}. Try a wider time range or check that IAM events are being emitted.`}
          />
        )}

        {/* Empty: filters produced nothing but data exists */}
        {data && authzItems.length > 0 && displayed.length === 0 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 12,
              borderRadius: 8,
              border: "1px dashed var(--border-bright)",
              padding: "48px 24px",
              textAlign: "center",
            }}
          >
            <ShieldAlert style={{ width: 32, height: 32, color: "var(--text-muted)" }} />
            <p style={{ fontSize: 14, fontWeight: 500, color: "var(--text-secondary)" }}>
              {CATEGORY_META[category].emptyMsg}
            </p>
            <button
              type="button"
              onClick={() => {
                setCategory("all");
                setOutcome("all");
                setSearch("");
                resetPagination();
              }}
              style={{
                fontSize: 12,
                fontWeight: 500,
                color: "var(--accent)",
                textDecoration: "underline",
                background: "none",
                border: "none",
                cursor: "pointer",
              }}
            >
              Clear filters
            </button>
          </div>
        )}

        {/* Load more */}
        {data && hasMore && (
          <div style={{ display: "flex", justifyContent: "center", padding: "8px 0" }}>
            <Button
              variant="secondary"
              size="sm"
              loading={loadMore.isPending}
              data-testid="authz-audit-load-more"
              onClick={async () => {
                if (!effectiveCursor) return;
                const res = await loadMore.mutateAsync({
                  filters: {
                    since,
                    outcome: outcome === "all" ? undefined : outcome,
                  },
                  cursor: effectiveCursor,
                  limit: 1000,
                });
                setAccumulated((prev) => {
                  const ids = new Set(prev.map((r) => r.id));
                  const fresh = res.items.filter((r) => !ids.has(r.id));
                  return [...prev, ...fresh];
                });
                setTailCursor(res.next_cursor);
              }}
            >
              {loadMore.isPending ? "Loading…" : "Load more"}
            </Button>
          </div>
        )}
      </div>
    </>
  );
}
