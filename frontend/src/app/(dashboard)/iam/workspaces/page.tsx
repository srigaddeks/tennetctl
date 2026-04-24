"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
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
} from "@/components/ui";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import {
  useCreateWorkspace,
  useWorkspaces,
} from "@/features/iam-workspaces/hooks/use-workspaces";
import { ApiClientError } from "@/lib/api";

const SLUG = /^[a-z][a-z0-9-]{1,62}$/;

const createSchema = z.object({
  org_id: z.string().min(1, "pick an org"),
  slug: z.string().regex(SLUG, "invalid slug"),
  display_name: z.string().min(1, "required"),
});
type CreateForm = z.infer<typeof createSchema>;

export default function WorkspacesPage() {
  const router = useRouter();
  const [filterOrgId, setFilterOrgId] = useState<string>("");
  const [appFilter, setAppFilter] = useState<string | null>(null);
  const [openCreate, setOpenCreate] = useState(false);

  const { data: orgs } = useOrgs({ limit: 500 });
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useWorkspaces({
    limit: 100,
    org_id: filterOrgId || undefined,
  });

  const allItems = data?.items ?? [];
  const totalWorkspaces = allItems.length;
  const activeWorkspaces = allItems.filter((w) => w.is_active).length;
  const inactiveWorkspaces = allItems.filter((w) => !w.is_active).length;

  return (
    <>
      <PageHeader
        title="Workspaces"
        description="Scoped work containers within an org. Slug unique per (org_id, slug)."
        testId="heading-workspaces"
        actions={
          <Button
            variant="primary"
            onClick={() => setOpenCreate(true)}
            data-testid="open-create-workspace"
          >
            + New workspace
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="workspaces-body">

        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard
              label="Total Workspaces"
              value={totalWorkspaces}
              sub={filterOrgId ? "in selected org" : "across all orgs"}
              accent="blue"
            />
            <StatCard
              label="Active"
              value={activeWorkspaces}
              sub="currently enabled"
              accent="green"
            />
            <StatCard
              label="Inactive"
              value={inactiveWorkspaces}
              sub="disabled or archived"
              accent="red"
            />
          </div>
        )}

        <div className="mb-5">
          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Scope workspaces to application"
          />
        </div>

        {/* Filter bar */}
        <div className="mb-4 flex items-center gap-3">
          <span
            className="label-caps"
            style={{ color: "var(--text-muted)" }}
          >
            ORG
          </span>
          <Select
            value={filterOrgId}
            onChange={(e) => setFilterOrgId(e.target.value)}
            className="w-64"
            data-testid="filter-workspace-org"
          >
            <option value="">All orgs</option>
            {orgs?.items.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name ?? o.slug} ({o.slug})
              </option>
            ))}
          </Select>
          {filterOrgId && (
            <button
              type="button"
              onClick={() => {
                setFilterOrgId("");
              }}
              className="text-xs hover:underline"
              style={{ color: "var(--text-muted)" }}
            >
              Clear filter
            </button>
          )}
          {data && (
            <span
              className="ml-auto rounded px-2 py-0.5 text-xs font-mono"
              style={{
                background: "var(--bg-elevated)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border)",
              }}
            >
              {allItems.length} workspaces
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
            title="No workspaces"
            description={
              filterOrgId
                ? "This org has no workspaces yet."
                : "Create a workspace to organise work inside an org."
            }
            action={
              <Button variant="primary" onClick={() => setOpenCreate(true)}>
                + New workspace
              </Button>
            }
          />
        )}

        {/* Table */}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Name</TH>
                <TH>Org</TH>
                <TH>Status</TH>
                <TH>Created</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((ws) => {
                const org = orgs?.items.find((o) => o.id === ws.org_id);
                return (
                  <TR
                    key={ws.id}
                    onClick={() => router.push(`/iam/workspaces/${ws.id}`)}
                    data-testid={`workspace-row-${ws.id}`}
                  >
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--accent)" }}
                      >
                        {ws.slug}
                      </span>
                    </TD>
                    <TD>
                      {ws.display_name ? (
                        <span style={{ color: "var(--text-primary)" }}>{ws.display_name}</span>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>—</span>
                      )}
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {org?.slug ?? ws.org_id.slice(0, 8)}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={ws.is_active ? "success" : "default"} dot={ws.is_active}>
                        {ws.is_active ? "active" : "inactive"}
                      </Badge>
                    </TD>
                    <TD>
                      <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                        {ws.created_at.slice(0, 10)}
                      </span>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </div>

      {openCreate && (
        <CreateWorkspaceDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
          orgs={orgs?.items ?? []}
          defaultOrgId={filterOrgId || null}
        />
      )}
    </>
  );
}

function CreateWorkspaceDialog({
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
  const create = useCreateWorkspace();
  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      org_id: defaultOrgId ?? "",
      slug: "",
      display_name: "",
    },
  });

  useEffect(() => {
    if (open)
      form.reset({
        org_id: defaultOrgId ?? "",
        slug: "",
        display_name: "",
      });
  }, [open, defaultOrgId, form]);

  async function onSubmit(values: CreateForm) {
    try {
      const ws = await create.mutateAsync(values);
      toast(`Created workspace "${ws.slug}"`, "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New workspace"
      description="Workspaces nest inside an org. Slug is unique per-org."
    >
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid="create-workspace-form"
      >
        <Field
          label="Org"
          required
          error={form.formState.errors.org_id?.message}
          htmlFor="ws-org"
        >
          <Select
            id="ws-org"
            {...form.register("org_id")}
            data-testid="create-workspace-org"
          >
            <option value="">Select org…</option>
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name ?? o.slug} ({o.slug})
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Slug"
          required
          error={form.formState.errors.slug?.message}
          htmlFor="ws-slug"
        >
          <Input
            id="ws-slug"
            placeholder="engineering"
            autoFocus
            {...form.register("slug")}
            data-testid="create-workspace-slug"
          />
        </Field>
        <Field
          label="Display name"
          required
          error={form.formState.errors.display_name?.message}
          htmlFor="ws-display-name"
        >
          <Input
            id="ws-display-name"
            placeholder="Engineering"
            {...form.register("display_name")}
            data-testid="create-workspace-display-name"
          />
        </Field>
        <div className="mt-2 flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={create.isPending}
            data-testid="create-workspace-submit"
          >
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
}
