"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
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
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useDeleteOrg,
  useOrg,
  useUpdateOrg,
} from "@/features/iam-orgs/hooks/use-orgs";
import { useWorkspaces } from "@/features/iam-workspaces/hooks/use-workspaces";
import { useApplications } from "@/features/iam-applications/hooks/use-applications";
import { useFlags } from "@/features/featureflags/hooks/use-flags";
import { useSecrets } from "@/features/vault/secrets/hooks/use-secrets";
import { ApiClientError } from "@/lib/api";

const SLUG = /^[a-z][a-z0-9-]{1,62}$/;

const editSchema = z.object({
  slug: z.string().regex(SLUG, "invalid slug"),
  display_name: z.string().min(1, "required"),
});
type EditForm = z.infer<typeof editSchema>;

type QuickLinkCardProps = {
  label: string;
  count: number | string;
  sub: string;
  href: string;
  accentColor: string;
};

function QuickLinkCard({ label, count, sub, href, accentColor }: QuickLinkCardProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <Link
      href={href}
      style={{
        display: "block",
        background: "var(--bg-elevated)",
        border: `1px solid ${hovered ? accentColor : "var(--border)"}`,
        borderRadius: "8px",
        padding: "16px",
        textDecoration: "none",
        transition: "border-color 150ms ease",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <p
        className="label-caps mb-2"
        style={{ color: "var(--text-secondary)" }}
      >
        {label}
      </p>
      <p
        className="text-xl font-semibold"
        style={{ color: hovered ? accentColor : "var(--text-primary)" }}
      >
        {count}
      </p>
      <p
        className="text-xs mt-1"
        style={{ color: "var(--text-muted)" }}
      >
        {sub} →
      </p>
    </Link>
  );
}

export default function OrgDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orgId = typeof params.id === "string" ? params.id : "";
  const { toast } = useToast();

  const { data: org, isLoading, isError, error } = useOrg(orgId);
  const update = useUpdateOrg();
  const del = useDeleteOrg();
  const { data: workspaces } = useWorkspaces({ limit: 500, org_id: orgId });
  const { data: applications } = useApplications({ org_id: orgId, limit: 50 });
  const { data: flags } = useFlags({ org_id: orgId, limit: 1 });
  const { data: secrets } = useSecrets({ org_id: orgId });

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState("");

  const form = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    defaultValues: { slug: "", display_name: "" },
  });

  useEffect(() => {
    if (org) {
      form.reset({
        slug: org.slug,
        display_name: org.display_name ?? "",
      });
    }
  }, [org, form]);

  async function onSave(values: EditForm) {
    if (!org) return;
    const dirty = form.formState.dirtyFields;
    const body: { slug?: string; display_name?: string } = {};
    if (dirty.slug) body.slug = values.slug;
    if (dirty.display_name) body.display_name = values.display_name;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: org.id, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function handleDelete() {
    if (!org) return;
    if (deleteConfirm !== org.slug) return;
    try {
      await del.mutateAsync(org.id);
      toast("Org deleted", "success");
      router.push("/iam/orgs");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    } finally {
      setDeleteOpen(false);
      setDeleteConfirm("");
    }
  }

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Organisation"
          description="Loading…"
          testId="heading-org-detail"
        />
        <div className="px-8 py-6 space-y-3">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-48" />
        </div>
      </>
    );
  }

  if (isError || !org) {
    return (
      <>
        <PageHeader
          title="Organisation"
          description="Not found"
          testId="heading-org-detail"
        />
        <div className="px-8 py-6">
          <ErrorState
            message={
              error instanceof Error
                ? error.message
                : "Org not found or you don't have access."
            }
          />
          <div className="mt-4">
            <Link
              href="/iam/orgs"
              style={{ color: "var(--text-secondary)" }}
              className="text-sm hover:underline"
            >
              ← Back to orgs
            </Link>
          </div>
        </div>
      </>
    );
  }

  const wsItems = workspaces?.items ?? [];
  const activeWs = wsItems.filter((w) => w.is_active).length;
  const flagCount = flags?.pagination.total ?? 0;
  const secretCount = secrets?.pagination.total ?? 0;

  return (
    <>
      <PageHeader
        title={org.display_name ?? org.slug}
        description={`Organisation · ${org.slug}`}
        testId="heading-org-detail"
        breadcrumbs={[
          { label: "IAM", href: "/iam/orgs" },
          { label: "Organisations", href: "/iam/orgs" },
          { label: org.display_name ?? org.slug },
        ]}
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="org-detail-body">

        {/* Stat cards */}
        <div className="mb-6 grid grid-cols-3 gap-4">
          <StatCard
            label="Workspaces"
            value={wsItems.length}
            sub={`${activeWs} active`}
            accent="blue"
          />
          <StatCard
            label="Status"
            value={org.is_active ? "Active" : "Inactive"}
            sub={org.is_test ? "test tenant" : "production tenant"}
            accent={org.is_active ? "green" : "red"}
          />
          <StatCard
            label="Created"
            value={org.created_at.slice(0, 10)}
            sub={`ID: ${org.id.slice(0, 8)}…`}
            accent="blue"
          />
        </div>

        {/* General Info card */}
        <section
          className="mb-6 rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="org-detail-info"
        >
          <div className="mb-5 flex items-center justify-between">
            <h2
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              General Information
            </h2>
            <div className="flex flex-wrap gap-1.5">
              <Badge tone={org.is_active ? "success" : "default"} dot={org.is_active}>
                {org.is_active ? "active" : "inactive"}
              </Badge>
              {org.is_test && <Badge tone="amber">TEST</Badge>}
            </div>
          </div>

          <form
            onSubmit={form.handleSubmit(onSave)}
            className="flex flex-col gap-4"
            data-testid="org-edit-form"
          >
            <div className="grid grid-cols-2 gap-4">
              <Field
                label="Slug"
                required
                error={form.formState.errors.slug?.message}
                htmlFor="org-edit-slug"
              >
                <Input
                  id="org-edit-slug"
                  {...form.register("slug")}
                  data-testid="org-edit-slug"
                />
              </Field>
              <Field
                label="Display Name"
                required
                error={form.formState.errors.display_name?.message}
                htmlFor="org-edit-display-name"
              >
                <Input
                  id="org-edit-display-name"
                  {...form.register("display_name")}
                  data-testid="org-edit-display-name"
                />
              </Field>
            </div>

            <div
              className="flex justify-between gap-2 pt-4"
              style={{ borderTop: "1px solid var(--border)" }}
            >
              <Button
                variant="danger"
                type="button"
                size="sm"
                onClick={() => setDeleteOpen(true)}
                data-testid="org-delete-open"
              >
                Delete org
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
                data-testid="org-edit-save"
              >
                Save changes
              </Button>
            </div>
          </form>
        </section>

        {/* Workspaces section */}
        <section
          className="mb-6 rounded-lg p-6"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
          }}
          data-testid="org-workspaces-section"
        >
          <div className="mb-5 flex items-center justify-between">
            <h2
              className="label-caps"
              style={{ color: "var(--text-secondary)" }}
            >
              Workspaces
              <span
                className="ml-2 rounded px-1.5 py-0.5 font-mono-data"
                style={{
                  background: "var(--bg-elevated)",
                  color: "var(--text-muted)",
                  fontSize: "10px",
                }}
              >
                {wsItems.length}
              </span>
            </h2>
            <Link
              href={`/iam/workspaces?org_id=${org.id}`}
              className="text-xs hover:underline"
              style={{ color: "var(--accent)" }}
            >
              Manage workspaces →
            </Link>
          </div>

          {wsItems.length === 0 ? (
            <EmptyState
              title="No workspaces"
              description="This org has no workspaces yet."
            />
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH>Slug</TH>
                  <TH>Name</TH>
                  <TH>Status</TH>
                  <TH>Created</TH>
                </tr>
              </THead>
              <TBody>
                {wsItems.map((ws) => (
                  <TR
                    key={ws.id}
                    onClick={() => router.push(`/iam/workspaces/${ws.id}`)}
                    data-testid={`org-ws-row-${ws.id}`}
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
                ))}
              </TBody>
            </Table>
          )}
        </section>

        {/* Applications in this org */}
        {(applications?.items ?? []).length > 0 && (
          <section
            className="mb-6 rounded-lg p-6"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
            }}
            data-testid="org-applications-section"
          >
            <h2
              className="label-caps mb-4"
              style={{ color: "var(--text-secondary)" }}
            >
              Applications in this org
              <span
                className="ml-2 rounded px-1.5 py-0.5 font-mono-data"
                style={{
                  background: "var(--bg-elevated)",
                  color: "var(--text-muted)",
                  fontSize: "10px",
                }}
              >
                {applications?.items.length ?? 0}
              </span>
            </h2>
            <div className="flex flex-wrap gap-2">
              {(applications?.items ?? []).map((app) => (
                <Link
                  key={app.id}
                  href={`/iam/applications/${app.id}`}
                  className="rounded border px-3 py-1.5 text-xs hover:underline"
                  style={{
                    background: "var(--bg-elevated)",
                    borderColor: "var(--border)",
                    color: "var(--text-primary)",
                  }}
                >
                  {app.label ?? app.code}
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Quick Links section */}
        <section data-testid="org-quick-links">
          <h2
            className="label-caps mb-4"
            style={{ color: "var(--text-secondary)" }}
          >
            Quick Links
          </h2>
          <div className="grid grid-cols-4 gap-4">
            <QuickLinkCard
              label="Feature Flags"
              count={flagCount}
              sub="flags for this org"
              href={`/feature-flags?org_id=${org.id}&org_scope=true`}
              accentColor="var(--accent)"
            />
            <QuickLinkCard
              label="Vault Secrets"
              count={secretCount}
              sub="secrets for this org"
              href={`/vault/secrets?org_id=${org.id}`}
              accentColor="#f5a623"
            />
            <QuickLinkCard
              label="Audit Events"
              count="View"
              sub="activity for this org"
              href={`/audit?org_id=${org.id}`}
              accentColor="#ff6b35"
            />
            <QuickLinkCard
              label="Members"
              count="Manage"
              sub="access in this org"
              href={`/iam/memberships?org_id=${org.id}`}
              accentColor="var(--success)"
            />
          </div>
        </section>
      </div>

      <Modal
        open={deleteOpen}
        onClose={() => {
          setDeleteOpen(false);
          setDeleteConfirm("");
        }}
        title={`Delete org "${org.slug}"?`}
        description="This soft-deletes the org. Workspaces and memberships under this org are retained but the org itself is hidden from active listings."
      >
        <div className="flex flex-col gap-4">
          <Field
            label={`Type the slug "${org.slug}" to confirm`}
            htmlFor="org-delete-confirm-input"
          >
            <Input
              id="org-delete-confirm-input"
              value={deleteConfirm}
              onChange={(e) => setDeleteConfirm(e.target.value)}
              placeholder={org.slug}
              data-testid="org-delete-confirm-input"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              type="button"
              onClick={() => {
                setDeleteOpen(false);
                setDeleteConfirm("");
              }}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              type="button"
              disabled={deleteConfirm !== org.slug}
              loading={del.isPending}
              onClick={handleDelete}
              data-testid="org-delete-confirm-submit"
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
