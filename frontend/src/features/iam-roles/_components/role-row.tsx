"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Building2,
  ChevronDown,
  ChevronRight,
  Copy,
  Lock,
  Pencil,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Field,
  Input,
  Textarea,
} from "@/components/ui";
import { CapabilityGrid } from "@/features/capabilities/capability-grid";
import { useUpdateRole } from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Role } from "@/types/api";

import { CATEGORY_META, ROLE_TYPE_BADGE, updateSchema, type UpdateForm } from "./constants";
import type { ActiveTab, RoleCategory } from "./types";

function TabBar({
  active,
  roleCode,
  onChange,
}: {
  active: ActiveTab;
  roleCode: string;
  onChange: (t: ActiveTab) => void;
}) {
  const tabs: { id: ActiveTab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "capabilities", label: "Capabilities" },
    { id: "audit", label: "Audit" },
  ];
  return (
    <div className="flex gap-0 border-b border-zinc-200 dark:border-zinc-800">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          data-testid={`tab-${t.id}-${roleCode}`}
          className={cn(
            "px-4 py-2 text-xs font-medium transition border-b-2 -mb-px",
            active === t.id
              ? "border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-50"
              : "border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

function OverviewTab({
  role,
  orgLabel,
  onSaved,
  onDelete,
  onDuplicate,
  onClose,
}: {
  role: Role;
  orgLabel: string | null;
  onSaved: (updated: Role) => void;
  onDelete: (role: Role) => void;
  onDuplicate: (role: Role) => void;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const update = useUpdateRole();

  const form = useForm<UpdateForm>({
    resolver: zodResolver(updateSchema),
    defaultValues: {
      label: role.label ?? "",
      description: role.description ?? "",
      is_active: role.is_active,
    },
  });

  // Reset when role changes
  useEffect(() => {
    form.reset({
      label: role.label ?? "",
      description: role.description ?? "",
      is_active: role.is_active,
    });
  }, [role.id, form]); // eslint-disable-line react-hooks/exhaustive-deps

  async function onSubmit(v: UpdateForm) {
    const dirty = form.formState.dirtyFields;
    const body: UpdateForm = {};
    if (dirty.label) body.label = v.label;
    if (dirty.description) body.description = v.description;
    if (dirty.is_active) body.is_active = v.is_active;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      const updated = await update.mutateAsync({ id: role.id, body });
      toast("Saved", "success");
      onSaved(updated);
    } catch (err) {
      toast(err instanceof ApiClientError ? err.message : String(err), "error");
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4 pt-4">
      {/* Metadata row */}
      <div className="flex flex-wrap gap-1.5">
        <Badge tone={ROLE_TYPE_BADGE[role.role_type].tone}>
          {ROLE_TYPE_BADGE[role.role_type].label}
        </Badge>
        {!role.org_id && <Badge tone="amber">platform</Badge>}
        {orgLabel && (
          <span className="inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-800/40 px-2 py-0.5 text-[11px] font-medium text-zinc-300 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300">
            <Building2 className="h-2.5 w-2.5" />
            {orgLabel}
          </span>
        )}
        <Badge tone={role.is_active ? "emerald" : "zinc"}>
          {role.is_active ? "active" : "inactive"}
        </Badge>
      </div>

      {/* Code — frozen */}
      <Field label="Code" hint="frozen after create">
        <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-900">
          <code className="flex-1 font-mono text-xs text-zinc-700 dark:text-zinc-300">
            {role.code ?? "—"}
          </code>
          <Lock className="h-3 w-3 shrink-0 text-zinc-400" />
        </div>
      </Field>

      <Field label="Label" error={form.formState.errors.label?.message}>
        <Input
          {...form.register("label")}
          data-testid={`edit-label-${role.code}`}
        />
      </Field>

      <Field label="Description">
        <Textarea rows={3} {...form.register("description")} />
      </Field>

      <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
        <input
          type="checkbox"
          {...form.register("is_active")}
          className="h-4 w-4 rounded border-zinc-300 dark:border-zinc-700"
        />
        Active
      </label>

      {/* Action row */}
      <div className="mt-2 flex items-center justify-between border-t border-zinc-200 pt-4 dark:border-zinc-800">
        <div className="flex gap-1.5">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => onDuplicate(role)}
            title="Duplicate role"
          >
            <Copy className="h-3.5 w-3.5" />
            Duplicate
          </Button>
          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={() => onDelete(role)}
            data-testid={`delete-role-${role.code}`}
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </Button>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            size="sm"
            loading={update.isPending}
            disabled={!form.formState.isDirty}
            data-testid={`save-role-${role.code}`}
          >
            Save
          </Button>
        </div>
      </div>
    </form>
  );
}

function CapabilitiesTab({ roleId, roleCode }: { roleId: string; roleCode: string | null }) {
  return (
    <div className="py-2">
      <CapabilityGrid roleId={roleId} roleCode={roleCode} />
    </div>
  );
}

function AuditTab() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
      <ShieldCheck className="h-8 w-8 text-zinc-300 dark:text-zinc-600" />
      <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
        Audit trail view — see /audit for now
      </p>
      <p className="text-xs text-zinc-400 dark:text-zinc-500">
        Full per-role audit history will be available in the Audit module.
      </p>
    </div>
  );
}

function ExpandedPanel({
  role,
  orgLabel,
  onClose,
  onDelete,
  onDuplicate,
}: {
  role: Role;
  orgLabel: string | null;
  onClose: () => void;
  onDelete: (role: Role) => void;
  onDuplicate: (role: Role) => void;
}) {
  const [tab, setTab] = useState<ActiveTab>("overview");

  // Reset tab when role changes
  useEffect(() => {
    setTab("overview");
  }, [role.id]);

  return (
    <div className="border-t border-zinc-100 bg-zinc-50 px-4 pb-4 dark:border-zinc-800 dark:bg-zinc-900/40">
      <TabBar active={tab} roleCode={role.code ?? role.id} onChange={setTab} />

      {tab === "overview" && (
        <OverviewTab
          role={role}
          orgLabel={orgLabel}
          onSaved={() => {/* cache invalidated by mutation */}}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
          onClose={onClose}
        />
      )}
      {tab === "capabilities" && <CapabilitiesTab roleId={role.id} roleCode={role.code} />}
      {tab === "audit" && <AuditTab />}
    </div>
  );
}

export function RoleRow({
  role,
  orgLabel,
  expanded,
  onToggle,
  onDelete,
  onDuplicate,
}: {
  role: Role;
  orgLabel: string | null;
  expanded: boolean;
  onToggle: (id: string) => void;
  onDelete: (role: Role) => void;
  onDuplicate: (role: Role) => void;
}) {
  const category: RoleCategory = role.org_id ? "org-scoped" : "platform";
  const meta = CATEGORY_META[category];
  const typeMeta = ROLE_TYPE_BADGE[role.role_type];

  return (
    <div
      className={cn(
        "border-b border-zinc-100 last:border-b-0 dark:border-zinc-800/60",
        !role.is_active && "opacity-60"
      )}
      data-testid={`role-row-${role.code ?? role.id}`}
    >
      {/* Collapsed header */}
      <div
        className={cn(
          "grid grid-cols-[auto_1fr_auto] items-center gap-x-3 border-l-[3px] px-4 py-3 transition hover:bg-zinc-50 dark:hover:bg-zinc-900/30",
          meta.borderCls,
          expanded && "bg-zinc-50 dark:bg-zinc-900/40"
        )}
      >
        {/* Expand chevron */}
        <button
          type="button"
          onClick={() => onToggle(role.id)}
          title={expanded ? "Collapse" : "Expand"}
          data-testid={`expand-role-${role.code ?? role.id}`}
          className="shrink-0 rounded-md p-1 text-zinc-400 transition hover:bg-zinc-200 hover:text-zinc-700 dark:hover:bg-zinc-700 dark:hover:text-zinc-200"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </button>

        {/* Code + label + badges */}
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <code className="font-mono text-xs font-semibold text-zinc-900 dark:text-zinc-50">
            {role.code ?? "—"}
          </code>
          {role.label && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {role.label}
            </span>
          )}
          <Badge tone={typeMeta.tone}>{typeMeta.label}</Badge>
          {orgLabel && (
            <span className="inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-800/40 px-1.5 py-0.5 text-[10px] font-medium text-zinc-300 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300">
              <Building2 className="h-2.5 w-2.5" />
              {orgLabel}
            </span>
          )}
          {!role.is_active && (
            <Badge tone="zinc">inactive</Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => onToggle(role.id)}
            title="Edit"
            className="rounded-md p-1 text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
          >
            <Pencil className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <ExpandedPanel
          role={role}
          orgLabel={orgLabel}
          onClose={() => onToggle(role.id)}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
        />
      )}
    </div>
  );
}

