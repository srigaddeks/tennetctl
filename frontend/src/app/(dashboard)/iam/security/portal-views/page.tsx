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
import { Badge, EmptyState, ErrorState, Skeleton, StatCard } from "@/components/ui";
import {
  useAttachView,
  useDetachView,
  usePortalViews,
  useRoleViews,
} from "@/features/iam-portal-views/hooks/use-portal-views";
import { useRoles } from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import type { PortalView, Role } from "@/types/api";

// ─── Icon map ───────────────────────────────────────────────────────────────

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

// ─── Role picker panel ───────────────────────────────────────────────────────

function RolePickerPanel({ view, roles }: { view: PortalView; roles: Role[] }) {
  const { toast } = useToast();
  const { data: assignments = [], isLoading } = useRoleViews(undefined);

  const grantedRoleIds = useMemo(() => {
    return new Set(assignments.filter((a) => a.view_id === view.id).map((a) => a.role_id));
  }, [assignments, view.id]);

  return (
    <div
      className="border-t px-4 pb-4 pt-3"
      style={{
        background: "var(--bg-base)",
        borderColor: "var(--border)",
      }}
    >
      <p
        className="label-caps mb-3 text-[11px]"
        style={{ color: "var(--text-muted)" }}
      >
        Role access — check to grant this view
      </p>
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
        </div>
      ) : roles.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No roles defined yet.
        </p>
      ) : (
        <ul className="space-y-1.5">
          {roles.map((role) => (
            <RoleCheckRow
              key={role.id}
              role={role}
              view={view}
              granted={grantedRoleIds.has(role.id)}
              onGrantChange={(granted, err) => {
                if (err) toast(err, "error");
                else
                  toast(
                    granted
                      ? `Granted "${view.label}" to ${role.code ?? role.id}`
                      : `Revoked "${view.label}" from ${role.code ?? role.id}`,
                    "success",
                  );
              }}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

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
  const attach = useAttachView(role.id);
  const detach = useDetachView(role.id);
  const isPending = attach.isPending || detach.isPending;

  async function toggle() {
    try {
      if (granted) {
        await detach.mutateAsync(view.id);
        onGrantChange(false, null);
      } else {
        await attach.mutateAsync(view.id);
        onGrantChange(true, null);
      }
    } catch (err) {
      onGrantChange(
        granted,
        err instanceof ApiClientError ? err.message : String(err),
      );
    }
  }

  return (
    <li
      className="flex items-center gap-3 rounded border px-3 py-2 transition-colors"
      style={{
        background: granted ? "var(--accent-muted)" : "var(--bg-surface)",
        borderColor: granted ? "var(--accent)" : "var(--border)",
      }}
    >
      <input
        type="checkbox"
        checked={granted}
        onChange={toggle}
        disabled={isPending}
        className="h-4 w-4 rounded"
        style={{ accentColor: "var(--accent)" }}
        data-testid={`grant-view-${view.id}-role-${role.id}`}
      />
      <div className="min-w-0 flex-1">
        <code
          className="font-mono-data text-xs font-semibold"
          style={{ color: granted ? "var(--accent)" : "var(--text-primary)" }}
        >
          {role.code ?? role.id.slice(0, 8)}
        </code>
        {role.label && (
          <span
            className="ml-2 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            {role.label}
          </span>
        )}
      </div>
      <Badge tone={role.role_type === "system" ? "purple" : "blue"}>
        {role.role_type}
      </Badge>
      {!role.is_active && <Badge tone="default">inactive</Badge>}
    </li>
  );
}

// ─── View card ───────────────────────────────────────────────────────────────

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
  const accentColor = view.color ?? "#6366F1";

  return (
    <div
      className="overflow-hidden rounded border"
      style={{
        background: "var(--bg-surface)",
        borderColor: expanded ? accentColor : "var(--border)",
        transition: "border-color 0.15s",
      }}
      data-testid={`view-card-${view.code}`}
    >
      {/* Header row */}
      <button
        type="button"
        onClick={() => onToggle(view.id)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
        style={{
          borderLeft: `3px solid ${accentColor}`,
          background: expanded ? "var(--bg-elevated)" : "transparent",
        }}
        data-testid={`toggle-view-${view.code}`}
      >
        {/* Icon */}
        <div
          className="shrink-0 rounded p-2"
          style={{ backgroundColor: `${accentColor}20` }}
        >
          <ViewIcon
            name={view.icon}
            className="h-4 w-4"
            // @ts-expect-error - dynamic color from view
            style={{ color: accentColor }}
          />
        </div>

        {/* Label + route */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="text-sm font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              {view.label}
            </span>
            <code
              className="font-mono-data rounded px-1.5 py-0.5 text-[10px]"
              style={{
                background: "var(--bg-base)",
                color: "var(--text-muted)",
              }}
            >
              {view.code}
            </code>
          </div>
          <p
            className="mt-0.5 font-mono-data text-[11px]"
            style={{ color: "var(--text-muted)" }}
          >
            {view.default_route}
          </p>
        </div>

        {/* Grant count */}
        <span
          className="label-caps shrink-0 rounded-full px-2.5 py-0.5 text-[11px] tabular-nums"
          style={{
            background: grantCount > 0 ? "var(--accent-muted)" : "var(--bg-base)",
            color: grantCount > 0 ? "var(--accent)" : "var(--text-muted)",
            border: `1px solid ${grantCount > 0 ? "var(--accent)" : "var(--border)"}`,
          }}
        >
          {grantCount} {grantCount === 1 ? "role" : "roles"}
        </span>

        {/* Chevron */}
        {expanded ? (
          <ChevronDown
            className="h-4 w-4 shrink-0"
            style={{ color: "var(--text-secondary)" }}
          />
        ) : (
          <ChevronRight
            className="h-4 w-4 shrink-0"
            style={{ color: "var(--text-muted)" }}
          />
        )}
      </button>

      {/* Expanded: role picker */}
      {expanded && <RolePickerPanel view={view} roles={roles} />}
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function PortalViewsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: views = [], isLoading, isError, error, refetch } = usePortalViews();
  const { data: rolesData } = useRoles({ limit: 500 });
  const { data: allAssignments = [] } = useRoleViews(undefined);
  const allRoles = rolesData?.items ?? [];

  const grantsByView = useMemo(() => {
    const m = new Map<number, number>();
    for (const a of allAssignments) {
      m.set(a.view_id, (m.get(a.view_id) ?? 0) + 1);
    }
    return m;
  }, [allAssignments]);

  const totalViews = views.length;
  const activeRoles = allRoles.filter((r) => r.is_active).length;
  const configuredViews = views.filter((v) => (grantsByView.get(v.id) ?? 0) > 0).length;

  function handleToggle(id: number) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  return (
    <>
      <PageHeader
        title="Portal Views"
        description="Configure which UI sections each role can access. Click a view to expand and assign roles."
        testId="heading-portal-views"
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in space-y-5">
        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="grid grid-cols-3 gap-3">
            <StatCard
              label="Total Views"
              value={totalViews}
              accent="blue"
            />
            <StatCard
              label="Active Roles"
              value={activeRoles}
              accent="green"
            />
            <StatCard
              label="Configured"
              value={configuredViews}
              accent="blue"
            />
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded" />
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

        {/* Empty */}
        {!isLoading && !isError && views.length === 0 && (
          <EmptyState
            title="No portal views"
            description="Portal views are seeded by migration. Run the migration to populate them."
          />
        )}

        {/* View list */}
        {!isLoading && !isError && views.length > 0 && (
          <div className="space-y-2">
            {views.map((view) => (
              <ViewCard
                key={view.id}
                view={view}
                roles={allRoles}
                grantCount={grantsByView.get(view.id) ?? 0}
                expanded={expandedId === view.id}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}

        {/* Hint */}
        {!isLoading && !isError && views.length > 0 && (
          <p
            className="text-center text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            Changes take effect immediately — users see the new view set on next page load.
          </p>
        )}
      </div>
    </>
  );
}
