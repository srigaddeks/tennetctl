"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Badge, Button, Field, Input, Select, Textarea } from "@/components/ui";
import { useCreateFlag } from "@/features/featureflags/hooks/use-flags";
import { useApplications } from "@/features/iam-applications/hooks/use-applications";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { FlagScope, FlagValueType } from "@/types/api";

const FLAG_KEY = /^[a-z][a-z0-9_]{1,62}$/;

const createSchema = z
  .object({
    scope: z.enum(["global", "org", "application"]),
    org_id: z.string().optional(),
    application_id: z.string().optional(),
    flag_key: z.string().regex(FLAG_KEY, "lowercase_snake_case"),
    value_type: z.enum(["boolean", "string", "number", "json"]),
    default_value_input: z.string(),
    description: z.string().optional(),
  })
  .superRefine((v, ctx) => {
    if (v.scope !== "global" && !v.org_id) {
      ctx.addIssue({ code: "custom", path: ["org_id"], message: "required" });
    }
    if (v.scope === "application" && !v.application_id) {
      ctx.addIssue({
        code: "custom",
        path: ["application_id"],
        message: "required",
      });
    }
  });

type CreateForm = z.infer<typeof createSchema>;

function parseDefault(v: string, t: FlagValueType): unknown {
  if (t === "boolean") return v.trim().toLowerCase() === "true";
  if (t === "number") {
    const n = Number(v);
    if (Number.isNaN(n)) throw new Error("invalid number");
    return n;
  }
  if (t === "json") return JSON.parse(v);
  return v;
}

export function CreateFlagDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const { toast } = useToast();
  const create = useCreateFlag();
  const [step, setStep] = useState<"scope" | "details">("scope");
  const { data: orgs } = useOrgs({ limit: 500 });

  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      scope: "global",
      org_id: "",
      application_id: "",
      flag_key: "",
      value_type: "boolean",
      default_value_input: "false",
      description: "",
    },
  });

  const scope = form.watch("scope") as FlagScope;
  const orgId = form.watch("org_id");
  const valueType = form.watch("value_type") as FlagValueType;

  const { data: apps } = useApplications({
    limit: 500,
    org_id: orgId || undefined,
  });

  async function onSubmit(v: CreateForm) {
    try {
      const parsed = parseDefault(v.default_value_input, v.value_type);
      const flag = await create.mutateAsync({
        scope: v.scope,
        org_id: v.scope === "global" ? null : v.org_id || null,
        application_id: v.scope === "application" ? v.application_id || null : null,
        flag_key: v.flag_key,
        value_type: v.value_type,
        default_value: parsed,
        description: v.description || undefined,
      });
      toast(`Created flag "${flag.flag_key}"`, "success");
      onClose();
      router.push(`/feature-flags/${flag.id}`);
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New feature flag"
      description={
        step === "scope"
          ? "Pick where this flag applies."
          : "Configure the flag definition."
      }
      size="lg"
    >
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-5"
        data-testid="create-flag-form"
      >
        {step === "scope" && (
          <div className="grid gap-3 sm:grid-cols-3">
            {(
              [
                {
                  id: "global",
                  title: "Global",
                  tone: "amber",
                  desc: "Platform-wide. Every org and app can evaluate.",
                },
                {
                  id: "org",
                  title: "Org",
                  tone: "blue",
                  desc: "Scoped to one organisation.",
                },
                {
                  id: "application",
                  title: "Application",
                  tone: "purple",
                  desc: "Scoped to one application under an org.",
                },
              ] as const
            ).map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => {
                  form.setValue("scope", c.id);
                  setStep("details");
                }}
                className={cn(
                  "flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-4 text-left transition hover:border-zinc-900 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-100",
                  scope === c.id && "ring-2 ring-zinc-900 dark:ring-zinc-100"
                )}
                data-testid={`scope-${c.id}`}
              >
                <Badge tone={c.tone}>{c.title}</Badge>
                <p className="text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                  {c.desc}
                </p>
              </button>
            ))}
          </div>
        )}

        {step === "details" && (
          <>
            <div className="flex items-center justify-between rounded-md bg-zinc-50 px-3 py-2 text-xs dark:bg-zinc-900">
              <div>
                Scope:{" "}
                <Badge
                  tone={
                    scope === "global"
                      ? "amber"
                      : scope === "org"
                        ? "blue"
                        : "purple"
                  }
                >
                  {scope}
                </Badge>
              </div>
              <button
                type="button"
                onClick={() => setStep("scope")}
                className="text-xs font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
              >
                Change
              </button>
            </div>

            {scope !== "global" && (
              <Field
                label="Org"
                required
                error={form.formState.errors.org_id?.message}
              >
                <Select {...form.register("org_id")} data-testid="create-flag-org">
                  <option value="">Select org…</option>
                  {orgs?.items.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.display_name ?? o.slug} ({o.slug})
                    </option>
                  ))}
                </Select>
              </Field>
            )}
            {scope === "application" && (
              <Field
                label="Application"
                required
                error={form.formState.errors.application_id?.message}
              >
                <Select
                  {...form.register("application_id")}
                  data-testid="create-flag-app"
                >
                  <option value="">Select application…</option>
                  {apps?.items.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.label ?? a.code}
                    </option>
                  ))}
                </Select>
              </Field>
            )}

            <Field
              label="Flag key"
              required
              hint="lowercase_snake_case"
              error={form.formState.errors.flag_key?.message}
            >
              <Input
                placeholder="new_checkout_flow"
                autoFocus
                {...form.register("flag_key")}
                data-testid="create-flag-key"
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Value type" required>
                <Select {...form.register("value_type")} data-testid="create-flag-type">
                  <option value="boolean">boolean</option>
                  <option value="string">string</option>
                  <option value="number">number</option>
                  <option value="json">json</option>
                </Select>
              </Field>
              <Field
                label="Default value"
                required
                hint={
                  valueType === "boolean"
                    ? "true or false"
                    : valueType === "json"
                      ? "JSON literal"
                      : valueType === "number"
                        ? "numeric"
                        : "text"
                }
                error={form.formState.errors.default_value_input?.message}
              >
                {valueType === "boolean" ? (
                  <Select {...form.register("default_value_input")}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                  </Select>
                ) : (
                  <Input
                    {...form.register("default_value_input")}
                    placeholder={
                      valueType === "json" ? '{"variant":"A"}' : ""
                    }
                    data-testid="create-flag-default"
                  />
                )}
              </Field>
            </div>

            <Field label="Description" hint="optional">
              <Textarea rows={2} {...form.register("description")} />
            </Field>

            <div className="flex justify-end gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
              <Button variant="secondary" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                loading={create.isPending}
                data-testid="create-flag-submit"
              >
                Create flag
              </Button>
            </div>
          </>
        )}
      </form>
    </Modal>
  );
}
