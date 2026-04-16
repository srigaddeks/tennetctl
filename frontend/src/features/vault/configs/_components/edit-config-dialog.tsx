"use client";

/**
 * Edit-config dialog. Patches value only (key / scope / type are immutable).
 * Description edit is a separate concern; deferred to a v0.3 polish.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Field, Input, Textarea } from "@/components/ui";
import { useUpdateConfig } from "@/features/vault/configs/hooks/use-configs";
import {
  configUpdateValueSchema,
  parseValue,
  stringifyValue,
  type ConfigUpdateValueForm,
} from "@/features/vault/configs/schema";
import { ApiClientError } from "@/lib/api";
import type { VaultConfigMeta } from "@/types/api";

export function EditConfigDialog({
  open,
  config,
  onClose,
}: {
  open: boolean;
  config: VaultConfigMeta;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const update = useUpdateConfig(config.id);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<ConfigUpdateValueForm>({
    resolver: zodResolver(configUpdateValueSchema),
    defaultValues: { value_raw: stringifyValue(config.value, config.value_type) },
    mode: "onChange",
  });

  useEffect(() => {
    if (open) {
      form.reset({ value_raw: stringifyValue(config.value, config.value_type) });
      setServerError(null);
    }
  }, [open, config.value, config.value_type, form]);

  async function onSubmit(values: ConfigUpdateValueForm) {
    setServerError(null);
    try {
      const body = {
        value: parseValue(values.value_raw, config.value_type),
      };
      await update.mutateAsync(body);
      toast(`Updated config "${config.key}"`, "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      setServerError(msg);
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        setServerError(null);
        onClose();
      }}
      title={`Edit "${config.key}"`}
      description={`Type: ${config.value_type}. Scope: ${config.scope}. Only value is editable; key / type / scope are immutable.`}
      size="md"
    >
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid={`edit-config-form-${config.id}`}
      >
        <Field
          label="Value"
          required
          error={form.formState.errors.value_raw?.message}
          htmlFor={`edit-config-value-${config.id}`}
        >
          {config.value_type === "json" ? (
            <Textarea
              id={`edit-config-value-${config.id}`}
              rows={6}
              className="font-mono text-xs"
              data-testid={`edit-config-value-${config.id}`}
              {...form.register("value_raw")}
            />
          ) : (
            <Input
              id={`edit-config-value-${config.id}`}
              data-testid={`edit-config-value-${config.id}`}
              {...form.register("value_raw")}
            />
          )}
        </Field>

        {serverError && (
          <div
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
            data-testid={`edit-config-error-${config.id}`}
          >
            {serverError}
          </div>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setServerError(null);
              onClose();
            }}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={update.isPending}
            data-testid={`edit-config-submit-${config.id}`}
          >
            Save
          </Button>
        </div>
      </form>
    </Modal>
  );
}
