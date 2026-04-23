"use client";

/**
 * Generic org-scoped resource UI — used for groups + applications.
 * Both have identical shape: org_id + code + label + description.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import {
  useEffect,
  useState,
  type ComponentType,
} from "react";
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
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { ApiClientError } from "@/lib/api";
import type { UseQueryResult } from "@tanstack/react-query";

const CODE = /^[a-z][a-z0-9_]{1,62}$/;

const createSchema = z.object({
  org_id: z.string().min(1),
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

type OrgScopedItem = {
  id: string;
  org_id: string;
  code: string | null;
  label: string | null;
  description: string | null;
  is_active: boolean;
};

export type OrgScopedListResult<T> = {
  items: T[];
  pagination: { total: number; limit: number; offset: number };
};

type CreateBody = {
  org_id: string;
  code: string;
  label: string;
  description?: string;
};

type UpdateBody = {
  label?: string;
  description?: string;
  is_active?: boolean;
};

export type OrgScopedHooks<T extends OrgScopedItem> = {
  useList: (p?: {
    limit?: number;
    org_id?: string | null;
  }) => UseQueryResult<OrgScopedListResult<T>>;
  useOne: (id: string | null) => UseQueryResult<T | null>;
  useCreate: () => { mutateAsync: (b: CreateBody) => Promise<T>; isPending: boolean };
  useUpdate: () => {
    mutateAsync: (v: { id: string; body: UpdateBody }) => Promise<T>;
    isPending: boolean;
  };
  useDelete: () => { mutateAsync: (id: string) => Promise<void>; isPending: boolean };
};

export function OrgScopedResourcePage<T extends OrgScopedItem>({
  title,
  description,
  resourceNoun,
  pageTestId,
  testPrefix,
  hooks,
}: {
  title: string;
  description: string;
  resourceNoun: string;
  pageTestId: string;
  testPrefix: string;
  hooks: OrgScopedHooks<T>;
}) {
  const [filterOrg, setFilterOrg] = useState("");
  const [openCreate, setOpenCreate] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const { data: orgs } = useOrgs({ limit: 500 });
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = hooks.useList({ limit: 200, org_id: filterOrg || undefined });

  const allItems = data?.items ?? [];
  const totalItems = allItems.length;
  const activeItems = allItems.filter((r) => r.is_active).length;
  const inactiveItems = allItems.filter((r) => !r.is_active).length;

  return (
    <>
      <PageHeader
        title={title}
        description={description}
        testId={pageTestId}
        actions={
          <Button
            variant="primary"
            onClick={() => setOpenCreate(true)}
            data-testid={`open-create-${testPrefix}`}
          >
            + New {resourceNoun}
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in">

        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard
              label={`Total ${title}`}
              value={totalItems}
              sub="all records"
              accent="blue"
            />
            <StatCard
              label="Active"
              value={activeItems}
              sub="currently enabled"
              accent="green"
            />
            <StatCard
              label="Inactive"
              value={inactiveItems}
              sub="disabled or archived"
              accent="red"
            />
          </div>
        )}

        {/* Filter bar */}
        <div className="mb-4 flex items-center gap-3">
          <span
            className="label-caps"
            style={{ color: "var(--text-muted)" }}
          >
            ORG
          </span>
          <Select
            value={filterOrg}
            onChange={(e) => setFilterOrg(e.target.value)}
            className="w-64"
          >
            <option value="">All orgs</option>
            {orgs?.items.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name ?? o.slug}
              </option>
            ))}
          </Select>
          {data && (
            <span
              className="ml-auto rounded px-2 py-0.5 text-xs font-mono"
              style={{
                background: "var(--bg-elevated)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border)",
              }}
            >
              {allItems.length} {resourceNoun}s
            </span>
          )}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {/* Empty */}
        {data && data.items.length === 0 && (
          <EmptyState
            title={`No ${resourceNoun}s`}
            description={`Create a ${resourceNoun} to get started.`}
            action={
              <Button variant="primary" onClick={() => setOpenCreate(true)}>
                + New {resourceNoun}
              </Button>
            }
          />
        )}

        {/* Table */}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Code</TH>
                <TH>Label</TH>
                <TH>Org</TH>
                <TH>Status</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((r) => {
                const org = orgs?.items.find((o) => o.id === r.org_id);
                return (
                  <TR key={r.id} onClick={() => setSelected(r.id)}>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--accent)" }}
                      >
                        {r.code ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span style={{ color: "var(--text-primary)" }}>
                        {r.label ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {org?.slug ?? r.org_id.slice(0, 8)}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={r.is_active ? "success" : "default"} dot={r.is_active}>
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
        <CreateOrgScopedDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
          resourceNoun={resourceNoun}
          orgs={orgs?.items ?? []}
          defaultOrgId={filterOrg || null}
          testPrefix={testPrefix}
          useCreate={hooks.useCreate}
        />
      )}
      <OrgScopedDetailDrawer
        id={selected}
        onClose={() => setSelected(null)}
        resourceNoun={resourceNoun}
        useOne={hooks.useOne}
        useUpdate={hooks.useUpdate}
        useDelete={hooks.useDelete}
      />
    </>
  );
}

