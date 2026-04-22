"use client";

import {
  Building2,
  Globe,
  Lock,
  Plus,
  Search,
  ShieldAlert,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import { ConfirmDialog } from "@/features/iam-roles/_components/confirm-dialog";
import { CreateRoleDialog } from "@/features/iam-roles/_components/create-role-dialog";
import { CategorySection } from "@/features/iam-roles/_components/role-row";
import { StatCards } from "@/features/iam-roles/_components/stat-cards";
import type { ConfirmAction, RoleCategory, StatCard } from "@/features/iam-roles/_components/types";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import {
  useDeleteRole,
  useRoles,
} from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Role } from "@/types/api";

export default function RolesPage() {
  const [orgFilter, setOrgFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [openCreate, setOpenCreate] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);

  const { data: orgsData } = useOrgs({ limit: 500 });
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useRoles({ limit: 500 });

  const deleteRole = useDeleteRole();
  const { toast } = useToast();

  const allRoles = data?.items ?? [];
  const allOrgs = orgsData?.items ?? [];

  // Build org lookup map
  const orgsMap = useMemo(() => {
    const m = new Map<string, string>();
    for (const o of allOrgs) {
      m.set(o.id, o.display_name ?? o.slug);
    }
    return m;
  }, [allOrgs]);

  // Stats
  const stats = useMemo(
    () => ({
      total: allRoles.length,
      platform: allRoles.filter((r) => !r.org_id).length,
      orgScoped: allRoles.filter((r) => !!r.org_id).length,
      system: allRoles.filter((r) => r.role_type === "system").length,
      custom: allRoles.filter((r) => r.role_type === "custom").length,
    }),
    [allRoles]
  );

  // Filter pipeline
  const filtered = useMemo(() => {
    let roles = allRoles;

    if (orgFilter !== "all") {
      if (orgFilter === "platform") {
        roles = roles.filter((r) => !r.org_id);
      } else {
        roles = roles.filter((r) => r.org_id === orgFilter);
      }
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      roles = roles.filter(
        (r) =>
          (r.code ?? "").toLowerCase().includes(q) ||
          (r.label ?? "").toLowerCase().includes(q)
      );
    }

    return roles;
  }, [allRoles, orgFilter, search]);

  // Group
  const grouped = useMemo(() => {
    const platform = filtered.filter((r) => !r.org_id);
    const orgScoped = filtered.filter((r) => !!r.org_id);
    const result: { category: RoleCategory; roles: Role[] }[] = [];
    if (platform.length > 0) result.push({ category: "platform", roles: platform });
    if (orgScoped.length > 0) result.push({ category: "org-scoped", roles: orgScoped });
    return result;
  }, [filtered]);

  function handleToggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  function handleDelete(role: Role) {
    setConfirmAction({
      title: "Delete role?",
      body: `"${role.code ?? role.id}" will be soft-deleted. This cannot be undone from the UI.`,
      variant: "danger",
      confirmLabel: "Delete",
      onConfirm: async () => {
        try {
          await deleteRole.mutateAsync(role.id);
          toast(`Role "${role.code}" deleted`, "success");
          if (expandedId === role.id) setExpandedId(null);
        } catch (err) {
          toast(err instanceof ApiClientError ? err.message : String(err), "error");
        }
      },
    });
  }

  function handleDuplicate(role: Role) {
    // Pre-fill create dialog fields by opening it and then setting values
    setOpenCreate(true);
    // We rely on the CreateRoleDialog useEffect reset — caller opens dialog;
    // actual pre-fill would require a separate prop; log intent for now.
    // TODO: pass defaultValues prop to CreateRoleDialog for duplicate pre-fill
    toast(`Opened create dialog — adjust code and label to duplicate "${role.code}"`, "info");
  }

  const statCards: StatCard[] = [
    {
      label: "Total",
      value: stats.total,
      icon: ShieldCheck,
      borderCls: "border-l-zinc-900 dark:border-l-zinc-100",
      numCls: "text-zinc-900 dark:text-zinc-50",
      testId: "stat-card-total",
    },
    {
      label: "Platform",
      value: stats.platform,
      icon: Globe,
      borderCls: "border-l-violet-500",
      numCls: "text-violet-600 dark:text-violet-400",
      testId: "stat-card-platform",
    },
    {
      label: "Org-scoped",
      value: stats.orgScoped,
      icon: Building2,
      borderCls: "border-l-blue-500",
      numCls: "text-blue-600 dark:text-blue-400",
      testId: "stat-card-org-scoped",
    },
    {
      label: "System",
      value: stats.system,
      icon: Lock,
      borderCls: "border-l-purple-500",
      numCls: "text-purple-600 dark:text-purple-400",
      testId: "stat-card-system",
    },
    {
      label: "Custom",
      value: stats.custom,
      icon: Users,
      borderCls: "border-l-emerald-500",
      numCls: "text-emerald-600 dark:text-emerald-400",
      testId: "stat-card-custom",
    },
  ];

  return (
    <>
      {confirmAction && (
        <ConfirmDialog action={confirmAction} onClose={() => setConfirmAction(null)} />
      )}

      {openCreate && (
        <CreateRoleDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
          orgs={allOrgs}
        />
      )}

      <PageHeader
        title="Roles"
        description="Named permission bundles. Platform roles (no org) apply globally; org-scoped roles are bound to a specific org."
        testId="heading-roles"
        actions={
          <Button
            onClick={() => setOpenCreate(true)}
            data-testid="open-create-role"
          >
            <Plus className="h-4 w-4" />
            New role
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {/* Stat cards */}
        {!isLoading && !isError && <StatCards cards={statCards} />}

        {/* Filter bar */}
        {!isLoading && !isError && (
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
            {/* Org pills */}
            <button
              type="button"
              onClick={() => setOrgFilter("all")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
                orgFilter === "all"
                  ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                  : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50"
              )}
              data-testid="filter-role-org-all"
            >
              All orgs
              <span className={cn("tabular-nums", orgFilter === "all" ? "opacity-70" : "text-zinc-400")}>
                {stats.total}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setOrgFilter("platform")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
                orgFilter === "platform"
                  ? "border-violet-700 bg-violet-700 text-white dark:border-violet-300 dark:bg-violet-300 dark:text-violet-900"
                  : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50"
              )}
              data-testid="filter-role-org-platform"
            >
              <Globe className="h-3 w-3" />
              Platform
              <span className={cn("tabular-nums", orgFilter === "platform" ? "opacity-70" : "text-zinc-400")}>
                {stats.platform}
              </span>
            </button>

            {/* Per-org pills */}
            {allOrgs.map((org) => {
              const count = allRoles.filter((r) => r.org_id === org.id).length;
              if (count === 0) return null;
              const active = orgFilter === org.id;
              return (
                <button
                  key={org.id}
                  type="button"
                  onClick={() => setOrgFilter(org.id)}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
                    active
                      ? "border-blue-700 bg-blue-700 text-white dark:border-blue-300 dark:bg-blue-300 dark:text-blue-900"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50"
                  )}
                  data-testid={`filter-role-org-${org.id}`}
                >
                  <Building2 className="h-3 w-3" />
                  {org.display_name ?? org.slug}
                  <span className={cn("tabular-nums", active ? "opacity-70" : "text-zinc-400")}>
                    {count}
                  </span>
                </button>
              );
            })}

            {/* Active filter chips */}
            {orgFilter !== "all" && (
              <button
                type="button"
                onClick={() => setOrgFilter("all")}
                className="inline-flex items-center gap-1 rounded-full border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-700 transition hover:bg-zinc-200 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
              >
                {orgFilter === "platform"
                  ? "scope: platform"
                  : `org: ${orgsMap.get(orgFilter) ?? orgFilter.slice(0, 8)}`}
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
                placeholder="Search roles…"
                className="h-7 w-full rounded-lg border border-zinc-200 bg-white pl-7 pr-2 text-xs text-zinc-900 transition focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
                data-testid="filter-role-search"
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
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Failed to load roles"}
            retry={() => refetch()}
          />
        )}

        {/* Grouped list */}
        {data && filtered.length > 0 && (
          <div className="space-y-1">
            {grouped.map(({ category, roles }) => (
              <CategorySection
                key={category}
                category={category}
                roles={roles}
                orgsMap={orgsMap}
                expandedId={expandedId}
                onToggle={handleToggleExpand}
                onDelete={handleDelete}
                onDuplicate={handleDuplicate}
              />
            ))}
          </div>
        )}

        {/* Empty: no roles at all */}
        {data && allRoles.length === 0 && (
          <EmptyState
            title="No roles yet"
            description="Create your first role. Platform roles apply globally; org-scoped roles bind to a specific org."
            action={
              <Button onClick={() => setOpenCreate(true)}>
                <Plus className="h-4 w-4" />
                Create first role
              </Button>
            }
          />
        )}

        {/* Empty: filters produced nothing */}
        {data && allRoles.length > 0 && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 px-6 py-12 text-center dark:border-zinc-700">
            <ShieldAlert className="h-8 w-8 text-zinc-400" />
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              No roles match your filters.
            </p>
            <button
              type="button"
              onClick={() => {
                setOrgFilter("all");
                setSearch("");
              }}
              className="text-xs font-medium text-zinc-600 underline underline-offset-2 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    </>
  );
}
