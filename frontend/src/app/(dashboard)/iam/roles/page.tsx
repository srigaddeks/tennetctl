"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  ChevronRight,
  Copy,
  Globe,
  Info,
  Lock,
  Pencil,
  Plus,
  Search,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  Textarea,
} from "@/components/ui";
import { CapabilityGrid } from "@/features/capabilities/capability-grid";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import {
  useCreateRole,
  useDeleteRole,
  useUpdateRole,
  useRoles,
} from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Role, RoleType } from "@/types/api";

// ─── Types ─────────────────────────────────────────────────────────────────────

type RoleCategory = "platform" | "org-scoped";
type ActiveTab = "overview" | "capabilities" | "audit";

type ConfirmAction = {
  title: string;
  body: string;
  variant: "info" | "warning" | "danger";
  confirmLabel: string;
  onConfirm: () => Promise<void>;
};

// ─── Constants ─────────────────────────────────────────────────────────────────

const CATEGORY_META: Record<
  RoleCategory,
  {
    label: string;
    icon: typeof Globe;
    borderCls: string;
    numCls: string;
    desc: string;
  }
> = {
  platform: {
    label: "Platform",
    icon: Globe,
    borderCls: "border-l-violet-500",
    numCls: "text-violet-600 dark:text-violet-400",
    desc: "Roles without an org (org_id = NULL) — apply across the whole platform",
  },
  "org-scoped": {
    label: "Org-scoped",
    icon: Building2,
    borderCls: "border-l-blue-500",
    numCls: "text-blue-600 dark:text-blue-400",
    desc: "Roles bound to a specific org",
  },
};

const ROLE_TYPE_BADGE: Record<
  RoleType,
  { tone: "purple" | "blue"; label: string }
> = {
  system: { tone: "purple", label: "system" },
  custom: { tone: "blue", label: "custom" },
};

const CODE_RE = /^[a-z][a-z0-9_]{1,62}$/;

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 62);
}

// ─── Zod schemas ──────────────────────────────────────────────────────────────

const createSchema = z.object({
  org_id: z.string().optional(),
  role_type: z.enum(["system", "custom"]),
  code: z.string().regex(CODE_RE, "Must be lowercase_snake_case (a–z, 0–9, _)"),
  label: z.string().min(1, "Required"),
  description: z.string().optional(),
});
type CreateForm = z.infer<typeof createSchema>;

const updateSchema = z.object({
  label: z.string().min(1, "Required").optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});
type UpdateForm = z.infer<typeof updateSchema>;

