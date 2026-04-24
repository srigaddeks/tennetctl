"use client";

import Link from "next/link";
import { Suspense, useMemo, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
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

const SCOPE_META: Record<FlagScope, { label: string; icon: typeof Globe; accentColor: string; badgeTone: "amber" | "blue" | "purple" }> = {
  global:      { label: "Global",      icon: Globe,     accentColor: "var(--warning)",  badgeTone: "amber"  },
  org:         { label: "Org",         icon: Building2, accentColor: "var(--accent)",   badgeTone: "blue"   },
  application: { label: "Application", icon: Package,   accentColor: "#a855f7",         badgeTone: "purple" },
};

const VALUE_TYPE_COLORS: Record<string, string> = {
  boolean: "emerald",
  string:  "blue",
  number:  "amber",
  json:    "purple",
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
    info:    { icon: Info,          iconColor: "var(--info)",    bg: "var(--info-muted)",    border: "var(--info)"    },
    warning: { icon: AlertTriangle, iconColor: "var(--warning)", bg: "var(--warning-muted)", border: "var(--warning)" },
    danger:  { icon: AlertTriangle, iconColor: "var(--danger)",  bg: "var(--danger-muted)",  border: "var(--danger)"  },
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
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(6,11,23,0.85)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      data-testid="confirm-dialog"
    >
      <div
        className="mx-4 w-full max-w-md rounded-2xl"
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-bright)",
          boxShadow: "0 25px 50px rgba(0,0,0,0.6)",
        }}
      >
        <div className="flex items-start gap-3 p-6 pb-4">
          <div
            className="shrink-0 rounded-xl p-2"
            style={{ background: colors.bg, border: `1px solid ${colors.border}` }}
          >
            <IconComp className="h-5 w-5" style={{ color: colors.iconColor }} />
          </div>
          <div>
            <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>{action.title}</h2>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>{action.body}</p>
          </div>
        </div>
        <div
          className="flex justify-end gap-2 px-6 py-4"
          style={{ borderTop: "1px solid var(--border)" }}
        >
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
  options: { value: T; label: string; active: boolean }[];
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
            className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition"
            style={o.active ? {
              background: "var(--success-muted)",
              border: "1px solid var(--success)",
              color: "var(--success)",
            } : {
              background: "var(--bg-elevated)",
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
            }}
          >
            {o.active && <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--success)" }} />}
            {o.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setOpen(false)}
          style={{ color: "var(--text-muted)" }}
          className="hover:opacity-80 transition"
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
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition hover:opacity-90"
      style={cur.active ? {
        background: "var(--success-muted)",
        border: "1px solid var(--success)",
        color: "var(--success)",
        cursor: disabled ? "default" : "pointer",
      } : {
        background: "var(--bg-elevated)",
        border: "1px solid var(--border)",
        color: "var(--text-muted)",
        cursor: disabled ? "default" : "pointer",
      }}
    >
      {cur.active && <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--success)" }} />}
      {cur.label}
    </button>
  );
}

// ─── Stat cards ──────────────────────────────────────────────────────────────

type StatCardData = {
  label: string;
  value: number;
  icon: typeof Flag;
  accentColor: string;
  testId: string;
};

