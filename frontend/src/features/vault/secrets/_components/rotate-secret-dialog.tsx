"use client";

/**
 * Rotate-secret dialog. Same reveal-once orchestration as create.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Field, Textarea } from "@/components/ui";
import { RevealOnceDialog } from "@/features/vault/secrets/_components/reveal-once-dialog";
import {
  useRotateSecret,
  type SecretIdentity,
} from "@/features/vault/secrets/hooks/use-secrets";
import {
  secretRotateSchema,
  type SecretRotateForm,
} from "@/features/vault/secrets/schema";
import { ApiClientError } from "@/lib/api";

export function RotateSecretDialog({
  open,
  identity,
  onClose,
}: {
  open: boolean;
  identity: SecretIdentity;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const rotate = useRotateSecret(identity);
  const revealRef = useRef<{ key: string; value: string } | null>(null);
  const [revealOpen, setRevealOpen] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<SecretRotateForm>({
    resolver: zodResolver(secretRotateSchema),
    defaultValues: { value: "", description: "" },
    mode: "onChange",
  });

  async function onSubmit(values: SecretRotateForm) {
    setServerError(null);
    try {
      const body = {
        value: values.value,
        description: values.description ? values.description : null,
      };
      const secret = await rotate.mutateAsync(body);
      revealRef.current = { key: identity.key, value: values.value };
      toast(`Rotated to v${secret.version}`, "success");
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
        title={`Rotate "${identity.key}"`}
        description="New value is envelope-encrypted, version bumps, and the new value is shown exactly once."
        size="md"
      >
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
          data-testid={`rotate-secret-form-${identity.key}`}
        >
          <Field
            label="New value"
            required
            error={form.formState.errors.value?.message}
            htmlFor={`rotate-secret-value-${identity.key}`}
          >
            <Textarea
              id={`rotate-secret-value-${identity.key}`}
              placeholder="paste or type the new value"
              rows={4}
              autoFocus
              autoComplete="off"
              data-testid={`rotate-secret-value-${identity.key}`}
              {...form.register("value")}
            />
          </Field>

          {serverError && (
            <div
              className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
              data-testid={`rotate-secret-error-${identity.key}`}
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
              loading={rotate.isPending}
              data-testid={`rotate-secret-submit-${identity.key}`}
            >
              Rotate
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
