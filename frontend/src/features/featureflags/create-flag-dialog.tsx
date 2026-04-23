"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Globe, Building2, Package, ChevronLeft } from "lucide-react";

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

const SCOPE_OPTIONS = [
  {
    id: "global" as const,
    title: "Global",
    tone: "amber" as const,
    icon: Globe,
    desc: "Platform-wide. Every org and application can evaluate this flag.",
    accentColor: "var(--warning)",
    accentMuted: "var(--warning-muted)",
  },
  {
    id: "org" as const,
    title: "Org",
    tone: "blue" as const,
    icon: Building2,
    desc: "Scoped to one organisation. Other orgs cannot see or evaluate it.",
    accentColor: "var(--accent)",
    accentMuted: "var(--accent-muted)",
  },
  {
    id: "application" as const,
    title: "Application",
    tone: "purple" as const,
    icon: Package,
    desc: "Scoped to one application under an org. Finest targeting granularity.",
    accentColor: "#a855f7",
    accentMuted: "#1a0533",
  },
];

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

  const selectedScopeMeta = SCOPE_OPTIONS.find((s) => s.id === scope)!;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New feature flag"
      description={
        step === "scope"
          ? "Choose the scope — this determines who can evaluate the flag."
          : "Configure the flag key, type, and default value."
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
            {SCOPE_OPTIONS.map((c) => {
              const isSelected = scope === c.id;
              return (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => {
                    form.setValue("scope", c.id);
                    setStep("details");
                  }}
                  className="flex flex-col gap-3 rounded-xl p-4 text-left transition"
                  style={{
                    background: isSelected ? c.accentMuted : "var(--bg-elevated)",
                    border: `1px solid ${isSelected ? c.accentColor : "var(--border)"}`,
                  }}
                  data-testid={`scope-${c.id}`}
                >
                  <div
                    className="flex h-8 w-8 items-center justify-center rounded-lg"
                    style={{
                      background: c.accentMuted,
                      border: `1px solid ${c.accentColor}`,
                    }}
                  >
                    <c.icon className="h-4 w-4" style={{ color: c.accentColor }} />
                  </div>
                  <div>
                    <div
                      className="text-sm font-semibold mb-1"
                      style={{ color: isSelected ? c.accentColor : "var(--text-primary)" }}
                    >
                      {c.title}
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                      {c.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {step === "details" && (
          <>
            {/* Scope indicator */}
            <div
              className="flex items-center justify-between rounded-lg px-3 py-2.5"
              style={{
                background: selectedScopeMeta.accentMuted,
                border: `1px solid ${selectedScopeMeta.accentColor}`,
              }}
            >
              <div className="flex items-center gap-2">
                <selectedScopeMeta.icon
                  className="h-3.5 w-3.5"
                  style={{ color: selectedScopeMeta.accentColor }}
                />
                <span className="text-xs font-medium" style={{ color: selectedScopeMeta.accentColor }}>
                  {selectedScopeMeta.title} scope
                </span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  — {selectedScopeMeta.desc}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setStep("scope")}
                className="flex items-center gap-1 text-xs font-medium transition hover:opacity-80"
                style={{ color: "var(--text-secondary)" }}
              >
                <ChevronLeft className="h-3 w-3" />
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
              hint="lowercase_snake_case · max 63 chars · e.g. new_checkout_flow"
              error={form.formState.errors.flag_key?.message}
            >
              <Input
                placeholder="new_checkout_flow"
                autoFocus
                {...form.register("flag_key")}
                data-testid="create-flag-key"
                style={{ fontFamily: "var(--font-mono)" }}
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Value type" required>
                <Select {...form.register("value_type")} data-testid="create-flag-type">
                  <option value="boolean">boolean — true / false</option>
                  <option value="string">string — text value</option>
                  <option value="number">number — numeric value</option>
                  <option value="json">json — structured object</option>
                </Select>
              </Field>
              <Field
                label="Default value"
                required
                hint={
                  valueType === "boolean"
                    ? "true or false"
                    : valueType === "json"
                      ? "valid JSON literal"
                      : valueType === "number"
                        ? "numeric (int or float)"
                        : "text string"
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
                    placeholder={valueType === "json" ? '{"variant":"A"}' : ""}
                    style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}
                    data-testid="create-flag-default"
                  />
                )}
              </Field>
            </div>

            <Field label="Description" hint="optional — helps teammates understand the flag's purpose">
              <Textarea rows={2} {...form.register("description")} />
            </Field>

            <div
              className="flex justify-end gap-2 pt-4"
              style={{ borderTop: "1px solid var(--border)" }}
            >
              <Button variant="secondary" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="primary"
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
