"use client";

/**
 * Create-config dialog.
 *
 * Configs are plaintext — no reveal-once orchestration. value_type picks the
 * validation; value is entered as a string and parsed on submit.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Field, Input, Select, Textarea } from "@/components/ui";
import { useCreateConfig } from "@/features/vault/configs/hooks/use-configs";
import {
  configCreateSchema,
  parseValue,
  type ConfigCreateForm,
} from "@/features/vault/configs/schema";
import { ApiClientError } from "@/lib/api";

export function CreateConfigDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateConfig();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<ConfigCreateForm>({
    resolver: zodResolver(configCreateSchema),
    defaultValues: {
      key: "",
      value_type: "string",
      value_raw: "",
      description: "",
      scope: "global",
      org_id: "",
      workspace_id: "",
    },
    mode: "onChange",
  });

  const scope = form.watch("scope");
  const valueType = form.watch("value_type");

  async function onSubmit(values: ConfigCreateForm) {
    setServerError(null);
    try {
      const body = {
        key: values.key,
        value_type: values.value_type,
        value: parseValue(values.value_raw, values.value_type),
        description: values.description ? values.description : null,
        scope: values.scope,
        org_id: values.scope === "global" ? null : values.org_id || null,
        workspace_id:
          values.scope === "workspace" ? values.workspace_id || null : null,
      };
      await create.mutateAsync(body);
      toast(`Created config "${values.key}"`, "success");
      form.reset();
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
        form.reset();
        setServerError(null);
        onClose();
      }}
      title="New config"
      description="Plaintext typed config. Unlike secrets, configs are always viewable + editable."
      size="md"
    >
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid="create-config-form"
      >
        <Field
          label="Key"
          required
          hint="lowercase + . - _"
          error={form.formState.errors.key?.message}
          htmlFor="new-config-key"
        >
          <Input
            id="new-config-key"
            placeholder="rate_limit.per_minute"
            autoFocus
            data-testid="new-config-key"
            {...form.register("key")}
          />
        </Field>

        <Field
          label="Type"
          required
          error={form.formState.errors.value_type?.message}
          htmlFor="new-config-type"
        >
          <Select
            id="new-config-type"
            data-testid="new-config-type"
            {...form.register("value_type")}
          >
            <option value="string">string</option>
            <option value="boolean">boolean</option>
            <option value="number">number</option>
            <option value="json">json</option>
          </Select>
        </Field>

        <Field
          label="Value"
          required
          hint={
            valueType === "boolean"
              ? "true or false"
              : valueType === "number"
                ? "integer or float"
                : valueType === "json"
                  ? "valid JSON object or array"
                  : "free-text string"
          }
          error={form.formState.errors.value_raw?.message}
          htmlFor="new-config-value"
        >
          {valueType === "json" ? (
            <Textarea
              id="new-config-value"
              rows={4}
              className="font-mono text-xs"
              placeholder={'{"key": "value"}'}
              data-testid="new-config-value"
              {...form.register("value_raw")}
            />
          ) : (
            <Input
              id="new-config-value"
              placeholder={
                valueType === "boolean"
                  ? "true"
                  : valueType === "number"
                    ? "60"
                    : "hello world"
              }
              data-testid="new-config-value"
              {...form.register("value_raw")}
            />
          )}
        </Field>

        <Field
          label="Scope"
          required
          error={form.formState.errors.scope?.message}
          htmlFor="new-config-scope"
        >
          <Select
            id="new-config-scope"
            data-testid="new-config-scope"
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
            htmlFor="new-config-org-id"
          >
            <Input
              id="new-config-org-id"
              placeholder="uuid of the org"
              data-testid="new-config-org-id"
              {...form.register("org_id")}
            />
          </Field>
        )}

        {scope === "workspace" && (
          <Field
            label="Workspace ID"
            required
            error={form.formState.errors.workspace_id?.message}
            htmlFor="new-config-workspace-id"
          >
            <Input
              id="new-config-workspace-id"
              placeholder="uuid of the workspace"
              data-testid="new-config-workspace-id"
              {...form.register("workspace_id")}
            />
          </Field>
        )}

        <Field
          label="Description"
          hint="optional — purpose of this config"
          error={form.formState.errors.description?.message}
          htmlFor="new-config-description"
        >
          <Input
            id="new-config-description"
            placeholder="per-request rate limit"
            data-testid="new-config-description"
            {...form.register("description")}
          />
        </Field>

        {serverError && (
          <div
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300"
            data-testid="new-config-error"
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
            data-testid="new-config-submit"
          >
            Create config
          </Button>
        </div>
      </form>
    </Modal>
  );
}
