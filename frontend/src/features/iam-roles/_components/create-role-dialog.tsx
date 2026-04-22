"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, ShieldCheck, X } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { useToast } from "@/components/toast";
import {
  Button,
  Field,
  Input,
  Select,
  Textarea,
} from "@/components/ui";
import { useCreateRole } from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";

import { createSchema, slugify, type CreateForm } from "./constants";

export function CreateRoleDialog({
  open,
  onClose,
  orgs,
}: {
  open: boolean;
  onClose: () => void;
  orgs: { id: string; slug: string; display_name: string | null }[];
}) {
  const { toast } = useToast();
  const create = useCreateRole();

  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: "",
      role_type: "custom",
      code: "",
      label: "",
      description: "",
    },
  });

  const labelVal = form.watch("label");

  // Auto-generate code from label
  useEffect(() => {
    if (!form.formState.dirtyFields.code && labelVal) {
      form.setValue("code", slugify(labelVal), { shouldDirty: false });
    }
  }, [labelVal, form]);

  useEffect(() => {
    if (open) {
      form.reset({
        org_id: "",
        role_type: "custom",
        code: "",
        label: "",
        description: "",
      });
    }
  }, [open, form]);

  async function onSubmit(v: CreateForm) {
    try {
      const role = await create.mutateAsync({
        org_id: v.org_id || null,
        role_type: v.role_type,
        code: v.code,
        label: v.label,
        ...(v.description ? { description: v.description } : {}),
      });
      toast(`Created role "${role.code}"`, "success");
      onClose();
    } catch (err) {
      toast(err instanceof ApiClientError ? err.message : String(err), "error");
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-zinc-500" />
            <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
              New role
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4 p-6"
          data-testid="create-role-form"
        >
          {/* Org picker — optional, omit = platform */}
          <Field label="Org" hint="optional — omit for platform role">
            <Select
              {...form.register("org_id")}
              data-testid="create-role-org"
            >
              <option value="">— Platform (no org) —</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Role type">
            <Select {...form.register("role_type")}>
              <option value="custom">Custom</option>
              <option value="system">System</option>
            </Select>
          </Field>

          <Field
            label="Label"
            required
            error={form.formState.errors.label?.message}
          >
            <Input
              placeholder="Platform Admin"
              {...form.register("label")}
              data-testid="create-role-label"
            />
          </Field>

          <Field
            label="Code"
            required
            hint="lowercase_snake_case"
            error={form.formState.errors.code?.message}
          >
            <Input
              placeholder="platform_admin"
              {...form.register("code")}
              data-testid="create-role-code"
              className="font-mono"
            />
          </Field>

          <Field label="Description" hint="optional">
            <Textarea rows={2} {...form.register("description")} />
          </Field>

          <div className="flex justify-end gap-2 border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <Button type="button" variant="secondary" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              loading={create.isPending}
              data-testid="create-role-submit"
            >
              <Plus className="h-3.5 w-3.5" />
              Create role
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
