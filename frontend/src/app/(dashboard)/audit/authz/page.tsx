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

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Clock,
  Flag,
  KeyRound,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import {
  useAuditEvents,
  useLoadMore,
} from "@/features/audit-analytics/hooks/use-audit-events";
import { cn } from "@/lib/cn";
import type { AuditEventRow, AuditOutcome } from "@/types/api";

// ─── Category definitions ─────────────────────────────────────────────────────

type CategoryCode =
  | "all"
  | "permissions"
  | "flags"
  | "roles"
  | "sso_mfa"
  | "sessions";

type CategoryMeta = {
  label: string;
  icon: typeof Shield;
  prefixes: string[];
  borderCls: string;
  badgeCls: string;
  numCls: string;
  emptyMsg: string;
};

const CATEGORY_META: Record<CategoryCode, CategoryMeta> = {
  all: {
    label: "All",
    icon: ShieldCheck,
    prefixes: [
      "authz.",
      "iam.users.",
      "flags.",
      "featureflags.",
      "iam.roles.",
      "iam.groups.",
      "iam.oidc.",
      "iam.saml.",
      "iam.mfa.",
      "iam.sessions.",
      "iam.auth.",
    ],
    borderCls: "border-l-zinc-900 dark:border-l-zinc-100",
    badgeCls:
      "bg-zinc-100 border-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300",
    numCls: "text-zinc-900 dark:text-zinc-50",
    emptyMsg: "No AuthZ events in this time range — try widening the window.",
  },
  permissions: {
    label: "Permissions",
    icon: KeyRound,
    prefixes: ["authz.permission.", "iam.users."],
    borderCls: "border-l-violet-500",
    badgeCls:
      "bg-violet-50 border-violet-200 text-violet-700 dark:bg-violet-900/30 dark:border-violet-800 dark:text-violet-300",
    numCls: "text-violet-600 dark:text-violet-400",
    emptyMsg:
      "No permission checks in this time range — tighten the time range or widen the categories.",
  },
  flags: {
    label: "Flags",
    icon: Flag,
    prefixes: ["flags.", "featureflags."],
    borderCls: "border-l-amber-500",
    badgeCls:
      "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/30 dark:border-amber-800 dark:text-amber-300",
    numCls: "text-amber-600 dark:text-amber-400",
    emptyMsg:
      "No flag evaluations in this time range — ensure feature flag activity is being recorded.",
  },
  roles: {
    label: "Roles",
    icon: Users,
    prefixes: ["iam.roles.", "iam.groups."],
    borderCls: "border-l-blue-500",
    badgeCls:
      "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300",
    numCls: "text-blue-600 dark:text-blue-400",
    emptyMsg:
      "No role mutations in this time range — role create/assign/revoke events will appear here.",
  },
  sso_mfa: {
    label: "SSO / MFA",
    icon: Shield,
    prefixes: ["iam.oidc.", "iam.saml.", "iam.mfa."],
    borderCls: "border-l-emerald-500",
    badgeCls:
      "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-300",
    numCls: "text-emerald-600 dark:text-emerald-400",
    emptyMsg:
      "No SSO or MFA events in this time range — OIDC/SAML/MFA activity will appear here.",
  },
  sessions: {
    label: "Sessions",
    icon: Clock,
    prefixes: ["iam.sessions.", "iam.auth."],
    borderCls: "border-l-rose-500",
    badgeCls:
      "bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-900/30 dark:border-rose-800 dark:text-rose-300",
    numCls: "text-rose-600 dark:text-rose-400",
    emptyMsg:
      "No session or auth events in this time range — login and session activity appears here.",
  },
};

const CATEGORIES = Object.keys(CATEGORY_META) as CategoryCode[];

// All authz prefixes combined (for the broad server-side q-filter fallback)
const ALL_AUTHZ_PREFIXES = CATEGORY_META.all.prefixes;

// ─── Time range helpers ───────────────────────────────────────────────────────

type TimeRange = "1h" | "24h" | "7d" | "30d";

const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  "1h": "1h",
  "24h": "24h",
  "7d": "7d",
  "30d": "30d",
};

function sinceForRange(range: TimeRange): string {
  const now = new Date();
  const ms: Record<TimeRange, number> = {
    "1h": 60 * 60 * 1000,
    "24h": 24 * 60 * 60 * 1000,
    "7d": 7 * 24 * 60 * 60 * 1000,
    "30d": 30 * 24 * 60 * 60 * 1000,
  };
  return new Date(now.getTime() - ms[range]).toISOString();
}

// ─── Relative time ────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ─── Date group label ─────────────────────────────────────────────────────────

function dateGroupLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// ─── Event key prefix check ───────────────────────────────────────────────────

function matchesPrefixes(eventKey: string, prefixes: string[]): boolean {
  return prefixes.some((p) => eventKey.startsWith(p));
}

// ─── Category badge ───────────────────────────────────────────────────────────

