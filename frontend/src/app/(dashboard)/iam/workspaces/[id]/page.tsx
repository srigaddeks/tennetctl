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
} from "@/components/ui";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { WorkspaceMembers } from "@/features/iam-workspaces/_components/WorkspaceMembers";
import {
  useDeleteWorkspace,
  useUpdateWorkspace,
  useWorkspace,
} from "@/features/iam-workspaces/hooks/use-workspaces";
import { ApiClientError } from "@/lib/api";

const SLUG = /^[a-z][a-z0-9-]{1,62}$/;

const editSchema = z.object({
  slug: z.string().regex(SLUG, "invalid slug"),
  display_name: z.string().min(1, "required"),
});
type EditForm = z.infer<typeof editSchema>;

export default function WorkspaceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = typeof params.id === "string" ? params.id : "";
  const { toast } = useToast();

  const { data: ws, isLoading, isError, error } = useWorkspace(workspaceId);
  const { data: orgs } = useOrgs({ limit: 500 });
  const update = useUpdateWorkspace();
  const del = useDeleteWorkspace();

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
        <div className="px-8 py-6">
          <Skeleton className="mb-3 h-6 w-48" />
          <Skeleton className="mb-3 h-6 w-72" />
          <Skeleton className="h-6 w-32" />
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
              className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              ← Back to workspaces
            </Link>
          </div>
        </div>
      </>
    );
  }

  const org = orgs?.items.find((o) => o.id === ws.org_id);

  return (
    <>
      <PageHeader
        title={ws.display_name ?? ws.slug}
        description={`Workspace in org ${org?.slug ?? ws.org_id.slice(0, 8)}`}
        testId="heading-workspace-detail"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="workspace-detail-body">
        <div className="mb-4">
          <Link
            href="/iam/workspaces"
            className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            ← Back to workspaces
          </Link>
        </div>

        <section
          className="mb-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950"
          data-testid="ws-detail-info"
        >
          <div className="mb-4 flex flex-wrap gap-1.5">
            <Badge tone={ws.is_active ? "emerald" : "zinc"}>
              {ws.is_active ? "active" : "inactive"}
            </Badge>
            <Badge tone="zinc">
              org: {org?.slug ?? `${ws.org_id.slice(0, 8)}…`}
            </Badge>
            <Badge tone="zinc">created {ws.created_at.slice(0, 10)}</Badge>
          </div>

          <form
            onSubmit={form.handleSubmit(onSave)}
            className="flex flex-col gap-4"
            data-testid="ws-edit-form"
          >
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
              label="Display name"
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

            <div className="flex justify-between gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
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
                loading={update.isPending}
                disabled={!form.formState.isDirty}
                data-testid="ws-edit-save"
              >
                Save changes
              </Button>
            </div>
          </form>
        </section>

        <WorkspaceMembers workspaceId={ws.id} orgId={ws.org_id} />
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