// ─── ConfirmDialog ────────────────────────────────────────────────────────────

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
    info: {
      icon: Info,
      iconColor: "text-blue-600",
      bg: "bg-blue-50 dark:bg-blue-950/40",
      border: "border-blue-200 dark:border-blue-900/50",
    },
    warning: {
      icon: AlertTriangle,
      iconColor: "text-amber-600",
      bg: "bg-amber-50 dark:bg-amber-950/40",
      border: "border-amber-200 dark:border-amber-900/50",
    },
    danger: {
      icon: AlertTriangle,
      iconColor: "text-red-600",
      bg: "bg-red-50 dark:bg-red-950/40",
      border: "border-red-200 dark:border-red-900/50",
    },
  };
  const colors = colorsMap[action.variant];
  const IconComp = colors.icon;

  async function confirm() {
    setRunning(true);
    try {
      await action?.onConfirm();
    } catch {
      /* errors surfaced by caller */
    }
    setRunning(false);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      data-testid="confirm-dialog"
    >
      <div className="mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-start gap-3 p-6 pb-4">
          <div
            className={cn(
              "shrink-0 rounded-xl p-2 border",
              colors.bg,
              colors.border
            )}
          >
            <IconComp className={cn("h-5 w-5", colors.iconColor)} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
              {action.title}
            </h2>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {action.body}
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <Button variant="secondary" size="sm" onClick={onClose} disabled={running}>
            Cancel
          </Button>
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

// ─── StatCards ────────────────────────────────────────────────────────────────

type StatCard = {
  label: string;
  value: number;
  icon: typeof ShieldCheck;
  borderCls: string;
  numCls: string;
  testId: string;
};

function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map(({ label, value, icon: Icon, borderCls, numCls, testId }) => (
        <div
          key={label}
          className={cn(
            "flex items-center gap-3 rounded-xl border border-l-[3px] bg-white px-4 py-3 dark:bg-zinc-950",
            "border-zinc-200 dark:border-zinc-800",
            borderCls
          )}
          data-testid={testId}
        >
          <div className="shrink-0 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">
            <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </div>
          <div className="min-w-0">
            <span
              className={cn(
                "block text-2xl font-bold tabular-nums leading-none",
                numCls
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

// ─── Tab bar ──────────────────────────────────────────────────────────────────

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

// ─── OverviewTab ──────────────────────────────────────────────────────────────

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
          <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700 dark:border-blue-900/50 dark:bg-blue-900/30 dark:text-blue-300">
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

// ─── CapabilitiesTab (23R unified model) ──────────────────────────────────────

function CapabilitiesTab({ roleId, roleCode }: { roleId: string; roleCode: string | null }) {
  return (
    <div className="py-2">
      <CapabilityGrid roleId={roleId} roleCode={roleCode} />
    </div>
  );
}

// ─── AuditTab ─────────────────────────────────────────────────────────────────

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

// ─── ExpandedPanel ────────────────────────────────────────────────────────────

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

// ─── RoleRow ──────────────────────────────────────────────────────────────────

function RoleRow({
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
            <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-700 dark:border-blue-900/50 dark:bg-blue-900/30 dark:text-blue-300">
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

// ─── CategorySection ──────────────────────────────────────────────────────────

function CategorySection({
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

// ─── CreateRoleDialog ─────────────────────────────────────────────────────────

function CreateRoleDialog({
  open,
  onClose,
  orgs,
}: {
  open: boolean;
  onClose: () => void;
  orgs: { id: string; slug: string; display_name: string | null }[];
}) {
  const { toast } = useToast();
  const create = useCreateRole();

  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: "",
      role_type: "custom",
      code: "",
      label: "",
      description: "",
    },
  });

  const labelVal = form.watch("label");

  // Auto-generate code from label
  useEffect(() => {
    if (!form.formState.dirtyFields.code && labelVal) {
      form.setValue("code", slugify(labelVal), { shouldDirty: false });
    }
  }, [labelVal, form]);

  useEffect(() => {
    if (open) {
      form.reset({
        org_id: "",
        role_type: "custom",
        code: "",
        label: "",
        description: "",
      });
    }
  }, [open, form]);

  async function onSubmit(v: CreateForm) {
    try {
      const role = await create.mutateAsync({
        org_id: v.org_id || null,
        role_type: v.role_type,
        code: v.code,
        label: v.label,
        ...(v.description ? { description: v.description } : {}),
      });
      toast(`Created role "${role.code}"`, "success");
      onClose();
    } catch (err) {
      toast(err instanceof ApiClientError ? err.message : String(err), "error");
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-zinc-500" />
            <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              New role
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4 p-6"
          data-testid="create-role-form"
        >
          {/* Org picker — optional, omit = platform */}
          <Field label="Org" hint="optional — omit for platform role">
            <Select
              {...form.register("org_id")}
              data-testid="create-role-org"
            >
              <option value="">— Platform (no org) —</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Role type">
            <Select {...form.register("role_type")}>
              <option value="custom">Custom</option>
              <option value="system">System</option>
            </Select>
          </Field>

          <Field
            label="Label"
            required
            error={form.formState.errors.label?.message}
          >
            <Input
              placeholder="Platform Admin"
              {...form.register("label")}
              data-testid="create-role-label"
            />
          </Field>

          <Field
            label="Code"
            required
            hint="lowercase_snake_case"
            error={form.formState.errors.code?.message}
          >
            <Input
              placeholder="platform_admin"
              {...form.register("code")}
              data-testid="create-role-code"
              className="font-mono"
            />
          </Field>

          <Field label="Description" hint="optional">
            <Textarea rows={2} {...form.register("description")} />
          </Field>

          <div className="flex justify-end gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <Button type="button" variant="secondary" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              loading={create.isPending}
              data-testid="create-role-submit"
            >
              <Plus className="h-3.5 w-3.5" />
              Create role
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────────

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
  const createRole = useCreateRole();
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