function CreateOrgScopedDialog<T extends OrgScopedItem>({
  open,
  onClose,
  resourceNoun,
  orgs,
  defaultOrgId,
  testPrefix,
  useCreate,
}: {
  open: boolean;
  onClose: () => void;
  resourceNoun: string;
  orgs: { id: string; slug: string; display_name: string | null }[];
  defaultOrgId: string | null;
  testPrefix: string;
  useCreate: OrgScopedHooks<T>["useCreate"];
}) {
  const { toast } = useToast();
  const create = useCreate();
  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: defaultOrgId ?? "",
      code: "",
      label: "",
      description: "",
    },
  });

  useEffect(() => {
    if (open)
      form.reset({
        org_id: defaultOrgId ?? "",
        code: "",
        label: "",
        description: "",
      });
  }, [open, defaultOrgId, form]);

  async function onSubmit(v: CreateForm) {
    try {
      const item = await create.mutateAsync({
        org_id: v.org_id,
        code: v.code,
        label: v.label,
        ...(v.description ? { description: v.description } : {}),
      });
      toast(`Created ${resourceNoun} ${item.code}`, "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={`New ${resourceNoun}`}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid={`create-${testPrefix}-form`}
      >
        <Field
          label="Org"
          required
          error={form.formState.errors.org_id?.message}
        >
          <Select
            {...form.register("org_id")}
            data-testid={`create-${testPrefix}-org`}
          >
            <option value="">Select org…</option>
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name ?? o.slug}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Code"
          required
          error={form.formState.errors.code?.message}
          hint="lowercase_snake_case"
        >
          <Input
            {...form.register("code")}
            data-testid={`create-${testPrefix}-code`}
          />
        </Field>
        <Field
          label="Label"
          required
          error={form.formState.errors.label?.message}
        >
          <Input
            {...form.register("label")}
            data-testid={`create-${testPrefix}-label`}
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
            variant="primary"
            loading={create.isPending}
            data-testid={`create-${testPrefix}-submit`}
          >
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function OrgScopedDetailDrawer<T extends OrgScopedItem>({
  id,
  onClose,
  resourceNoun,
  useOne,
  useUpdate,
  useDelete,
}: {
  id: string | null;
  onClose: () => void;
  resourceNoun: string;
  useOne: OrgScopedHooks<T>["useOne"];
  useUpdate: OrgScopedHooks<T>["useUpdate"];
  useDelete: OrgScopedHooks<T>["useDelete"];
}) {
  const { toast } = useToast();
  const { data: item, isLoading } = useOne(id);
  const update = useUpdate();
  const del = useDelete();

  const form = useForm<UpdateForm>({
    resolver: zodResolver(updateSchema),
    defaultValues: { label: "", description: "", is_active: true },
  });

  useEffect(() => {
    if (item) {
      form.reset({
        label: item.label ?? "",
        description: item.description ?? "",
        is_active: item.is_active,
      });
    }
  }, [item, form]);

  async function onSubmit(v: UpdateForm) {
    if (!id) return;
    const dirty = form.formState.dirtyFields;
    const body: UpdateBody = {};
    if (dirty.label) body.label = v.label;
    if (dirty.description) body.description = v.description;
    if (dirty.is_active) body.is_active = v.is_active;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function onDelete() {
    if (!id) return;
    if (!confirm(`Delete ${resourceNoun} "${item?.code ?? id}"?`)) return;
    try {
      await del.mutateAsync(id);
      toast("Deleted", "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={id !== null}
      onClose={onClose}
      title={item?.label ?? resourceNoun}
      description={item?.code ?? undefined}
    >
      {isLoading && (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading…
        </p>
      )}
      {item && (
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <div className="flex flex-wrap gap-1.5">
            <Badge tone={item.is_active ? "success" : "default"} dot={item.is_active}>
              {item.is_active ? "active" : "inactive"}
            </Badge>
            <Badge tone="default">org: {item.org_id.slice(0, 8)}…</Badge>
          </div>
          <Field label="Code" hint="frozen">
            <Input disabled value={item.code ?? ""} />
          </Field>
          <Field label="Label" error={form.formState.errors.label?.message}>
            <Input {...form.register("label")} />
          </Field>
          <Field label="Description">
            <Textarea rows={3} {...form.register("description")} />
          </Field>
          <label
            className="flex items-center gap-2 text-sm"
            style={{ color: "var(--text-secondary)" }}
          >
            <input type="checkbox" {...form.register("is_active")} />
            Active
          </label>
          <div
            className="mt-2 flex justify-between pt-4"
            style={{ borderTop: "1px solid var(--border)" }}
          >
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
                variant="primary"
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

// Silence unused import (ComponentType reserved for future prop injection).
export type _Unused = ComponentType;
