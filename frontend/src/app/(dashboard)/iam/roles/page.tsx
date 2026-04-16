"use client";

import { zodResolver } from "@hookform/resolvers/zod";
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
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import {
  useCreateRole,
  useDeleteRole,
  useRole,
  useRoles,
  useUpdateRole,
} from "@/features/iam-roles/hooks/use-roles";
import { ApiClientError } from "@/lib/api";

const CODE = /^[a-z][a-z0-9_]{1,62}$/;

const createSchema = z.object({
  scope: z.enum(["global", "org"]),
  org_id: z.string().optional(),
  role_type: z.enum(["system", "custom"]),
  code: z.string().regex(CODE, "lowercase_snake_case"),
  label: z.string().min(1),
  description: z.string().optional(),
});
type CreateForm = z.infer<typeof createSchema>;

const updateSchema = z.object({
  label: z.string().min(1).optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});
type UpdateForm = z.infer<typeof updateSchema>;

export default function RolesPage() {
  const [filterOrg, setFilterOrg] = useState("");
  const [openCreate, setOpenCreate] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const { data: orgs } = useOrgs({ limit: 500 });
  const { data, isLoading, isError, error, refetch } = useRoles({
    limit: 200,
    org_id: filterOrg || undefined,
  });

  return (
    <>
      <PageHeader
        title="Roles"
        description="Named permission bundles. Global (org_id = NULL) or org-scoped. System = built-in, Custom = editable."
        testId="heading-roles"
        actions={
          <Button
            onClick={() => setOpenCreate(true)}
            data-testid="open-create-role"
          >
            + New role
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 flex items-center gap-2">
          <label className="text-xs text-zinc-500">Filter org</label>
          <Select
            value={filterOrg}
            onChange={(e) => setFilterOrg(e.target.value)}
            className="w-64"
          >
            <option value="">All (global + org-scoped)</option>
            {orgs?.items.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name ?? o.slug}
              </option>
            ))}
          </Select>
        </div>
        {isLoading && <Skeleton className="h-12 w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No roles"
            description="Create a role to define a permission bundle."
            action={<Button onClick={() => setOpenCreate(true)}>+ New role</Button>}
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Code</TH>
                <TH>Label</TH>
                <TH>Type</TH>
                <TH>Scope</TH>
                <TH>Status</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((r) => {
                const org = orgs?.items.find((o) => o.id === r.org_id);
                return (
                  <TR key={r.id} onClick={() => setSelected(r.id)}>
                    <TD>
                      <span className="font-mono text-xs">{r.code ?? "—"}</span>
                    </TD>
                    <TD>{r.label ?? "—"}</TD>
                    <TD>
                      <Badge tone={r.role_type === "system" ? "purple" : "blue"}>
                        {r.role_type}
                      </Badge>
                    </TD>
                    <TD>
                      {r.org_id ? (
                        <span className="text-xs text-zinc-500">
                          {org?.slug ?? r.org_id.slice(0, 8)}
                        </span>
                      ) : (
                        <Badge tone="amber">global</Badge>
                      )}
                    </TD>
                    <TD>
                      <Badge tone={r.is_active ? "emerald" : "zinc"}>
                        {r.is_active ? "active" : "inactive"}
                      </Badge>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </div>

      {openCreate && (
        <CreateRoleDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
          orgs={orgs?.items ?? []}
          defaultOrgId={filterOrg || null}
        />
      )}
      <RoleDetailDrawer
        roleId={selected}
        onClose={() => setSelected(null)}
      />
    </>
  );
}

function CreateRoleDialog({
  open,
  onClose,
  orgs,
  defaultOrgId,
}: {
  open: boolean;
  onClose: () => void;
  orgs: { id: string; slug: string; display_name: string | null }[];
  defaultOrgId: string | null;
}) {
  const { toast } = useToast();
  const create = useCreateRole();
  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      scope: defaultOrgId ? "org" : "global",
      org_id: defaultOrgId ?? "",
      role_type: "custom",
      code: "",
      label: "",
      description: "",
    },
  });
  const scope = form.watch("scope");

  useEffect(() => {
    if (open) form.reset(form.getValues());
  }, [open, form]);

  async function onSubmit(v: CreateForm) {
    try {
      const role = await create.mutateAsync({
        org_id: v.scope === "global" ? null : v.org_id || null,
        role_type: v.role_type,
        code: v.code,
        label: v.label,
        ...(v.description ? { description: v.description } : {}),
      });
      toast(`Created role ${role.code}`, "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New role">
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid="create-role-form"
      >
        <Field label="Scope" required>
          <Select
            {...form.register("scope")}
            data-testid="create-role-scope"
          >
            <option value="global">Global (no org)</option>
            <option value="org">Org-scoped</option>
          </Select>
        </Field>
        {scope === "org" && (
          <Field
            label="Org"
            required
            error={form.formState.errors.org_id?.message}
          >
            <Select
              {...form.register("org_id")}
              data-testid="create-role-org"
            >
              <option value="">Select org…</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name ?? o.slug}
                </option>
              ))}
            </Select>
          </Field>
        )}
        <Field label="Role type" required>
          <Select {...form.register("role_type")}>
            <option value="custom">Custom</option>
            <option value="system">System</option>
          </Select>
        </Field>
        <Field
          label="Code"
          required
          error={form.formState.errors.code?.message}
          hint="lowercase_snake_case"
        >
          <Input
            placeholder="platform_admin"
            {...form.register("code")}
            data-testid="create-role-code"
          />
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
        <Field label="Description" hint="optional">
          <Textarea rows={3} {...form.register("description")} />
        </Field>
        <div className="mt-2 flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-role-submit"
          >
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RoleDetailDrawer({
  roleId,
  onClose,
}: {
  roleId: string | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const { data: role, isLoading } = useRole(roleId);
  const update = useUpdateRole();
  const del = useDeleteRole();

  const form = useForm<UpdateForm>({
    resolver: zodResolver(updateSchema),
    defaultValues: { label: "", description: "", is_active: true },
  });

  useEffect(() => {
    if (role) {
      form.reset({
        label: role.label ?? "",
        description: role.description ?? "",
        is_active: role.is_active,
      });
    }
  }, [role, form]);

  async function onSubmit(v: UpdateForm) {
    if (!roleId) return;
    const dirty = form.formState.dirtyFields;
    const body: UpdateForm = {};
    if (dirty.label) body.label = v.label;
    if (dirty.description) body.description = v.description;
    if (dirty.is_active) body.is_active = v.is_active;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: roleId, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function onDelete() {
    if (!roleId) return;
    if (!confirm(`Delete role "${role?.code ?? roleId}"?`)) return;
    try {
      await del.mutateAsync(roleId);
      toast("Deleted", "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={roleId !== null}
      onClose={onClose}
      title={role?.label ?? "Role"}
      description={role?.code ?? undefined}
    >
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {role && (
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <div className="flex flex-wrap gap-1.5">
            <Badge tone={role.role_type === "system" ? "purple" : "blue"}>
              {role.role_type}
            </Badge>
            {!role.org_id && <Badge tone="amber">global</Badge>}
            <Badge tone={role.is_active ? "emerald" : "zinc"}>
              {role.is_active ? "active" : "inactive"}
            </Badge>
          </div>
          <Field label="Code" hint="frozen">
            <Input disabled value={role.code ?? ""} />
          </Field>
          <Field label="Label" error={form.formState.errors.label?.message}>
            <Input {...form.register("label")} />
          </Field>
          <Field label="Description">
            <Textarea rows={3} {...form.register("description")} />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...form.register("is_active")} />
            Active
          </label>
          <div className="mt-2 flex justify-between border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <Button
              variant="danger"
              type="button"
              size="sm"
              onClick={onDelete}
              loading={del.isPending}
            >
              Delete
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" type="button" onClick={onClose}>
                Close
              </Button>
              <Button
                type="submit"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
              >
                Save
              </Button>
            </div>
          </div>
        </form>
      )}
    </Modal>
  );
}
