"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2, Users } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { ConfirmDialog } from "@/components/confirm-dialog";
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
import {
  useCreateGroup,
  useDeleteGroup,
  useGroups,
  useUpdateGroup,
} from "@/features/iam-groups/hooks/use-groups";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { ApiClientError } from "@/lib/api";
import type { Group } from "@/types/api";

const createSchema = z.object({
  org_id: z.string().min(1, "Organisation required"),
  code: z.string().min(1, "Code required").regex(/^[a-z0-9_-]+$/, "Lowercase + _ and - only").max(64),
  label: z.string().min(1, "Label required").max(128),
  description: z.string().max(512).optional(),
});
type CreateForm = z.infer<typeof createSchema>;

const editSchema = z.object({
  label: z.string().min(1).max(128),
  description: z.string().max(512).optional(),
  is_active: z.boolean(),
});
type EditForm = z.infer<typeof editSchema>;

export default function GroupsPage() {
  const { toast } = useToast();
  const [orgFilter, setOrgFilter] = useState<string>("");
  const [appFilter, setAppFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [openCreate, setOpenCreate] = useState(false);
  const [editGroup, setEditGroup] = useState<Group | null>(null);
  const [deleteGroup, setDeleteGroup] = useState<Group | null>(null);

  const { data, isLoading, isError, refetch } = useGroups({
    limit: 200,
    org_id: orgFilter || undefined,
  });
  const { data: orgsData } = useOrgs({ limit: 200 });
  const allOrgs = orgsData?.items ?? [];
  const orgMap = useMemo(
    () => Object.fromEntries(allOrgs.map((o) => [o.id, o.display_name ?? o.slug])),
    [allOrgs],
  );

  const createGroup = useCreateGroup();
  const updateGroup = useUpdateGroup();
  const deleteGroupMut = useDeleteGroup();

  const groups = data?.items ?? [];
  const filtered = search
    ? groups.filter(
        (g) =>
          g.code?.toLowerCase().includes(search.toLowerCase()) ||
          g.label?.toLowerCase().includes(search.toLowerCase()),
      )
    : groups;

  const total = groups.length;
  const active = groups.filter((g) => g.is_active).length;
  const inactive = total - active;

  const createForm = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: allOrgs[0]?.id ?? "",
      code: "",
      label: "",
      description: "",
    },
  });

  async function onCreateSubmit(values: CreateForm) {
    try {
      await createGroup.mutateAsync({
        org_id: values.org_id,
        code: values.code,
        label: values.label,
        description: values.description || undefined,
      });
      toast("Group created", "success");
      setOpenCreate(false);
      createForm.reset();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to create group";
      toast(msg, "error");
    }
  }

  const editForm = useForm<EditForm>({ resolver: zodResolver(editSchema) });

  function openEdit(g: Group) {
    editForm.reset({
      label: g.label ?? "",
      description: g.description ?? "",
      is_active: g.is_active,
    });
    setEditGroup(g);
  }

  async function onEditSubmit(values: EditForm) {
    if (!editGroup) return;
    try {
      await updateGroup.mutateAsync({
        id: editGroup.id,
        body: {
          label: values.label,
          description: values.description || undefined,
          is_active: values.is_active,
        },
      });
      toast("Group updated", "success");
      setEditGroup(null);
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to update";
      toast(msg, "error");
    }
  }

  async function onDeleteConfirm() {
    if (!deleteGroup) return;
    try {
      await deleteGroupMut.mutateAsync(deleteGroup.id);
      toast("Group deleted", "success");
      setDeleteGroup(null);
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : "Failed to delete";
      toast(msg, "error");
    }
  }

  return (
    <>
      <PageHeader
        title="Groups"
        description="Org-scoped user collections. Bulk-assign roles to many users at once. Groups are immutable on the roster layer — revoke = delete."
        testId="heading-groups"
        actions={
          <Button onClick={() => setOpenCreate(true)}>
            <Plus size={14} className="mr-1.5" />
            New group
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in">
        <div className="mb-6 grid grid-cols-3 gap-4">
          <StatCard label="Total Groups" value={total} sub="all groups" accent="blue" />
          <StatCard label="Active" value={active} sub="accepting members" accent="green" />
          <StatCard label="Inactive" value={inactive} sub="archived or disabled" accent="amber" />
        </div>

        <div className="mb-5">
          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Scope groups to application"
          />
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="label-caps" style={{ color: "var(--text-muted)" }}>ORG</span>
            <Select
              value={orgFilter}
              onChange={(e) => setOrgFilter(e.target.value)}
              className="w-52"
              data-testid="filter-group-org"
            >
              <option value="">All orgs</option>
              {allOrgs.map((o) => (
                <option key={o.id} value={o.id}>{o.display_name ?? o.slug}</option>
              ))}
            </Select>
          </div>
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by code or label…"
            className="w-64"
            data-testid="filter-group-search"
          />
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-14" />)}
          </div>
        ) : isError ? (
          <ErrorState message="Failed to load groups" retry={refetch} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={search ? "No matches" : "No groups yet"}
            description={
              search
                ? "Try a different filter or create a new group."
                : "Create your first group to bulk-assign roles to multiple users at once."
            }
            action={
              <Button onClick={() => setOpenCreate(true)}>
                <Plus size={14} className="mr-1.5" />
                New group
              </Button>
            }
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Group</TH>
                <TH>Code</TH>
                <TH>Org</TH>
                <TH>Status</TH>
                <TH className="text-right">Actions</TH>
              </TR>
            </THead>
            <TBody>
              {filtered.map((g) => (
                <TR key={g.id} data-testid={`group-row-${g.id}`}>
                  <TD>
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-md bg-[var(--bg-elevated)] border border-[var(--border)] flex items-center justify-center">
                        <Users size={13} className="text-[var(--text-muted)]" />
                      </div>
                      <div>
                        <div className="font-semibold text-sm text-[var(--text-primary)]">
                          {g.label ?? "—"}
                        </div>
                        {g.description && (
                          <div className="text-[11px] text-[var(--text-muted)] truncate max-w-md">
                            {g.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </TD>
                  <TD>
                    <code className="font-mono-data text-[11px] text-[var(--text-secondary)]">{g.code}</code>
                  </TD>
                  <TD>
                    <span className="text-xs text-[var(--text-muted)]">
                      {orgMap[g.org_id] ?? g.org_id.slice(0, 8)}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone={g.is_active ? "success" : "warning"}>
                      {g.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </TD>
                  <TD className="text-right">
                    <div className="inline-flex gap-2">
                      <Button size="sm" variant="secondary" onClick={() => openEdit(g)}>
                        Edit
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => setDeleteGroup(g)}>
                        <Trash2 size={12} />
                      </Button>
                    </div>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <Modal
        open={openCreate}
        onClose={() => { setOpenCreate(false); createForm.reset(); }}
        title="New Group"
        description="Create an org-scoped user group for bulk role assignment."
      >
        <form onSubmit={createForm.handleSubmit(onCreateSubmit)} className="space-y-4">
          <Field label="Organisation" error={createForm.formState.errors.org_id?.message}>
            <Select {...createForm.register("org_id")}>
              {allOrgs.map((o) => (
                <option key={o.id} value={o.id}>{o.display_name ?? o.slug}</option>
              ))}
            </Select>
          </Field>
          <Field label="Code" hint="Lowercase alphanumeric + _ and -" error={createForm.formState.errors.code?.message}>
            <Input placeholder="e.g. engineering" {...createForm.register("code")} />
          </Field>
          <Field label="Label" error={createForm.formState.errors.label?.message}>
            <Input placeholder="e.g. Engineering" {...createForm.register("label")} />
          </Field>
          <Field label="Description (optional)">
            <Textarea rows={2} placeholder="What is this group for?" {...createForm.register("description")} />
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => { setOpenCreate(false); createForm.reset(); }}>
              Cancel
            </Button>
            <Button type="submit" loading={createGroup.isPending}>
              Create group
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={!!editGroup}
        onClose={() => setEditGroup(null)}
        title={`Edit ${editGroup?.label ?? "group"}`}
      >
        <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
          <Field label="Label" error={editForm.formState.errors.label?.message}>
            <Input {...editForm.register("label")} />
          </Field>
          <Field label="Description">
            <Textarea rows={2} {...editForm.register("description")} />
          </Field>
          <Field label="Status">
            <Select {...editForm.register("is_active", { setValueAs: (v) => v === "true" })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setEditGroup(null)}>Cancel</Button>
            <Button type="submit" loading={updateGroup.isPending}>Save changes</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!deleteGroup}
        title={`Delete ${deleteGroup?.label ?? "group"}?`}
        description={`This will remove "${deleteGroup?.label ?? deleteGroup?.code}". Members are NOT deleted. This cannot be undone.`}
        confirmLabel="Delete"
        tone="danger"
        onConfirm={onDeleteConfirm}
        onClose={() => setDeleteGroup(null)}
        loading={deleteGroupMut.isPending}
      />
    </>
  );
}
