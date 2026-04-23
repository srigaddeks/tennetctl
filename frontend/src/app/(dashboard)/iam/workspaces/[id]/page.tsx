"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  ErrorState,
  Field,
  Input,
  Skeleton,
  StatCard,
} from "@/components/ui";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { WorkspaceMembers } from "@/features/iam-workspaces/_components/WorkspaceMembers";
import {
  useDeleteWorkspace,
  useUpdateWorkspace,
  useWorkspace,
} from "@/features/iam-workspaces/hooks/use-workspaces";
import { useSecrets } from "@/features/vault/secrets/hooks/use-secrets";
import { useFlags } from "@/features/featureflags/hooks/use-flags";
import { ApiClientError } from "@/lib/api";

const SLUG = /^[a-z][a-z0-9-]{1,62}$/;

const editSchema = z.object({
  slug: z.string().regex(SLUG, "invalid slug"),
  display_name: z.string().min(1, "required"),
});
type EditForm = z.infer<typeof editSchema>;

type QuickLinkCardProps = {
  label: string;
  count: number | string;
  sub: string;
  href: string;
  accentColor: string;
};

function QuickLinkCard({ label, count, sub, href, accentColor }: QuickLinkCardProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <Link
      href={href}
      style={{
        display: "block",
        background: "var(--bg-elevated)",
        border: `1px solid ${hovered ? accentColor : "var(--border)"}`,
        borderRadius: "8px",
        padding: "16px",
        textDecoration: "none",
        transition: "border-color 150ms ease",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <p
        className="label-caps mb-2"
        style={{ color: "var(--text-secondary)" }}
      >
        {label}
      </p>
      <p
        className="text-xl font-semibold"
        style={{ color: hovered ? accentColor : "var(--text-primary)" }}
      >
        {count}
      </p>
      <p
        className="text-xs mt-1"
        style={{ color: "var(--text-muted)" }}
      >
        {sub} →
      </p>
    </Link>
  );
}

export default function WorkspaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = typeof params.id === "string" ? params.id : "";
  const { toast } = useToast();

  const { data: ws, isLoading, isError, error } = useWorkspace(workspaceId);
  const { data: orgs } = useOrgs({ limit: 500 });
  const update = useUpdateWorkspace();
  const del = useDeleteWorkspace();

  const org = orgs?.items.find((o) => o.id === ws?.org_id);

  const { data: secrets } = useSecrets({ workspace_id: workspaceId });
  const { data: flags } = useFlags({ org_id: ws?.org_id ?? undefined, limit: 1 });

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConfirmInput, setDeleteConfirmInput] = useState("");

  const form = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    defaultValues: { slug: "", display_name: "" },
  });

  useEffect(() => {
    if (ws) {
      form.reset({
        slug: ws.slug,
        display_name: ws.display_name ?? "",
      });
    }
  }, [ws, form]);

  async function onSave(values: EditForm) {
    if (!ws) return;
    const dirty = form.formState.dirtyFields;
    const body: { slug?: string; display_name?: string } = {};
    if (dirty.slug) body.slug = values.slug;
    if (dirty.display_name) body.display_name = values.display_name;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: ws.id, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function handleDelete() {
    if (!ws) return;
    if (deleteConfirmInput !== ws.slug) return;
    try {
      await del.mutateAsync(ws.id);
      toast("Workspace deleted", "success");
      router.push("/iam/workspaces");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    } finally {
      setDeleteOpen(false);
      setDeleteConfirmInput("");
    }
  }

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Workspace"
          description="Loading…"
          testId="heading-workspace-detail"
        />
        <div className="px-8 py-6 space-y-3">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-48" />
        </div>
      </>
    );
  }

  if (isError || !ws) {
    return (
      <>
        <PageHeader
          title="Workspace"
          description="Not found"
          testId="heading-workspace-detail"
        />
        <div className="px-8 py-6">
          <ErrorState
            message={
              error instanceof Error
                ? error.message
                : "Workspace not found or you don't have access."
            }
          />
          <div className="mt-4">
            <Link
              href="/iam/workspaces"
              style={{ color: "var(--text-secondary)" }}
              className="text-sm hover:underline"
            >
              ← Back to workspaces
            </Link>
          </div>
        </div>
      </>
    );
  }

  const secretCount = secrets?.pagination.total ?? 0;
  const flagCount = flags?.pagination.total ?? 0;

  return (
    <>
      <PageHeader
        title={ws.display_name ?? ws.slug}
        description={`Workspace in org ${org?.slug ?? ws.org_id.slice(0, 8)}`}
        testId="heading-workspace-detail"
        breadcrumbs={[
          { label: "IAM", href: "/iam/workspaces" },
          { label: "Workspaces", href: "/iam/workspaces" },
          { label: ws.display_name ?? ws.slug },
        ]}
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="workspace-detail-body">

        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-3 gap-4">
          <StatCard
            label="Status"
            value={ws.is_active ? "Active" : "Inactive"}
            sub="workspace state"
            accent={ws.is_active ? "green" : "red"}
          />
          <StatCard
            label="Organisation"
            value={org?.display_name ?? org?.slug ?? ws.org_id.slice(0, 8)}
            sub={org?.slug ?? "parent org"}
            accent="blue"
          />
          <StatCard
            label="Created"
            value={ws.created_at.slice(0, 10)}
            sub={`ID: ${ws.id.slice(0, 8)}…`}
            accent="blue"
          />
        </div>

        {/* General Info section */}
        <section
          className="mb-6 rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="ws-detail-info"
        >
          <div className="mb-5 flex items-center justify-between">
            <h2
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              General Information
            </h2>
            <div className="flex flex-wrap gap-1.5">
              <Badge tone={ws.is_active ? "success" : "default"} dot={ws.is_active}>
                {ws.is_active ? "active" : "inactive"}
              </Badge>
              <Badge tone="default">
                org: {org?.slug ?? `${ws.org_id.slice(0, 8)}…`}
              </Badge>
            </div>
          </div>

          <form
            onSubmit={form.handleSubmit(onSave)}
            className="flex flex-col gap-4"
            data-testid="ws-edit-form"
          >
            <div className="grid grid-cols-2 gap-4">
              <Field
                label="Slug"
                required
                error={form.formState.errors.slug?.message}
                htmlFor="ws-edit-slug"
              >
                <Input
                  id="ws-edit-slug"
                  {...form.register("slug")}
                  data-testid="ws-edit-slug"
                />
              </Field>
              <Field
                label="Display Name"
                required
                error={form.formState.errors.display_name?.message}
                htmlFor="ws-edit-display-name"
              >
                <Input
                  id="ws-edit-display-name"
                  {...form.register("display_name")}
                  data-testid="ws-edit-display-name"
                />
              </Field>
            </div>

            <div
              className="flex justify-between gap-2 pt-4"
              style={{ borderTop: "1px solid var(--border)" }}
            >
              <Button
                variant="danger"
                type="button"
                size="sm"
                onClick={() => setDeleteOpen(true)}
                data-testid="ws-delete-open"
              >
                Delete workspace
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
                data-testid="ws-edit-save"
              >
                Save changes
              </Button>
            </div>
          </form>
        </section>

        {/* Resources section */}
        <section className="mb-6" data-testid="ws-resources-section">
          <h2
            className="label-caps mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            Resources
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <QuickLinkCard
              label="Vault Secrets"
              count={secretCount}
              sub="secrets in this workspace"
              href={`/vault/secrets?workspace_id=${ws.id}`}
              accentColor="#f5a623"
            />
            <QuickLinkCard
              label="Audit Events"
              count="View"
              sub="activity for this workspace"
              href={`/audit?workspace_id=${ws.id}`}
              accentColor="#ff6b35"
            />
            <QuickLinkCard
              label="Feature Flags"
              count={flagCount}
              sub="flags in parent org"
              href={`/feature-flags?org_id=${ws.org_id}`}
              accentColor="var(--accent)"
            />
          </div>
        </section>

        {/* Members section */}
        <section
          className="rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
        >
          <h2
            className="label-caps mb-5"
            style={{ color: "var(--text-secondary)" }}
          >
            Members
          </h2>
          <WorkspaceMembers workspaceId={ws.id} orgId={ws.org_id} />
        </section>
      </div>

      <Modal
        open={deleteOpen}
        onClose={() => {
          setDeleteOpen(false);
          setDeleteConfirmInput("");
        }}
        title={`Delete workspace "${ws.slug}"?`}
        description="This soft-deletes the workspace. Memberships remain linked but the workspace is hidden from active listings."
      >
        <div className="flex flex-col gap-4">
          <Field
            label={`Type the slug "${ws.slug}" to confirm`}
            htmlFor="ws-delete-confirm-input"
          >
            <Input
              id="ws-delete-confirm-input"
              value={deleteConfirmInput}
              onChange={(e) => setDeleteConfirmInput(e.target.value)}
              placeholder={ws.slug}
              data-testid="ws-delete-confirm-input"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              type="button"
              onClick={() => {
                setDeleteOpen(false);
                setDeleteConfirmInput("");
              }}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              type="button"
              disabled={deleteConfirmInput !== ws.slug}
              loading={del.isPending}
              onClick={handleDelete}
              data-testid="ws-delete-confirm-submit"
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
