"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Activity,
  ExternalLink,
  Layers,
  MoreHorizontal,
  Plus,
  Terminal,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Modal } from "@/components/modal";
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
  StatCard,
  Textarea,
} from "@/components/ui";
import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  useApplications,
  useCreateApplication,
  useDeleteApplication,
  useUpdateApplication,
} from "@/features/iam-applications/hooks/use-applications";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Application } from "@/types/api";

// ─── Schemas ──────────────────────────────────────────────────────────────────

const createSchema = z.object({
  org_id: z.string().min(1, "Organisation required"),
  code: z.string()
    .min(1, "Code required")
    .max(64)
    .regex(/^[a-z0-9_-]+$/, "Lowercase letters, numbers, _ and - only"),
  label: z.string().min(1, "Label required").max(128),
  description: z.string().max(512).optional(),
});
type CreateForm = z.infer<typeof createSchema>;

const editSchema = z.object({
  label: z.string().min(1).max(128),
  description: z.string().max(512).optional(),
  is_active: z.boolean(),
});
type EditForm = z.infer<typeof editSchema>;

// ─── Helpers ──────────────────────────────────────────────────────────────────

const APP_COLORS = [
  "#1f6feb", "#6e40c9", "#e36209", "#2da44e",
  "#f78166", "#79c0ff", "#56d364", "#d29922",
];

function appColor(code: string) {
  return APP_COLORS[(code?.charCodeAt(0) ?? 0) % APP_COLORS.length];
}