function deriveCategoryCode(eventKey: string): CategoryCode {
  for (const cat of CATEGORIES) {
    if (cat === "all") continue;
    if (matchesPrefixes(eventKey, CATEGORY_META[cat].prefixes)) return cat;
  }
  return "all";
}

// ─── Stat cards ───────────────────────────────────────────────────────────────

type StatCardDef = {
  kind: string;
  label: string;
  value: number;
  icon: typeof Shield;
  borderCls: string;
  numCls: string;
};

function StatCards({ cards }: { cards: StatCardDef[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map(({ kind, label, value, icon: Icon, borderCls, numCls }) => (
        <div
          key={kind}
          className={cn(
            "flex items-center gap-3 rounded-xl border border-l-[3px] bg-white px-4 py-3 dark:bg-zinc-950",
            "border-zinc-200 dark:border-zinc-800",
            borderCls,
          )}
          data-testid={`stat-card-${kind}`}
        >
          <div className="shrink-0 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">
            <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </div>
          <div className="min-w-0">
            <span
              className={cn(
                "block text-2xl font-bold tabular-nums leading-none",
                numCls,
              )}
            >
              {value}
            </span>
            <span className="mt-0.5 block truncate text-[11px] text-zinc-500 dark:text-zinc-400">
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Category pill ────────────────────────────────────────────────────────────

function CategoryPill({
  code,
  count,
  active,
  onClick,
}: {
  code: CategoryCode;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  const meta = CATEGORY_META[code];
  const Icon = meta.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`category-filter-${code}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      <Icon className="h-3 w-3" />
      {meta.label}
      <span
        className={cn(
          "tabular-nums",
          active ? "opacity-70" : "text-zinc-400",
        )}
      >
        {count}
      </span>
    </button>
  );
}

// ─── Outcome pill ─────────────────────────────────────────────────────────────

function OutcomePill({
  value,
  active,
  count,
  onClick,
}: {
  value: "all" | AuditOutcome;
  active: boolean;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`outcome-filter-${value}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      {value === "success" && (
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      )}
      {value === "failure" && (
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
      )}
      {value === "all" ? "All outcomes" : value}
      <span
        className={cn("tabular-nums", active ? "opacity-70" : "text-zinc-400")}
      >
        {count}
      </span>
    </button>
  );
}

// ─── Time range pill ──────────────────────────────────────────────────────────

function TimeRangePill({
  value,
  active,
  onClick,
}: {
  value: TimeRange;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`time-filter-${value}`}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium tabular-nums transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      {TIME_RANGE_LABELS[value]}
    </button>
  );
}

// ─── Metadata JSON viewer ─────────────────────────────────────────────────────

function MetaJson({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="overflow-x-auto rounded-lg bg-zinc-900 p-3 text-[11px] leading-relaxed text-zinc-100 dark:bg-zinc-950">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

// ─── Event row ────────────────────────────────────────────────────────────────

function EventRow({
  event,
  expanded,
  onToggle,
}: {
  event: AuditEventRow;
  expanded: boolean;
  onToggle: (id: string) => void;
}) {
  const catCode = deriveCategoryCode(event.event_key);
  const catMeta = CATEGORY_META[catCode];

  const actorLabel =
    event.actor_user_id
      ? event.actor_user_id.length > 12
        ? `${event.actor_user_id.slice(0, 8)}…`
        : event.actor_user_id
      : "system";

  return (
    <div
      className={cn(
        "border-b border-zinc-100 last:border-b-0 dark:border-zinc-800/60",
      )}
      data-testid={`audit-row-${event.id}`}
    >
      {/* Collapsed row */}
      <div
        className={cn(
          "grid grid-cols-[auto_auto_1fr_auto_auto_auto] items-center gap-x-3 border-l-[3px] px-4 py-2.5 transition hover:bg-zinc-50 dark:hover:bg-zinc-900/30",
          catMeta.borderCls,
          expanded && "bg-zinc-50 dark:bg-zinc-900/40",
        )}
      >
        {/* Expand toggle */}
        <button
          type="button"
          onClick={() => onToggle(event.id)}
          data-testid={`expand-row-${event.id}`}
          title={expanded ? "Collapse" : "Expand"}
          className="shrink-0 rounded-md p-1 text-zinc-400 transition hover:bg-zinc-200 hover:text-zinc-700 dark:hover:bg-zinc-700 dark:hover:text-zinc-200"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </button>

        {/* Timestamp */}
        <span
          className="shrink-0 font-mono text-[11px] text-zinc-400 dark:text-zinc-500"
          title={event.created_at}
        >
          {relativeTime(event.created_at)}
        </span>

        {/* event_key */}
        <code className="min-w-0 truncate font-mono text-xs font-semibold text-zinc-800 dark:text-zinc-200">
          {event.event_key}
        </code>

        {/* Category badge */}
        <span
          className={cn(
            "inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
            catMeta.badgeCls,
          )}
        >
          {catCode === "all" ? "other" : catMeta.label}
        </span>

        {/* Outcome badge */}
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
            event.outcome === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
          )}
        >
          {event.outcome === "failure" && (
            <AlertTriangle className="h-2.5 w-2.5" />
          )}
          {event.outcome}
        </span>

        {/* Actor chip */}
        <span className="shrink-0 rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 font-mono text-[10px] text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          {actorLabel}
        </span>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-zinc-100 bg-zinc-50 px-6 pb-4 pt-3 dark:border-zinc-800 dark:bg-zinc-900/40">
          <div className="grid gap-3 sm:grid-cols-2">
            {/* Left: key info */}
            <div className="flex flex-col gap-2 text-[11px]">
              <Row label="Event key" value={event.event_key} mono />
              {event.event_label && (
                <Row label="Label" value={event.event_label} />
              )}
              {event.event_description && (
                <Row label="Description" value={event.event_description} />
              )}
              <Row label="Outcome" value={event.outcome} />
              <Row
                label="Timestamp"
                value={new Date(event.created_at).toLocaleString()}
              />
              {event.actor_user_id && (
                <Row label="Actor" value={event.actor_user_id} mono />
              )}
              {event.actor_session_id && (
                <Row label="Session" value={event.actor_session_id} mono />
              )}
              {event.org_id && <Row label="Org" value={event.org_id} mono />}
              {event.workspace_id && (
                <Row label="Workspace" value={event.workspace_id} mono />
              )}
              <Row label="Trace ID" value={event.trace_id} mono />
              <Row label="Span ID" value={event.span_id} mono />
              {event.parent_span_id && (
                <Row label="Parent span" value={event.parent_span_id} mono />
              )}
            </div>

            {/* Right: metadata JSON */}
            <div>
              <p className="mb-1.5 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Metadata
              </p>
              <MetaJson data={event.metadata} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="w-20 shrink-0 text-zinc-400 dark:text-zinc-500">
        {label}
      </span>
      <span
        className={cn(
          "break-all text-zinc-700 dark:text-zinc-300",
          mono && "font-mono",
        )}
      >
        {value}
      </span>
    </div>
  );
}

// ─── Date group section ───────────────────────────────────────────────────────

function DateGroup({
  label,
  events,
  expandedId,
  onToggle,
}: {
  label: string;
  events: AuditEventRow[];
  expandedId: string | null;
  onToggle: (id: string) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-zinc-100 dark:hover:bg-zinc-800/50"
      >
        <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-50">
          {label}
        </span>
        <span className="text-[11px] tabular-nums text-zinc-400 dark:text-zinc-500">
          {events.length} event{events.length !== 1 ? "s" : ""}
        </span>
        {open ? (
          <ChevronDown className="ml-auto h-3.5 w-3.5 text-zinc-400" />
        ) : (
          <ChevronRight className="ml-auto h-3.5 w-3.5 text-zinc-400" />
        )}
      </button>

      {open && (
        <div className="mb-3 ml-4 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          {events.map((evt) => (
            <EventRow
              key={evt.id}
              event={evt}
              expanded={expandedId === evt.id}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AuthzAuditExplorerPage() {
  const [category, setCategory] = useState<CategoryCode>("all");
  const [outcome, setOutcome] = useState<"all" | AuditOutcome>("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [search, setSearch] = useState("");
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
        description="Pre-filtered audit trail for authorization, role, flag, SSO/MFA, and session events."
        testId="heading-authz-audit-explorer"
        actions={
          <div className="flex items-center gap-2">
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

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
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
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
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

            <span className="h-5 w-px bg-zinc-200 dark:bg-zinc-700" />

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

            <span className="h-5 w-px bg-zinc-200 dark:bg-zinc-700" />

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
                className="inline-flex items-center gap-1 rounded-full border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                {CATEGORY_META[category].label}
                <X className="ml-0.5 h-2.5 w-2.5" />
              </button>
            )}
            {outcome !== "all" && (
              <button
                type="button"
                onClick={() => {
                  setOutcome("all");
                  resetPagination();
                }}
                className="inline-flex items-center gap-1 rounded-full border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                outcome: {outcome}
                <X className="ml-0.5 h-2.5 w-2.5" />
              </button>
            )}

            {/* Search */}
            <div className="relative ml-auto w-56">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search event key or actor…"
                data-testid="authz-audit-search"
                className="h-7 w-full rounded-lg border border-zinc-200 bg-white pl-7 pr-2 text-xs text-zinc-900 transition focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
                >
                  <X className="h-3 w-3" />
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
          <div className="space-y-1">
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
          <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
            <ShieldAlert className="h-8 w-8 text-zinc-400" />
            <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
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
              className="text-xs font-medium text-zinc-600 underline underline-offset-2 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Clear filters
            </button>
          </div>
        )}

        {/* Load more */}
        {data && hasMore && (
          <div className="flex justify-center py-2">
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
