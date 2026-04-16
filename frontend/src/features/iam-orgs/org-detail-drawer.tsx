"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Badge, Button, Field, Input } from "@/components/ui";
import {
  useDeleteOrg,
  useOrg,
  useUpdateOrg,
} from "@/features/iam-orgs/hooks/use-orgs";
import {
  orgUpdateSchema,
  type OrgUpdateForm,
} from "@/features/iam-orgs/schema";
import { ApiClientError } from "@/lib/api";

export function OrgDetailDrawer({
  orgId,
  onClose,
}: {
  orgId: string | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const { data: org, isLoading } = useOrg(orgId);
  const update = useUpdateOrg();
  const del = useDeleteOrg();

  const form = useForm<OrgUpdateForm>({
    resolver: zodResolver(orgUpdateSchema),
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

  async function onSubmit(values: OrgUpdateForm) {
    if (!orgId) return;
    const dirty = form.formState.dirtyFields;
    const body: OrgUpdateForm = {};
    if (dirty.slug) body.slug = values.slug;
    if (dirty.display_name) body.display_name = values.display_name;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: orgId, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function onDelete() {
    if (!orgId) return;
    if (!confirm(`Soft-delete org "${org?.slug ?? orgId}"?`)) return;
    try {
      await del.mutateAsync(orgId);
      toast("Deleted", "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={orgId !== null}
      onClose={onClose}
      title={org?.display_name ?? "Organisation"}
      description={org ? `Created ${org.created_at.slice(0, 10)}` : undefined}
      size="md"
    >
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {org && (
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
          data-testid="edit-org-form"
        >
          <div className="flex flex-wrap gap-1.5">
            <Badge tone={org.is_active ? "emerald" : "zinc"}>
              {org.is_active ? "active" : "inactive"}
            </Badge>
            {org.is_test && <Badge tone="amber">test</Badge>}
            <Badge tone="zinc">id: {org.id.slice(0, 8)}…</Badge>
          </div>
          <Field
            label="Slug"
            error={form.formState.errors.slug?.message}
            htmlFor="edit-org-slug"
          >
            <Input
              id="edit-org-slug"
              {...form.register("slug")}
              data-testid="edit-org-slug"
            />
          </Field>
          <Field
            label="Display name"
            error={form.formState.errors.display_name?.message}
            htmlFor="edit-org-display-name"
          >
            <Input
              id="edit-org-display-name"
              {...form.register("display_name")}
              data-testid="edit-org-display-name"
            />
          </Field>
          <div className="mt-2 flex items-center justify-between gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <Button
              variant="danger"
              type="button"
              size="sm"
              onClick={onDelete}
              loading={del.isPending}
              data-testid="delete-org"
            >
              Delete
            </Button>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                type="button"
                onClick={onClose}
              >
                Close
              </Button>
              <Button
                type="submit"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
                data-testid="save-org"
              >
                Save changes
              </Button>
            </div>
          </div>
        </form>
      )}
    </Modal>
  );
}