function formatDate(ts: string) {
  return new Date(ts).toLocaleDateString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

// ─── App card ─────────────────────────────────────────────────────────────────

function AppCard({
  app,
  orgName,
  onEdit,
  onDelete,
}: {
  app: Application;
  orgName: string;
  onEdit: (app: Application) => void;
  onDelete: (app: Application) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const color = appColor(app.code ?? "a");

  return (
    <div
      className={cn(
        "group relative border border-[#21262d] rounded-xl bg-[#161b22] overflow-hidden",
        "hover:border-[#30363d] transition-all duration-200",
        !app.is_active && "opacity-60"
      )}
    >
      {/* Top accent stripe */}
      <div
        className="h-1 w-full"
        style={{ background: `linear-gradient(90deg, ${color}cc, ${color}33)` }}
      />

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {/* Avatar */}
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-base flex-shrink-0 shadow"
              style={{ backgroundColor: color }}
            >
              {(app.code ?? app.label ?? "A")[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[#e6edf3] truncate text-sm">
                  {app.label ?? "Untitled"}
                </span>
                {!app.is_active && (
                  <Badge tone="warning">inactive</Badge>
                )}
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Terminal size={10} className="text-[#8b949e]" />
                <code className="text-xs text-[#8b949e] font-mono">{app.code}</code>
              </div>
            </div>
          </div>

          {/* Overflow menu */}
          <div className="relative flex-shrink-0">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-1.5 rounded text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] transition-colors"
            >
              <MoreHorizontal size={14} />
            </button>
            {menuOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setMenuOpen(false)}
                />
                <div className="absolute right-0 top-8 z-20 w-36 bg-[#1c2128] border border-[#30363d] rounded-lg shadow-xl overflow-hidden">
                  <button
                    onClick={() => { setMenuOpen(false); onEdit(app); }}
                    className="w-full px-3 py-2 text-left text-xs text-[#e6edf3] hover:bg-[#21262d] transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onDelete(app); }}
                    className="w-full px-3 py-2 text-left text-xs text-[#f85149] hover:bg-[#21262d] transition-colors flex items-center gap-2"
                  >
                    <Trash2 size={11} />
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Description */}
        {app.description && (
          <p className="text-xs text-[#8b949e] mt-3 line-clamp-2">
            {app.description}
          </p>
        )}

        {/* Meta */}
        <div className="flex items-center gap-3 mt-4 pt-3 border-t border-[#21262d]">
          <div className="flex items-center gap-1 text-xs text-[#8b949e]">
            <Layers size={10} />
            <span className="truncate max-w-[120px]">{orgName}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-[#8b949e]">
            <Activity size={10} />
            <span>{formatDate(app.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Open hub footer */}
      <Link
        href={`/iam/applications/${app.id}`}
        className={cn(
          "flex items-center justify-center gap-1.5 py-2.5 text-xs font-semibold",
          "border-t border-[#21262d] text-[#8b949e]",
          "hover:text-[#58a6ff] hover:bg-[#1f2937] transition-colors"
        )}
      >
        <ExternalLink size={11} />
        Open application hub
      </Link>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ApplicationsPage() {
  const { toast } = useToast();
  const [orgFilter, setOrgFilter] = useState<string>("");
  const [openCreate, setOpenCreate] = useState(false);
  const [editApp, setEditApp] = useState<Application | null>(null);
  const [deleteApp, setDeleteApp] = useState<Application | null>(null);

  const { data, isLoading, isError, refetch } = useApplications({
    limit: 200,
    org_id: orgFilter || undefined,
  });

  const { data: orgsData } = useOrgs({ limit: 100 });
  const allOrgs = orgsData?.items ?? [];
  const orgMap = Object.fromEntries(allOrgs.map((o) => [o.id, o.display_name ?? o.slug]));

  const createApp = useCreateApplication();
  const updateApp = useUpdateApplication();
  const deleteAppMut = useDeleteApplication();

  const apps = data?.items ?? [];
  const total = apps.length;
  const activeCount = apps.filter((a) => a.is_active).length;
  const inactiveCount = apps.filter((a) => !a.is_active).length;

  // ─── Create form ─────────────────────────────────────────────────────
  const createForm = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: allOrgs[0]?.id ?? "",
      code: "",
      label: "",
      description: "",
    },
  });

  async function onCreateSubmit(values: CreateForm) {
    try {
      await createApp.mutateAsync({
        org_id: values.org_id,
        code: values.code,
        label: values.label,
        description: values.description || undefined,
      });
      toast("Application created", "success");
      setOpenCreate(false);
      createForm.reset();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to create application";
      toast(msg, "error");
    }
  }

  // ─── Edit form ───────────────────────────────────────────────────────
  const editForm = useForm<EditForm>({
    resolver: zodResolver(editSchema),
  });

  function openEdit(app: Application) {
    editForm.reset({
      label: app.label ?? "",
      description: app.description ?? "",
      is_active: app.is_active,
    });
    setEditApp(app);
  }

  async function onEditSubmit(values: EditForm) {
    if (!editApp) return;
    try {
      await updateApp.mutateAsync({
        id: editApp.id,
        body: {
          label: values.label,
          description: values.description || undefined,
          is_active: values.is_active,
        },
      });
      toast("Application updated", "success");
      setEditApp(null);
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to update";
      toast(msg, "error");
    }
  }

  async function onDeleteConfirm() {
    if (!deleteApp) return;
    try {
      await deleteAppMut.mutateAsync(deleteApp.id);
      toast("Application deleted", "success");
      setDeleteApp(null);
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to delete";
      toast(msg, "error");
    }
  }

  // ─── Render ──────────────────────────────────────────────────────────
  return (
    <>
      <div className="flex flex-col gap-6 p-8">
        <PageHeader
          title="Applications"
          description="Each application is an isolated IAM context — feature flags, roles, API keys, and audit events scoped to it. TennetCTL is the backbone for all of them."
          actions={
            <Button onClick={() => setOpenCreate(true)}>
              <Plus size={14} className="mr-1.5" />
              New application
            </Button>
          }
        />

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total Applications" value={String(total)} />
          <StatCard label="Active" value={String(activeCount)} accent="green" />
          <StatCard label="Inactive" value={String(inactiveCount)} accent="amber" />
        </div>

        {/* Org filter */}
        {allOrgs.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#8b949e] font-semibold uppercase tracking-wider">Org</span>
            <Select
              value={orgFilter}
              onChange={(e) => setOrgFilter(e.target.value)}
              className="w-56"
            >
              <option value="">All orgs</option>
              {allOrgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug}
                </option>
              ))}
            </Select>
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState message="Failed to load applications" retry={refetch} />
        ) : apps.length === 0 ? (
          <EmptyState
            title="No applications yet"
            description="Create your first application to connect an external service to TennetCTL. Each app gets its own feature flags, roles, API keys, and audit trail."
            action={
              <Button onClick={() => setOpenCreate(true)}>
                <Plus size={14} className="mr-1.5" />
                New application
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {apps.map((app) => (
              <AppCard
                key={app.id}
                app={app}
                orgName={orgMap[app.org_id] ?? app.org_id.slice(0, 8)}
                onEdit={openEdit}
                onDelete={setDeleteApp}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create modal */}
      <Modal
        open={openCreate}
        onClose={() => { setOpenCreate(false); createForm.reset(); }}
        title="New Application"
        description="Connect an external service to TennetCTL. Each application gets isolated IAM resources."
      >
        <form onSubmit={createForm.handleSubmit(onCreateSubmit)} className="space-y-4">
          <Field label="Organisation" error={createForm.formState.errors.org_id?.message}>
            <Select {...createForm.register("org_id")}>
              {allOrgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Code" hint="Unique identifier — lowercase letters, numbers, _, -" error={createForm.formState.errors.code?.message}>
            <Input
              placeholder="e.g. solsocial"
              {...createForm.register("code")}
            />
          </Field>
          <Field label="Label" error={createForm.formState.errors.label?.message}>
            <Input placeholder="e.g. SolSocial" {...createForm.register("label")} />
          </Field>
          <Field label="Description (optional)" error={createForm.formState.errors.description?.message}>
            <Textarea
              placeholder="What does this application do?"
              rows={2}
              {...createForm.register("description")}
            />
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setOpenCreate(false); createForm.reset(); }}>
              Cancel
            </Button>
            <Button type="submit" disabled={createApp.isPending}>
              {createApp.isPending ? "Creating…" : "Create application"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit modal */}
      <Modal
        open={!!editApp}
        onClose={() => setEditApp(null)}
        title={`Edit ${editApp?.label ?? "Application"}`}
      >
        <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
          <Field label="Label" error={editForm.formState.errors.label?.message}>
            <Input {...editForm.register("label")} />
          </Field>
          <Field label="Description (optional)">
            <Textarea rows={2} {...editForm.register("description")} />
          </Field>
          <Field label="Status">
            <Select {...editForm.register("is_active", { setValueAs: (v) => v === "true" })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setEditApp(null)}>Cancel</Button>
            <Button type="submit" disabled={updateApp.isPending}>
              {updateApp.isPending ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteApp}
        title={`Delete ${deleteApp?.label ?? "application"}?`}
        description={`This will permanently delete the application "${deleteApp?.label ?? deleteApp?.code}". This cannot be undone.`}
        confirmLabel="Delete"
        tone="danger"
        onConfirm={onDeleteConfirm}
        onClose={() => setDeleteApp(null)}
        loading={deleteAppMut.isPending}
      />
    </>
  );
}