function StatCards({ cards }: { cards: StatCardData[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map(({ label, value, icon: Icon, accentColor, testId }) => (
        <div
          key={label}
          className="flex items-center gap-3 rounded-xl px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderLeft: `3px solid ${accentColor}`,
          }}
          data-testid={testId}
        >
          <div
            className="shrink-0 rounded-lg p-2"
            style={{ background: "var(--bg-elevated)" }}
          >
            <Icon className="h-4 w-4" style={{ color: accentColor }} />
          </div>
          <div className="min-w-0">
            <span
              className="block text-2xl font-bold tabular-nums leading-none font-mono-data"
              style={{ color: accentColor }}
            >
              {value}
            </span>
            <span
              className="mt-0.5 block truncate text-[11px] label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Scope filter banner ──────────────────────────────────────────────────────

function ScopeFilterBanner({
  orgId,
  appId,
  onClear,
}: {
  orgId: string;
  appId: string | null;
  onClear: () => void;
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl px-4 py-3"
      style={{
        background: "var(--accent-muted)",
        border: "1px solid var(--accent-dim)",
      }}
      data-testid="scope-filter-banner"
    >
      <Building2 className="h-4 w-4 shrink-0" style={{ color: "var(--accent)" }} />
      <div className="flex-1 min-w-0 text-xs" style={{ color: "var(--text-secondary)" }}>
        <span className="font-medium" style={{ color: "var(--accent)" }}>Scope filter active. </span>
        Showing flags for org:{" "}
        <code
          className="rounded px-1.5 py-0.5 text-[11px]"
          style={{
            background: "var(--bg-elevated)",
            color: "var(--text-primary)",
            fontFamily: "var(--font-mono)",
          }}
        >
          {orgId}
        </code>
        {appId && (
          <>
            {" "}· application:{" "}
            <code
              className="rounded px-1.5 py-0.5 text-[11px]"
              style={{
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
              }}
            >
              {appId}
            </code>
          </>
        )}
      </div>
      <button
        type="button"
        onClick={onClear}
        className="shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-bright)",
          color: "var(--text-secondary)",
        }}
        data-testid="clear-scope-filter"
      >
        <X className="h-3 w-3" />
        Clear scope filter
      </button>
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

  return (
    <div
      className={cn(
        "grid grid-cols-[auto_1fr_auto] items-start gap-x-3 px-4 py-3 last:border-b-0 transition animate-fade-in",
        !flag.is_active && "opacity-50"
      )}
      style={{
        borderBottom: "1px solid var(--border)",
        borderLeft: `3px solid ${scopeMeta.accentColor}`,
      }}
    >
      {/* Scope icon */}
      <div
        className="row-span-2 mt-0.5 shrink-0 rounded-lg p-1.5"
        style={{ background: "var(--bg-elevated)" }}
        title={`${scopeMeta.label} scope`}
      >
        <scopeMeta.icon className="h-3.5 w-3.5" style={{ color: scopeMeta.accentColor }} />
      </div>

      {/* Flag key + description */}
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Link
            href={`/feature-flags/${flag.id}`}
            className="font-mono text-xs font-semibold transition hover:opacity-80"
            style={{ color: "var(--accent)", fontFamily: "var(--font-mono)" }}
            data-testid={`test-flag-key-${flag.flag_key}`}
          >
            {flag.flag_key}
          </Link>
          <Badge tone={(VALUE_TYPE_COLORS[flag.value_type] ?? "default") as "emerald" | "blue" | "amber" | "purple"}>
            {flag.value_type}
          </Badge>
        </div>
        {flag.description && (
          <p
            className="mt-0.5 max-w-lg truncate text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            {flag.description}
          </p>
        )}
      </div>

      {/* Actions: status + delete */}
      <div className="flex items-center gap-1.5 shrink-0">
        <InlinePicker
          current={flag.is_active ? "active" : "inactive"}
          options={[
            { value: "active",   label: "enabled",  active: true  },
            { value: "inactive", label: "disabled", active: false },
          ]}
          onPick={() => onToggleActive(flag)}
        />
        <span className="h-3.5 w-px" style={{ background: "var(--border)" }} />
        <code
          className="rounded px-1.5 py-0.5 text-[10px]"
          style={{
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            fontFamily: "var(--font-mono)",
          }}
        >
          {JSON.stringify(flag.default_value)}
        </code>
        <span className="h-3.5 w-px" style={{ background: "var(--border)" }} />
        <button
          type="button"
          onClick={() => onDelete(flag)}
          title="Delete flag"
          className="rounded-md p-1 transition"
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--danger)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          data-testid={`delete-flag-${flag.flag_key}`}
        >
          <X className="h-3.5 w-3.5" />
        </button>
        {flag.scope === "application" && flag.application_id && (
          <Link
            href={`/iam/applications/${flag.application_id}`}
            className="rounded-md px-2 py-1 text-[10px] font-medium transition"
            style={{ color: "#a855f7" }}
            title="Open this flag's application hub"
            data-testid={`flag-app-hub-${flag.flag_key}`}
          >
            App ↗
          </Link>
        )}
        <Link
          href={`/feature-flags/${flag.id}`}
          className="rounded-md px-2 py-1 text-xs font-medium transition"
          style={{ color: "var(--text-secondary)" }}
        >
          Manage →
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
  const activeCount = flags.filter((f) => f.is_active).length;

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition"
        style={{ color: "var(--text-primary)" }}
        data-testid={`group-header-${scope}`}
      >
        {open
          ? <FolderOpen className="h-4 w-4 shrink-0" style={{ color: "var(--text-secondary)" }} />
          : <Folder className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} />}
        <meta.icon className="h-3.5 w-3.5 shrink-0" style={{ color: meta.accentColor }} />
        <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          {meta.label}
        </span>
        <span
          className="ml-auto text-xs tabular-nums"
          style={{ color: "var(--text-muted)" }}
        >
          {flags.length}
        </span>
        <span
          className="text-[11px] font-medium tabular-nums"
          style={{ color: meta.accentColor }}
        >
          {activeCount} active
        </span>
        {open
          ? <ChevronDown className="h-3.5 w-3.5" style={{ color: "var(--text-muted)" }} />
          : <ChevronRight className="h-3.5 w-3.5" style={{ color: "var(--text-muted)" }} />}
      </button>

      {open && (
        <div
          className="mb-3 ml-4 overflow-hidden rounded-xl"
          style={{
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
          }}
        >
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

// ─── Inner page (needs useSearchParams) ──────────────────────────────────────

function FlagsListInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlOrgId = searchParams.get("org_id");
  const urlAppId = searchParams.get("application_id");

  const [scopeFilter, setScopeFilter] = useState<"all" | FlagScope>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [search, setSearch] = useState("");
  const [openCreate, setOpenCreate] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);

  const { data, isLoading, isError, error, refetch } = useFlags({
    limit: 500,
    org_id: urlOrgId ?? undefined,
    application_id: urlAppId ?? undefined,
  });
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
      title: `${next ? "Enable" : "Disable"} flag?`,
      body: `"${flag.flag_key}" will be ${next ? "enabled — evaluated normally across all environments" : "disabled — default value returned for all requests"}.`,
      variant: next ? "info" : "warning",
      confirmLabel: next ? "Enable" : "Disable",
      onConfirm: async () => {
        try {
          await updateFlag.mutateAsync({ id: flag.id, body: { is_active: next } });
          toast(`Flag "${flag.flag_key}" ${next ? "enabled" : "disabled"}`, "success");
        } catch (e) {
          toast(e instanceof Error ? e.message : "Failed", "error");
        }
      },
    });
  }

  function handleDelete(flag: FlagType) {
    setConfirmAction({
      title: "Delete flag?",
      body: `"${flag.flag_key}" will be permanently deleted. All environment states, rules, and overrides will be removed. This cannot be undone.`,
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

  function clearScopeFilter() {
    const url = new URL(window.location.href);
    url.searchParams.delete("org_id");
    url.searchParams.delete("application_id");
    router.replace(url.pathname + (url.searchParams.toString() ? `?${url.searchParams}` : ""));
  }

  const statCards: StatCardData[] = [
    { label: "Total Flags",   value: stats.total,       icon: Flag,      accentColor: "var(--text-secondary)", testId: "stat-card-total"       },
    { label: "Global",        value: stats.global,      icon: Globe,     accentColor: "var(--warning)",        testId: "stat-card-global"      },
    { label: "Org",           value: stats.org,         icon: Building2, accentColor: "var(--accent)",         testId: "stat-card-org"         },
    { label: "Application",   value: stats.application, icon: Package,   accentColor: "#a855f7",               testId: "stat-card-application" },
    { label: "Enabled",       value: stats.active,      icon: Zap,       accentColor: "var(--success)",        testId: "stat-card-active"      },
    { label: "Disabled",      value: stats.inactive,    icon: Flag,      accentColor: "var(--text-muted)",     testId: "stat-card-inactive"    },
  ];

  return (
    <>
      {confirmAction && (
        <ConfirmDialog action={confirmAction} onClose={() => setConfirmAction(null)} />
      )}

      <PageHeader
        title="Feature Flags"
        description="Control feature exposure across environments and scopes. Toggle, rule, and override production traffic without deployments."
        testId="heading-flags"
        actions={
          <>
            <Link
              href="/feature-flags/evaluate"
              className="inline-flex h-10 items-center rounded-lg border px-4 text-sm font-medium transition"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-bright)",
                color: "var(--text-secondary)",
              }}
              data-testid="link-evaluate"
            >
              Evaluate sandbox →
            </Link>
            <Button variant="primary" onClick={() => setOpenCreate(true)} data-testid="open-create-flag">
              + New flag
            </Button>
          </>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {/* Scope filter banner */}
        {urlOrgId && (
          <ScopeFilterBanner
            orgId={urlOrgId}
            appId={urlAppId}
            onClear={clearScopeFilter}
          />
        )}

        {/* Stat cards */}
        {!isLoading && !isError && <StatCards cards={statCards} />}

        {/* Filter bar */}
        {!isLoading && !isError && (
          <div
            className="flex flex-wrap items-center gap-2 rounded-xl px-4 py-3"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
            }}
          >
            {/* Scope pills */}
            {(["all", "global", "org", "application"] as const).map((s) => {
              const active = scopeFilter === s;
              const count = s === "all" ? stats.total : stats[s];
              const meta = s !== "all" ? SCOPE_META[s] : null;
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setScopeFilter(s)}
                  className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition"
                  style={active ? {
                    background: "var(--accent-dim)",
                    border: "1px solid var(--accent)",
                    color: "var(--accent)",
                  } : {
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border)",
                    color: "var(--text-secondary)",
                  }}
                  data-testid={`filter-flag-scope-${s}`}
                >
                  {meta && <meta.icon className="h-3 w-3" />}
                  {s === "all" ? "All scopes" : meta!.label}
                  <span className="tabular-nums opacity-70">{count}</span>
                </button>
              );
            })}

            <span className="h-5 w-px" style={{ background: "var(--border)" }} />

            {/* Status pills */}
            {(["all", "active", "inactive"] as const).map((s) => {
              const active = statusFilter === s;
              const count = s === "all" ? stats.total : stats[s];
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatusFilter(s)}
                  className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition"
                  style={active ? {
                    background: s === "active" ? "var(--success-muted)" : "var(--bg-elevated)",
                    border: `1px solid ${s === "active" ? "var(--success)" : "var(--accent)"}`,
                    color: s === "active" ? "var(--success)" : "var(--accent)",
                  } : {
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border)",
                    color: "var(--text-secondary)",
                  }}
                  data-testid={`filter-flag-status-${s}`}
                >
                  {s === "active" && (
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: "var(--success)" }}
                    />
                  )}
                  {s === "inactive" && (
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ background: "var(--text-muted)" }}
                    />
                  )}
                  {s === "all" ? "All statuses" : s}
                  <span className="tabular-nums opacity-70">{count}</span>
                </button>
              );
            })}

            {/* Active filter chips */}
            {scopeFilter !== "all" && (
              <button
                type="button"
                onClick={() => setScopeFilter("all")}
                className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium transition"
                style={{
                  background: "var(--accent-muted)",
                  border: "1px solid var(--accent-dim)",
                  color: "var(--accent)",
                }}
              >
                scope: {scopeFilter}
                <X className="h-2.5 w-2.5 ml-0.5" />
              </button>
            )}
            {statusFilter !== "all" && (
              <button
                type="button"
                onClick={() => setStatusFilter("all")}
                className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium transition"
                style={{
                  background: "var(--accent-muted)",
                  border: "1px solid var(--accent-dim)",
                  color: "var(--accent)",
                }}
              >
                status: {statusFilter}
                <X className="h-2.5 w-2.5 ml-0.5" />
              </button>
            )}

            {/* Search */}
            <div className="relative ml-auto w-56">
              <Search
                className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
                style={{ color: "var(--text-muted)" }}
              />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search flags…"
                className="h-8 w-full rounded-lg border pl-7 pr-2 text-xs transition focus:outline-none"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                }}
                data-testid="filter-flag-search"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 transition"
                  style={{ color: "var(--text-muted)" }}
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
            title="No feature flags yet"
            description="Create your first flag to start controlling feature exposure. Pick a scope, value type, and a default — environment toggles and rollout rules come next."
            action={
              <Button variant="primary" onClick={() => setOpenCreate(true)}>
                + Create first flag
              </Button>
            }
          />
        )}

        {/* Empty state: filters produced nothing */}
        {data && allFlags.length > 0 && filtered.length === 0 && (
          <div
            className="flex flex-col items-center justify-center gap-2 rounded-xl px-6 py-12 text-center"
            style={{
              border: "1px dashed var(--border-bright)",
              background: "var(--bg-surface)",
            }}
          >
            <Flag className="h-8 w-8" style={{ color: "var(--text-muted)" }} />
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              No flags match your current filters.
            </p>
            <button
              type="button"
              onClick={() => { setScopeFilter("all"); setStatusFilter("all"); setSearch(""); }}
              className="text-xs font-medium transition"
              style={{ color: "var(--accent)" }}
            >
              Clear all filters
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

// ─── Page export with Suspense boundary ──────────────────────────────────────

export default function FlagsListPage() {
  return (
    <Suspense fallback={
      <div
        className="flex items-center justify-center p-8"
        style={{ color: "var(--text-muted)" }}
      >
        Loading flags…
      </div>
    }>
      <FlagsListInner />
    </Suspense>
  );
}
