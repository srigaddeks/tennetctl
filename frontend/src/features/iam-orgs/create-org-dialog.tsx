"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Field, Input } from "@/components/ui";
import { useCreateOrg } from "@/features/iam-orgs/hooks/use-orgs";
import {
  orgCreateSchema,
  type OrgCreateForm,
} from "@/features/iam-orgs/schema";
import { ApiClientError } from "@/lib/api";

export function CreateOrgDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateOrg();

  const form = useForm<OrgCreateForm>({
    resolver: zodResolver(orgCreateSchema),
    defaultValues: { slug: "", display_name: "" },
  });

  async function onSubmit(values: OrgCreateForm) {
    try {
      const org = await create.mutateAsync(values);
      toast(`Created org "${org.slug}"`, "success");
      form.reset();
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        form.reset();
        onClose();
      }}
      title="New organisation"
      description="Orgs are tenant boundaries — workspaces, users, and applications all nest under one."
      size="md"
    >
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid="create-org-form"
      >
        <Field
          label="Slug"
          required
          error={form.formState.errors.slug?.message}
          hint="URL-safe identifier"
          htmlFor="org-slug"
        >
          <Input
            id="org-slug"
            placeholder="acme"
            autoFocus
            data-testid="create-org-slug"
            {...form.register("slug")}
          />
        </Field>
        <Field
          label="Display name"
          required
          error={form.formState.errors.display_name?.message}
          htmlFor="org-display-name"
        >
          <Input
            id="org-display-name"
            placeholder="Acme, Inc."
            data-testid="create-org-display-name"
            {...form.register("display_name")}
          />
        </Field>
        <div className="mt-2 flex justify-end gap-2">
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              form.reset();
              onClose();
            }}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-org-submit"
          >
            Create org
          </Button>
        </div>
      </form>
    </Modal>
  );
}
