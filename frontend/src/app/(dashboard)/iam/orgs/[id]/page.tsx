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
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useDeleteOrg,
  useOrg,
  useUpdateOrg,
} from "@/features/iam-orgs/hooks/use-orgs";
import { useWorkspaces } from "@/features/iam-workspaces/hooks/use-workspaces";
import { ApiClientError } from "@/lib/api";

const SLUG = /^[a-z][a-z0-9-]{1,62}$/;

const editSchema = z.object({
  slug: z.string().regex(SLUG, "invalid slug"),
  display_name: z.string().min(1, "required"),
});
type EditForm = z.infer<typeof editSchema>;

export default function OrgDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orgId = typeof params.id === "string" ? params.id : "";
  const { toast } = useToast();

  const { data: org, isLoading, isError, error } = useOrg(orgId);
  const update = useUpdateOrg();
  const del = useDeleteOrg();
  const { data: workspaces } = useWorkspaces({ limit: 500, org_id: orgId });

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState("");

  const form = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    defaultValues: { slug: "", display_name: "" },
  });

  useEffect(() => {
    if (org) {
      form.reset({
        slug: org.slug,
        display_name: org.display_name ?? "",
      });
    }
  }, [org, form]);

  async function onSave(values: EditForm) {
    if (!org) return;
    const dirty = form.formState.dirtyFields;
    const body: { slug?: string; display_name?: string } = {};
    if (dirty.slug) body.slug = values.slug;
    if (dirty.display_name) body.display_name = values.display_name;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: org.id, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function handleDelete() {
    if (!org) return;
    if (deleteConfirm !== org.slug) return;
    try {
      await del.mutateAsync(org.id);
      toast("Org deleted", "success");
      router.push("/iam/orgs");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    } finally {
      setDeleteOpen(false);
      setDeleteConfirm("");
    }
  }

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Org"
          description="Loading…"
          testId="heading-org-detail"
        />
        <div className="px-8 py-6">
          <Skeleton className="mb-3 h-6 w-48" />
          <Skeleton className="mb-3 h-6 w-72" />
          <Skeleton className="h-6 w-32" />
        </div>
      </>
    );
  }

  if (isError || !org) {
    return (
      <>
        <PageHeader
          title="Org"
          description="Not found"
          testId="heading-org-detail"
        />
        <div className="px-8 py-6">
          <ErrorState
            message={
              error instanceof Error
                ? error.message
                : "Org not found or you don't have access."
            }
          />
          <div className="mt-4">
            <Link
              href="/iam/orgs"
              className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              ← Back to orgs
            </Link>
          </div>
        </div>
      </>
    );
  }

  const wsItems = workspaces?.items ?? [];

  return (
    <>
      <PageHeader
        title={org.display_name ?? org.slug}
        description={`Organisation · ${org.slug}`}
        testId="heading-org-detail"
        breadcrumbs={[
          { label: "Identity", href: "/iam/orgs" },
          { label: "Orgs", href: "/iam/orgs" },
          { label: org.display_name ?? org.slug },
        ]}
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="org-detail-body">
        <section
          className="mb-6 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950"
          data-testid="org-detail-info"
        >
          <div className="mb-4 flex flex-wrap gap-1.5">
            <Badge tone={org.is_active ? "emerald" : "zinc"}>
              {org.is_active ? "active" : "inactive"}
            </Badge>
            <Badge tone="zinc">created {org.created_at.slice(0, 10)}</Badge>
            {org.is_test && <Badge tone="amber">test</Badge>}
          </div>

          <form
            onSubmit={form.handleSubmit(onSave)}
            className="flex flex-col gap-4"
            data-testid="org-edit-form"
          >
            <Field
              label="Slug"
              required
              error={form.formState.errors.slug?.message}
              htmlFor="org-edit-slug"
            >
              <Input
                id="org-edit-slug"
                {...form.register("slug")}
                data-testid="org-edit-slug"
              />
            </Field>
            <Field
              label="Display name"
              required
              error={form.formState.errors.display_name?.message}
              htmlFor="org-edit-display-name"
            >
              <Input
                id="org-edit-display-name"
                {...form.register("display_name")}
                data-testid="org-edit-display-name"
              />
            </Field>

            <div className="flex justify-between gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
              <Button
                variant="danger"
                type="button"
                size="sm"
                onClick={() => setDeleteOpen(true)}
                data-testid="org-delete-open"
              >
                Delete org
              </Button>
              <Button
                type="submit"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
                data-testid="org-edit-save"
              >
                Save changes
              </Button>
            </div>
          </form>
        </section>

        <section
          className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950"
          data-testid="org-workspaces-section"
        >
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
              Workspaces ({wsItems.length})
            </h2>
            <Link
              href={`/iam/workspaces?org_id=${org.id}`}
              className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              → Manage workspaces
            </Link>
          </div>
          {wsItems.length === 0 ? (
            <EmptyState
              title="No workspaces"
              description="This org has no workspaces yet."
            />
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH>Slug</TH>
                  <TH>Name</TH>
                  <TH>Status</TH>
                  <TH>Created</TH>
                </tr>
              </THead>
              <TBody>
                {wsItems.map((ws) => (
                  <TR
                    key={ws.id}
                    onClick={() => router.push(`/iam/workspaces/${ws.id}`)}
                    data-testid={`org-ws-row-${ws.id}`}
                  >
                    <TD>
                      <span className="font-mono text-xs">{ws.slug}</span>
                    </TD>
                    <TD>
                      {ws.display_name ?? <span className="text-zinc-400">—</span>}
                    </TD>
                    <TD>
                      <Badge tone={ws.is_active ? "emerald" : "zinc"}>
                        {ws.is_active ? "active" : "inactive"}
                      </Badge>
                    </TD>
                    <TD>
                      <span className="text-xs text-zinc-500">
                        {ws.created_at.slice(0, 10)}
                      </span>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>
      </div>

      <Modal
        open={deleteOpen}
        onClose={() => {
          setDeleteOpen(false);
          setDeleteConfirm("");
        }}
        title={`Delete org "${org.slug}"?`}
        description="This soft-deletes the org. Workspaces and memberships under this org are retained but the org itself is hidden from active listings."
      >
        <div className="flex flex-col gap-4">
          <Field
            label={`Type the slug "${org.slug}" to confirm`}
            htmlFor="org-delete-confirm-input"
          >
            <Input
              id="org-delete-confirm-input"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              placeholder={org.slug}
              data-testid="org-delete-confirm-input"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              type="button"
              onClick={() => {
                setDeleteOpen(false);
                setDeleteConfirm("");
              }}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              type="button"
              disabled={deleteConfirm !== org.slug}
              loading={del.isPending}
              onClick={handleDelete}
              data-testid="org-delete-confirm-submit"
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
