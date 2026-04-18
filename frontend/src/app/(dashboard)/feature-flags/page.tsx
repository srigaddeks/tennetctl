"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Flag,
  Globe,
  Building2,
  Package,
  Zap,
  ChevronDown,
  ChevronRight,
  Search,
  X,
  AlertTriangle,
  Info,
  Folder,
  FolderOpen,
} from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import { CreateFlagDialog } from "@/features/featureflags/create-flag-dialog";
import { useFlags, useDeleteFlag, useUpdateFlag } from "@/features/featureflags/hooks/use-flags";
import { cn } from "@/lib/cn";
import type { Flag as FlagType, FlagScope } from "@/types/api";

// ─── Constants ───────────────────────────────────────────────────────────────

const SCOPE_META: Record<FlagScope, { label: string; icon: typeof Globe; borderCls: string; numCls: string; badgeTone: "amber" | "blue" | "purple" }> = {
  global:      { label: "Global",      icon: Globe,     borderCls: "border-l-amber-500",  numCls: "text-amber-600 dark:text-amber-400",  badgeTone: "amber"  },
  org:         { label: "Org",         icon: Building2, borderCls: "border-l-blue-500",   numCls: "text-blue-600 dark:text-blue-400",    badgeTone: "blue"   },
  application: { label: "Application", icon: Package,   borderCls: "border-l-purple-500", numCls: "text-purple-600 dark:text-purple-400",badgeTone: "purple" },
};

const VALUE_TYPE_COLORS: Record<string, string> = {
  boolean: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  string:  "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  number:  "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  json:    "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
};

// ─── Confirm dialog ───────────────────────────────────────────────────────────

type ConfirmAction = {
  title: string;
  body: string;
  variant: "info" | "warning" | "danger";
  confirmLabel: string;
  onConfirm: () => Promise<void>;
};

