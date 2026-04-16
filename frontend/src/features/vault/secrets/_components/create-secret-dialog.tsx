"use client";

/**
 * Create-secret dialog.
 *
 * Scope picker lets the user choose global / org / workspace at create time.
 * Org ID / workspace ID fields appear conditionally. Value is held in a useRef
 * until the reveal-once dialog dismisses (reveal-once pattern — see ADR-028).
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Field, Input, Select, Textarea } from "@/components/ui";
import { RevealOnceDialog } from "@/features/vault/secrets/_components/reveal-once-dialog";
import { useCreateSecret } from "@/features/vault/secrets/hooks/use-secrets";
import {
  secretCreateSchema,
  type SecretCreateForm,
} from "@/features/vault/secrets/schema";
import { ApiClientError } from "@/lib/api";
import type { VaultScope } from "@/types/api";

export function CreateSecretDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateSecret();
  const revealRef = useRef<{ key: string; value: string } | null>(null);
  const [revealOpen, setRevealOpen] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<SecretCreateForm>({
    resolver: zodResolver(secretCreateSchema),
    defaultValues: {
      key: "",
      value: "",
      description: "",
      scope: "global" as VaultScope,
      org_id: "",
      workspace_id: "",
    },
    mode: "onChange",
  });

  const scope = form.watch("scope");

  async function onSubmit(values: SecretCreateForm) {
    setServerError(null);
    try {
      const body = {
        key: values.key,
        value: values.value,
        description: values.description ? values.description : null,
        scope: values.scope,
        org_id: values.scope === "global" ? null : values.org_id || null,
        workspace_id:
          values.scope === "workspace" ? values.workspace_id || null : null,
      };
      await create.mutateAsync(body);
      revealRef.current = { key: values.key, value: values.value };
      toast(`Created secret "${values.key}"`, "success");
      form.reset();
      onClose();
      setRevealOpen(true);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      setServerError(msg);
    }
  }

  function dismissReveal() {
    revealRef.current = null;
    setRevealOpen(false);
  }

  return (
    <>
      <Modal
        open={open}
        onClose={() => {
          form.reset();
          setServerError(null);
          onClose();
        }}
        title="New secret"
        description="Envelope-encrypted. The value is shown exactly once after create."
        size="md"
      >
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
          data-testid="create-secret-form"
        >
          <Field
            label="Key"
            required
            hint="lowercase + . - _"
            error={form.formState.errors.key?.message}
            htmlFor="new-secret-key"
          >
            <Input
              id="new-secret-key"
              placeholder="auth.argon2.pepper"
              autoFocus
              data-testid="new-secret-key"
              {...form.register("key")}
            />
          </Field>

          <Field
            label="Scope"
            required
            hint="who can read this secret"
            error={form.formState.errors.scope?.message}
            htmlFor="new-secret-scope"
          >
            <Select
              id="new-secret-scope"
              data-testid="new-secret-scope"
              {...form.register("scope")}
            >
              <option value="global">Global — platform-wide</option>
              <option value="org">Org — scoped to one org</option>
              <option value="workspace">Workspace — scoped to one workspace</option>
            </Select>
          </Field>

          {(scope === "org" || scope === "workspace") && (
            <Field
              label="Org ID"
              required
              error={form.formState.errors.org_id?.message}
              htmlFor="new-secret-org-id"
            >
              <Input
                id="new-secret-org-id"
                placeholder="uuid of the org"
                data-testid="new-secret-org-id"
                {...form.register("org_id")}
              />
            </Field>
          )}

          {scope === "workspace" && (
            <Field
              label="Workspace ID"
              required
              error={form.formState.errors.workspace_id?.message}
              htmlFor="new-secret-workspace-id"
            >
              <Input
                id="new-secret-workspace-id"
                placeholder="uuid of the workspace"
                data-testid="new-secret-workspace-id"
                {...form.register("workspace_id")}
              />
            </Field>
          )}

          <Field
            label="Value"
            required
            error={form.formState.errors.value?.message}
            htmlFor="new-secret-value"
          >
            <Textarea
              id="new-secret-value"
              placeholder="paste or type the secret value"
              rows={4}
              autoComplete="off"
              data-testid="new-secret-value"
              {...form.register("value")}
            />
          </Field>
          <Field
            label="Description"
            hint="optional — purpose of this secret"
            error={form.formState.errors.description?.message}
            htmlFor="new-secret-description"
          >
            <Input
              id="new-secret-description"
              placeholder="Argon2 pepper for password hashing"
              data-testid="new-secret-description"
              {...form.register("description")}
            />
          </Field>

          {serverError && (
            <div
              className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
              data-testid="new-secret-error"
            >
              {serverError}
            </div>
          )}

          <div className="mt-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                form.reset();
                setServerError(null);
                onClose();
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={create.isPending}
              data-testid="new-secret-submit"
            >
              Create secret
            </Button>
          </div>
        </form>
      </Modal>

      <RevealOnceDialog
        open={revealOpen}
        secretKey={revealRef.current?.key ?? ""}
        value={revealRef.current?.value ?? ""}
        onDismiss={dismissReveal}
      />
    </>
  );
}