export function CategorySection({
  category,
  roles,
  orgsMap,
  expandedId,
  onToggle,
  onDelete,
  onDuplicate,
}: {
  category: RoleCategory;
  roles: Role[];
  orgsMap: Map<string, string>;
  expandedId: string | null;
  onToggle: (id: string) => void;
  onDelete: (role: Role) => void;
  onDuplicate: (role: Role) => void;
}) {
  const [open, setOpen] = useState(true);
  const meta = CATEGORY_META[category];
  const Icon = meta.icon;
  const activeCount = roles.filter((r) => r.is_active).length;

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-zinc-100 dark:hover:bg-zinc-800/50"
        data-testid={`group-header-${category}`}
      >
        <Icon className="h-4 w-4 shrink-0 text-zinc-500 dark:text-zinc-400" />
        <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          {meta.label}
        </span>
        <span className="text-[11px] text-zinc-400 dark:text-zinc-500">
          {meta.desc}
        </span>
        <span className="ml-auto text-xs tabular-nums text-zinc-500 dark:text-zinc-400">
          {roles.length}
        </span>
        <span className={cn("text-[11px] font-medium tabular-nums", meta.numCls)}>
          {activeCount} active
        </span>
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-zinc-400" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-zinc-400" />
        )}
      </button>

      {open && (
        <div className="mb-3 ml-4 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          {roles.map((role) => (
            <RoleRow
              key={role.id}
              role={role}
              orgLabel={role.org_id ? (orgsMap.get(role.org_id) ?? role.org_id.slice(0, 8)) : null}
              expanded={expandedId === role.id}
              onToggle={onToggle}
              onDelete={onDelete}
              onDuplicate={onDuplicate}
            />
          ))}
        </div>
      )}
    </div>
  );
}