function ConfirmDialog({
  action,
  onClose,
}: {
  action: ConfirmAction | null;
  onClose: () => void;
}) {
  const [running, setRunning] = useState(false);
  if (!action) return null;

  const colorsMap = {
    info:    { icon: Info,          iconColor: "text-blue-600",  bg: "bg-blue-50 dark:bg-blue-950/40",   border: "border-blue-200 dark:border-blue-900/50"  },
    warning: { icon: AlertTriangle, iconColor: "text-amber-600", bg: "bg-amber-50 dark:bg-amber-950/40", border: "border-amber-200 dark:border-amber-900/50" },
    danger:  { icon: AlertTriangle, iconColor: "text-red-600",   bg: "bg-red-50 dark:bg-red-950/40",     border: "border-red-200 dark:border-red-900/50"     },
  };
  const colors = colorsMap[action.variant];
  const IconComp = colors.icon;

  async function confirm() {
    setRunning(true);
    try { await action?.onConfirm(); } catch { /* errors surfaced by caller */ }
    setRunning(false);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      data-testid="confirm-dialog"
    >
      <div className="mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-start gap-3 p-6 pb-4">
          <div className={cn("shrink-0 rounded-xl p-2", colors.bg, colors.border, "border")}>
            <IconComp className={cn("h-5 w-5", colors.iconColor)} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">{action.title}</h2>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{action.body}</p>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <Button variant="secondary" size="sm" onClick={onClose} disabled={running}>Cancel</Button>
          <Button
            size="sm"
            onClick={confirm}
            loading={running}
            variant={action.variant === "danger" ? "danger" : "primary"}
          >
            {action.confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Inline scope / status picker ────────────────────────────────────────────

function InlinePicker<T extends string>({
  current,
  options,
  onPick,
  disabled,
}: {
  current: T;
  options: { value: T; label: string; className: string }[];
  onPick: (v: T) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const cur = options.find((o) => o.value === current) ?? options[0];

  if (open && !disabled) {
    return (
      <div className="flex items-center gap-1 flex-wrap">
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            onClick={() => { setOpen(false); onPick(o.value); }}
            className={cn(
              "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium transition",
              o.className,
              o.value === current && "ring-2 ring-offset-1 ring-zinc-900 dark:ring-zinc-100"
            )}
          >
            {o.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="ml-0.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => !disabled && setOpen(true)}
      title="Click to change"
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium transition hover:opacity-80",
        cur.className,
        disabled && "cursor-default opacity-60"
      )}
    >
      {cur.label}
    </button>
  );
}

// ─── Stat cards ──────────────────────────────────────────────────────────────

type StatCard = {
  label: string;
  value: number;
  icon: typeof Flag;
  borderCls: string;
  numCls: string;
  testId: string;
};

function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map(({ label, value, icon: Icon, borderCls, numCls, testId }) => (
        <div
          key={label}
          className={cn(
            "flex items-center gap-3 rounded-xl border border-l-[3px] bg-white px-4 py-3 dark:bg-zinc-950",
            borderCls,
            "border-zinc-200 dark:border-zinc-800"
          )}
          data-testid={testId}
        >
          <div className="shrink-0 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">
            <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </div>
          <div className="min-w-0">
            <span className={cn("block text-2xl font-bold tabular-nums leading-none", numCls)}>{value}</span>
            <span className="mt-0.5 block truncate text-[11px] text-zinc-500 dark:text-zinc-400">{label}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Flag row ─────────────────────────────────────────────────────────────────

function FlagRow({
  flag,
  onToggleActive,
  onDelete,
}: {
  flag: FlagType;
  onToggleActive: (flag: FlagType) => void;
  onDelete: (flag: FlagType) => void;
}) {
  const scopeMeta = SCOPE_META[flag.scope];
  const ScopeIcon = scopeMeta.icon;

  return (
    <div
      className={cn(
        "grid grid-cols-[auto_1fr_auto] items-start gap-x-3 border-b border-l-[3px] border-zinc-100 px-4 py-3 last:border-b-0",
        "transition hover:bg-zinc-50 dark:border-zinc-900 dark:hover:bg-zinc-900/40",
        scopeMeta.borderCls,
        !flag.is_active && "opacity-60"
      )}
    >
      {/* Scope icon */}
      <div
        className="row-span-2 mt-0.5 shrink-0 rounded-lg bg-zinc-100 p-1.5 dark:bg-zinc-800"
        title={`${scopeMeta.label} scope`}
      >
        <ScopeIcon className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" />
      </div>

      {/* Flag key + description */}
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Link
            href={`/feature-flags/${flag.id}`}
            className="font-mono text-xs font-semibold text-zinc-900 underline-offset-2 hover:underline dark:text-zinc-50"
            data-testid={`test-flag-key-${flag.flag_key}`}
          >
            {flag.flag_key}
          </Link>
          <span
            className={cn(
              "inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
              VALUE_TYPE_COLORS[flag.value_type] ?? VALUE_TYPE_COLORS.string
            )}
          >
            {flag.value_type}
          </span>
        </div>
        {flag.description && (
          <p className="mt-0.5 max-w-lg truncate text-xs text-zinc-500 dark:text-zinc-400">
            {flag.description}
          </p>
        )}
      </div>

      {/* Actions: status + delete */}
      <div className="flex items-center gap-1.5 shrink-0">
        <InlinePicker
          current={flag.is_active ? "active" : "inactive"}
          options={[
            {
              value: "active",
              label: "active",
              className:
                "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-300",
            },
            {
              value: "inactive",
              label: "inactive",
              className:
                "bg-zinc-100 border-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400",
            },
          ]}
          onPick={() => onToggleActive(flag)}
        />
        <span className="h-3.5 w-px bg-zinc-200 dark:bg-zinc-700" />
        <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          {JSON.stringify(flag.default_value)}
        </code>
        <span className="h-3.5 w-px bg-zinc-200 dark:bg-zinc-700" />
        <button
          type="button"
          onClick={() => onDelete(flag)}
          title="Delete flag"
          className="rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
          data-testid={`delete-flag-${flag.flag_key}`}
        >
          <X className="h-3.5 w-3.5" />
        </button>
        <Link
          href={`/feature-flags/${flag.id}`}
          className="rounded-md px-2 py-1 text-xs font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-50"
        >
          Manage
        </Link>
      </div>
    </div>
  );
}

// ─── Scope section (grouped list) ────────────────────────────────────────────

function ScopeSection({
  scope,
  flags,
  onToggleActive,
  onDelete,
}: {
  scope: FlagScope;
  flags: FlagType[];
  onToggleActive: (flag: FlagType) => void;
  onDelete: (flag: FlagType) => void;
}) {
  const [open, setOpen] = useState(true);
  const meta = SCOPE_META[scope];
  const ScopeIcon = meta.icon;
  const activeCount = flags.filter((f) => f.is_active).length;

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-zinc-100 dark:hover:bg-zinc-800/50"
        data-testid={`group-header-${scope}`}
      >
        {open
          ? <FolderOpen className="h-4 w-4 shrink-0 text-zinc-700 dark:text-zinc-300" />
          : <Folder className="h-4 w-4 shrink-0 text-zinc-400" />}
        <ScopeIcon className="h-3.5 w-3.5 shrink-0 text-zinc-500 dark:text-zinc-400" />
        <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          {meta.label}
        </span>
        <span className="ml-auto text-xs tabular-nums text-zinc-500 dark:text-zinc-400">
          {flags.length}
        </span>
        <span className={cn("text-[11px] font-medium tabular-nums", meta.numCls)}>
          {activeCount} active
        </span>
        {open
          ? <ChevronDown className="h-3.5 w-3.5 text-zinc-400" />
          : <ChevronRight className="h-3.5 w-3.5 text-zinc-400" />}
      </button>

      {open && (
        <div className="mb-3 ml-4 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          {flags.map((flag) => (
            <FlagRow
              key={flag.id}
              flag={flag}
              onToggleActive={onToggleActive}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function FlagsListPage() {
  const [scopeFilter, setScopeFilter] = useState<"all" | FlagScope>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [search, setSearch] = useState("");
  const [openCreate, setOpenCreate] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);

  const { data, isLoading, isError, error, refetch } = useFlags({ limit: 500 });
  const updateFlag = useUpdateFlag();
  const deleteFlag = useDeleteFlag();
  const { toast } = useToast();

  const allFlags = data?.items ?? [];

  const stats = useMemo(() => ({
    total:       allFlags.length,
    global:      allFlags.filter((f) => f.scope === "global").length,
    org:         allFlags.filter((f) => f.scope === "org").length,
    application: allFlags.filter((f) => f.scope === "application").length,
    active:      allFlags.filter((f) => f.is_active).length,
    inactive:    allFlags.filter((f) => !f.is_active).length,
  }), [allFlags]);

  const filtered = useMemo(() => {
    let flags = scopeFilter === "all" ? allFlags : allFlags.filter((f) => f.scope === scopeFilter);
    if (statusFilter === "active") flags = flags.filter((f) => f.is_active);
    if (statusFilter === "inactive") flags = flags.filter((f) => !f.is_active);
    if (search.trim()) {
      const q = search.toLowerCase();
      flags = flags.filter(
        (f) =>
          f.flag_key.toLowerCase().includes(q) ||
          (f.description ?? "").toLowerCase().includes(q)
      );
    }
    return flags;
  }, [allFlags, scopeFilter, statusFilter, search]);

  const grouped = (["global", "org", "application"] as FlagScope[]).map((scope) => ({
    scope,
    flags: filtered.filter((f) => f.scope === scope),
  })).filter((g) => g.flags.length > 0);

  function handleToggleActive(flag: FlagType) {
    const next = !flag.is_active;
    setConfirmAction({
      title: `${next ? "Activate" : "Deactivate"} flag?`,
      body: `"${flag.flag_key}" will be ${next ? "active — evaluated normally" : "inactive — returns default for all requests"}.`,
      variant: next ? "info" : "warning",
      confirmLabel: next ? "Activate" : "Deactivate",
      onConfirm: async () => {
        try {
          await updateFlag.mutateAsync({ id: flag.id, body: { is_active: next } });
          toast(`Flag "${flag.flag_key}" ${next ? "activated" : "deactivated"}`, "success");
        } catch (e) {
          toast(e instanceof Error ? e.message : "Failed", "error");
        }
      },
    });
  }

  function handleDelete(flag: FlagType) {
    setConfirmAction({
      title: "Delete flag?",
      body: `"${flag.flag_key}" will be permanently deleted. This cannot be undone.`,
      variant: "danger",
      confirmLabel: "Delete",
      onConfirm: async () => {
        try {
          await deleteFlag.mutateAsync(flag.id);
          toast(`Flag "${flag.flag_key}" deleted`, "success");
        } catch (e) {
          toast(e instanceof Error ? e.message : "Failed", "error");
        }
      },
    });
  }

  const statCards: StatCard[] = [
    { label: "Total",       value: stats.total,       icon: Flag,     borderCls: "border-l-zinc-900 dark:border-l-zinc-100",   numCls: "text-zinc-900 dark:text-zinc-50",             testId: "stat-card-total"       },
    { label: "Global",      value: stats.global,      icon: Globe,    borderCls: "border-l-amber-500",                         numCls: "text-amber-600 dark:text-amber-400",           testId: "stat-card-global"      },
    { label: "Org",         value: stats.org,         icon: Building2,borderCls: "border-l-blue-500",                          numCls: "text-blue-600 dark:text-blue-400",             testId: "stat-card-org"         },
    { label: "Application", value: stats.application, icon: Package,  borderCls: "border-l-purple-500",                        numCls: "text-purple-600 dark:text-purple-400",         testId: "stat-card-application" },
    { label: "Active",      value: stats.active,      icon: Zap,      borderCls: "border-l-emerald-500",                       numCls: "text-emerald-600 dark:text-emerald-400",       testId: "stat-card-active"      },
    { label: "Inactive",    value: stats.inactive,    icon: Flag,     borderCls: "border-l-zinc-400",                          numCls: "text-zinc-500 dark:text-zinc-400",             testId: "stat-card-inactive"    },
  ];

  return (
    <>
      {confirmAction && (
        <ConfirmDialog action={confirmAction} onClose={() => setConfirmAction(null)} />
      )}

      <PageHeader
        title="Feature Flags"
        description="Control features across scopes. Click any status badge to toggle inline."
        testId="heading-flags"
        actions={
          <>
            <Link
              href="/feature-flags/evaluate"
              className="inline-flex h-10 items-center rounded-lg border border-zinc-200 bg-white px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:hover:bg-zinc-800"
              data-testid="link-evaluate"
            >
              Try evaluator &rarr;
            </Link>
            <Button onClick={() => setOpenCreate(true)} data-testid="open-create-flag">
              + New flag
            </Button>
          </>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {/* Stat cards */}
        {!isLoading && !isError && <StatCards cards={statCards} />}

        {/* Filter bar */}
        {!isLoading && !isError && (
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
            {/* Scope pills */}
            {(["all", "global", "org", "application"] as const).map((s) => {
              const active = scopeFilter === s;
              const count = s === "all" ? stats.total : stats[s];
              const meta = s !== "all" ? SCOPE_META[s] : null;
              const SIcon = meta?.icon;
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setScopeFilter(s)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
                    active
                      ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50"
                  )}
                  data-testid={`filter-flag-scope-${s}`}
                >
                  {SIcon && <SIcon className="h-3 w-3" />}
                  {s === "all" ? "All scopes" : meta!.label}
                  <span className={cn("tabular-nums", active ? "opacity-70" : "text-zinc-400")}>
                    {count}
                  </span>
                </button>
              );
            })}

            <span className="h-5 w-px bg-zinc-200 dark:bg-zinc-700" />

            {/* Status pills */}
            {(["all", "active", "inactive"] as const).map((s) => {
              const active = statusFilter === s;
              const count = s === "all" ? stats.total : stats[s];
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatusFilter(s)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
                    active
                      ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50"
                  )}
                  data-testid={`filter-flag-status-${s}`}
                >
                  {s === "active" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
                  {s === "inactive" && <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />}
                  {s === "all" ? "All statuses" : s}
                  <span className={cn("tabular-nums", active ? "opacity-70" : "text-zinc-400")}>
                    {count}
                  </span>
                </button>
              );
            })}

            {/* Active filter chips */}
            {scopeFilter !== "all" && (
              <button
                type="button"
                onClick={() => setScopeFilter("all")}
                className="inline-flex items-center gap-1 rounded-full border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                scope: {scopeFilter}
                <X className="h-2.5 w-2.5 ml-0.5" />
              </button>
            )}
            {statusFilter !== "all" && (
              <button
                type="button"
                onClick={() => setStatusFilter("all")}
                className="inline-flex items-center gap-1 rounded-full border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                status: {statusFilter}
                <X className="h-2.5 w-2.5 ml-0.5" />
              </button>
            )}

            {/* Search */}
            <div className="relative ml-auto w-56">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search flags…"
                className="h-7 w-full rounded-lg border border-zinc-200 bg-white pl-7 pr-2 text-xs text-zinc-900 transition focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
                data-testid="filter-flag-search"
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

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load flags"}
            retry={() => refetch()}
          />
        )}

        {/* Grouped flag list */}
        {data && filtered.length > 0 && (
          <div className="space-y-1">
            {grouped.map(({ scope, flags }) => (
              <ScopeSection
                key={scope}
                scope={scope}
                flags={flags}
                onToggleActive={handleToggleActive}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Empty state: no flags at all */}
        {data && allFlags.length === 0 && (
          <EmptyState
            title="No flags yet"
            description="Create your first flag. Pick a scope, value type, and a default. Per-environment toggles come next."
            action={
              <Button onClick={() => setOpenCreate(true)}>
                + Create first flag
              </Button>
            }
          />
        )}

        {/* Empty state: filters produced nothing */}
        {data && allFlags.length > 0 && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
            <Flag className="h-8 w-8 text-zinc-400" />
            <p className="text-sm text-zinc-500 dark:text-zinc-400">No flags match your filters.</p>
            <button
              type="button"
              onClick={() => { setScopeFilter("all"); setStatusFilter("all"); setSearch(""); }}
              className="text-xs font-medium text-zinc-600 underline underline-offset-2 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {openCreate && (
        <CreateFlagDialog open={openCreate} onClose={() => setOpenCreate(false)} />
      )}
    </>
  );
}
