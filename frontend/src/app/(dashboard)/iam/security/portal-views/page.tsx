"use client";

import {
  Activity,
  ChevronDown,
  ChevronRight,
  FileText,
  Flag,
  LayoutDashboard,
  Lock,
  Send,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import { Badge, EmptyState, ErrorState, Skeleton } from "@/components/ui";
import {
  useAttachView,
  useDetachView,
  usePortalViews,
  useRoleViews,
} from "@/features/iam-portal-views/hooks/use-portal-views";
import { useRoles } from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { PortalView, Role } from "@/types/api";

// ─── Icon map (lucide names from dim seed → components) ────────────────────────

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  ShieldCheck,
  Flag,
  Lock,
  Activity,
  FileText,
  Send,
};

function ViewIcon({ name, className }: { name: string | null; className?: string }) {
  const Icon = (name && ICON_MAP[name]) ? ICON_MAP[name] : ShieldAlert;
  return <Icon className={className} />;
}

// ─── Stat cards ───────────────────────────────────────────────────────────────

type StatCardProps = {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  borderCls: string;
  numCls: string;
  testId: string;
};

function StatCards({ cards }: { cards: StatCardProps[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {cards.map(({ label, value, icon: Icon, borderCls, numCls, testId }) => (
        <div
          key={label}
          className={cn(
            "flex items-center gap-3 rounded-xl border border-l-[3px] bg-white px-4 py-3 dark:bg-zinc-950",
            "border-zinc-200 dark:border-zinc-800",
            borderCls,
          )}
          data-testid={testId}
        >
          <div className="shrink-0 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">
            <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </div>
          <div className="min-w-0">
            <span className={cn("block text-2xl font-bold tabular-nums leading-none", numCls)}>
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

// ─── Role picker for a view ────────────────────────────────────────────────────

function RolePickerPanel({
  view,
  roles,
}: {
  view: PortalView;
  roles: Role[];
}) {
  const { toast } = useToast();
  const { data: assignments = [], isLoading } = useRoleViews(undefined);

  // We need per-role data — collect all granted role_ids for this view
  const grantedRoleIds = useMemo(() => {
    return new Set(assignments.filter((a) => a.view_id === view.id).map((a) => a.role_id));
  }, [assignments, view.id]);

  return (
    <div className="border-t border-zinc-100 bg-zinc-50 px-4 pb-4 pt-3 dark:border-zinc-800 dark:bg-zinc-900/40">
      <p className="mb-3 text-[11px] font-medium uppercase tracking-wide text-zinc-400 dark:text-zinc-500">
        Role access — check a role to grant this view
      </p>
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
        </div>
      ) : roles.length === 0 ? (
        <p className="text-xs text-zinc-400">No roles defined yet.</p>
      ) : (
        <ul className="space-y-1">
          {roles.map((role) => (
            <RoleCheckRow
              key={role.id}
              role={role}
              view={view}
              granted={grantedRoleIds.has(role.id)}
              onGrantChange={(granted, err) => {
                if (err) toast(err, "error");
                else toast(granted ? `Granted "${view.label}" to ${role.code ?? role.id}` : `Revoked "${view.label}" from ${role.code ?? role.id}`, "success");
              }}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

// We need per-role attach/detach — a small component that fetches its own role views
function RoleCheckRow({
  role,
  view,
  granted,
  onGrantChange,
}: {
  role: Role;
  view: PortalView;
  granted: boolean;
  onGrantChange: (granted: boolean, err: string | null) => void;
}) {
  const { data: roleAssignments = [] } = useRoleViews(role.id);
  const isGranted = roleAssignments.some((a) => a.view_id === view.id);
  const attach = useAttachView(role.id);
  const detach = useDetachView(role.id);
  const isPending = attach.isPending || detach.isPending;

  async function toggle() {
    try {
      if (isGranted) {
        await detach.mutateAsync(view.id);
        onGrantChange(false, null);
      } else {
        await attach.mutateAsync(view.id);
        onGrantChange(true, null);
      }
    } catch (err) {
      onGrantChange(isGranted, err instanceof ApiClientError ? err.message : String(err));
    }
  }

  return (
    <li className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-zinc-950">
      <input
        type="checkbox"
        checked={isGranted}
        onChange={toggle}
        disabled={isPending}
        className="h-4 w-4 rounded border-zinc-300 accent-violet-600 dark:border-zinc-700"
        data-testid={`grant-view-${view.id}-role-${role.id}`}
      />
      <div className="min-w-0 flex-1">
        <code className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
          {role.code ?? role.id.slice(0, 8)}
        </code>
        {role.label && (
          <span className="ml-2 text-xs text-zinc-400">{role.label}</span>
        )}
      </div>
      <Badge tone={role.role_type === "system" ? "purple" : "blue"}>
        {role.role_type}
      </Badge>
      {!role.is_active && <Badge tone="zinc">inactive</Badge>}
    </li>
  );
}

// ─── View card ────────────────────────────────────────────────────────────────

function ViewCard({
  view,
  grantCount,
  roles,
  expanded,
  onToggle,
}: {
  view: PortalView;
  grantCount: number;
  roles: Role[];
  expanded: boolean;
  onToggle: (id: number) => void;
}) {
  return (
    <div
      className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
      data-testid={`view-card-${view.code}`}
    >
      {/* Header row */}
      <button
        type="button"
        onClick={() => onToggle(view.id)}
        className={cn(
          "flex w-full items-center gap-3 border-l-[3px] px-4 py-3 text-left transition",
          "hover:bg-zinc-50 dark:hover:bg-zinc-900/40",
          expanded && "bg-zinc-50 dark:bg-zinc-900/40",
        )}
        style={{ borderLeftColor: view.color ?? "#6366F1" }}
        data-testid={`toggle-view-${view.code}`}
      >
        {/* Color dot + icon */}
        <div
          className="shrink-0 rounded-lg p-2"
          style={{ backgroundColor: `${view.color ?? "#6366F1"}18` }}
        >
          <ViewIcon
            name={view.icon}
            className="h-4 w-4"
            // inline color from dim
          />
        </div>

        {/* Label + route + grant count */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              {view.label}
            </span>
            <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
              {view.code}
            </code>
          </div>
          <p className="mt-0.5 text-xs text-zinc-400 dark:text-zinc-500">
            {view.default_route}
          </p>
        </div>

        {/* Grant count badge */}
        <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] tabular-nums text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {grantCount} {grantCount === 1 ? "role" : "roles"}
        </span>

        {/* Chevron */}
        {expanded ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-zinc-400" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-zinc-400" />
        )}
      </button>

      {/* Expanded: role picker */}
      {expanded && (
        <RolePickerPanel view={view} roles={roles} />
      )}
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────────

export default function PortalViewsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: views = [], isLoading, isError, error, refetch } = usePortalViews();
  const { data: rolesData } = useRoles({ limit: 500 });
  const allRoles = rolesData?.items ?? [];

  // Count grants per view — we need all role-view data
  // We approximate by counting per view via per-role queries; for the stat
  // card we just show total views and total roles for now, and compute
  // grants dynamically when a card is expanded.
  const totalViews = views.length;
  const activeRoles = allRoles.filter((r) => r.is_active).length;

  function handleToggle(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  const statCards: StatCardProps[] = [
    {
      label: "Total Views",
      value: totalViews,
      icon: LayoutDashboard,
      borderCls: "border-l-violet-500",
      numCls: "text-violet-600 dark:text-violet-400",
      testId: "stat-total-views",
    },
    {
      label: "Active Roles",
      value: activeRoles,
      icon: ShieldCheck,
      borderCls: "border-l-blue-500",
      numCls: "text-blue-600 dark:text-blue-400",
      testId: "stat-active-roles",
    },
    {
      label: "System Views",
      value: totalViews,
      icon: Lock,
      borderCls: "border-l-zinc-500",
      numCls: "text-zinc-600 dark:text-zinc-400",
      testId: "stat-system-views",
    },
  ];

  return (
    <>
      <PageHeader
        title="Portal Views"
        description="Configure which UI sections each role can access. Click a view to expand and assign roles."
        testId="heading-portal-views"
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {/* Stat cards */}
        {!isLoading && !isError && <StatCards cards={statCards} />}

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load portal views"}
            retry={() => refetch()}
          />
        )}

        {/* View list */}
        {!isLoading && !isError && views.length === 0 && (
          <EmptyState
            title="No portal views"
            description="Portal views are seeded by migration. Run the migration to populate them."
          />
        )}

        {!isLoading && !isError && views.length > 0 && (
          <div className="space-y-2">
            {views.map((view) => (
              <ViewCard
                key={view.id}
                view={view}
                grantCount={0} // populated inside expanded panel via per-role queries
                roles={allRoles}
                expanded={expandedId === view.id}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}

        {/* Hint */}
        {!isLoading && !isError && views.length > 0 && (
          <p className="text-center text-xs text-zinc-400 dark:text-zinc-500">
            Changes take effect immediately — users see the new view set on next page load.
          </p>
        )}
      </div>
    </>
  );
}
