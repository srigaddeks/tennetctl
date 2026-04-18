"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
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

  return (
    <>
      <PageHeader
        title="Workspaces"
        description="Scoped work containers within an org. Slug unique per (org_id, slug)."
        testId="heading-workspaces"
        actions={
          <Button
            onClick={() => setOpenCreate(true)}
            data-testid="open-create-workspace"
          >
            + New workspace
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="workspaces-body">
        <div className="mb-4 flex items-center gap-2">
          <label className="text-xs text-zinc-500">Filter by org</label>
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
        </div>
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No workspaces"
            description={
              filterOrgId
                ? "This org has no workspaces yet."
                : "Create a workspace to organise work inside an org."
            }
            action={
              <Button onClick={() => setOpenCreate(true)}>
                + New workspace
              </Button>
            }
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Name</TH>
                <TH>Org</TH>
                <TH>Status</TH>
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
                      <span className="font-mono text-xs">{ws.slug}</span>
                    </TD>
                    <TD>
                      {ws.display_name ?? <span className="text-zinc-400">—</span>}
                    </TD>
                    <TD>
                      <span className="text-xs text-zinc-500">
                        {org?.slug ?? ws.org_id.slice(0, 8)}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={ws.is_active ? "emerald" : "zinc"}>
                        {ws.is_active ? "active" : "inactive"}
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
