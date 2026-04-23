"use client";

import { useState } from "react";

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
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import {
  useCreateOidcProvider,
  useDeleteOidcProvider,
  useOidcProviders,
} from "@/features/iam-security/hooks/use-sso";
import { ApiClientError } from "@/lib/api";
import type { OidcProvider, OidcProviderCreateBody } from "@/types/api";

const DEFAULT_CLAIM_MAPPING = JSON.stringify(
  { email: "email", name: "name", sub: "sub" },
  null,
  2,
);
const DEFAULT_SCOPES = "openid email profile";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "SSO" },
];

export default function SSOPage() {
  const { data: providers = [], isLoading, isError, error, refetch } =
    useOidcProviders();
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<OidcProvider | null>(null);

  return (
    <>
      <PageHeader
        title="Single Sign-On"
        description="OpenID Connect providers used for federated sign-in into your organisation."
        testId="heading-iam-sso"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            variant="primary"
            data-testid="btn-new-sso"
            onClick={() => setCreateOpen(true)}
          >
            + Add provider
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in" data-testid="iam-sso-body">
        {/* Info banner */}
        <div
          className="mb-5 rounded border px-4 py-3 text-xs"
          style={{
            background: "var(--accent-muted)",
            borderColor: "var(--accent)",
            color: "var(--text-secondary)",
          }}
        >
          Providers are used for SP-initiated OIDC flows. The callback URL is{" "}
          <code
            className="font-mono-data"
            style={{ color: "var(--accent)" }}
          >
            /v1/auth/oidc/&#123;org-slug&#125;/callback
          </code>
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
        {!isLoading && !isError && providers.length === 0 && (
          <EmptyState
            title="No OIDC providers"
            description="Add an OIDC provider such as Okta, Auth0 or Google to enable SSO."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + Add provider
              </Button>
            }
          />
        )}
        {providers.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Issuer</TH>
                <TH>Client ID</TH>
                <TH>Status</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {providers.map((p) => (
                <TR key={p.id} data-testid={`sso-row-${p.id}`}>
                  <TD>
                    <span className="font-mono-data text-xs" style={{ color: "var(--accent)" }}>
                      {p.slug}
                    </span>
                  </TD>
                  <TD>
                    <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      {p.issuer}
                    </span>
                  </TD>
                  <TD>
                    <span className="font-mono-data text-xs">{p.client_id}</span>
                  </TD>
                  <TD>
                    <Badge tone={p.enabled ? "success" : "default"} dot>
                      {p.enabled ? "enabled" : "disabled"}
                    </Badge>
                  </TD>
                  <TD className="text-right">
                    <div className="flex justify-end gap-2">
                      <a
                        href={`/v1/auth/oidc/${p.org_slug ?? "default"}/initiate?provider=${p.slug}`}
                        target="_blank"
                        rel="noreferrer"
                        data-testid={`sso-test-${p.id}`}
                      >
                        <Button variant="ghost" size="sm" type="button">
                          Test
                        </Button>
                      </a>
                      <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        data-testid={`sso-delete-${p.id}`}
                        onClick={() => setDeleteTarget(p)}
                        style={{ color: "var(--danger)" }}
                      >
                        Delete
                      </Button>
                    </div>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <CreateProviderDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <DeleteProviderDialog
        provider={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </>
  );
}

function CreateProviderDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateOidcProvider();
  const [form, setForm] = useState<OidcProviderCreateBody>({
    slug: "",
    issuer: "",
    client_id: "",
    client_secret_vault_key: "",
    scopes: DEFAULT_SCOPES,
    claim_mapping: { email: "email", name: "name", sub: "sub" },
  });
  const [claimMappingRaw, setClaimMappingRaw] = useState(DEFAULT_CLAIM_MAPPING);
  const [err, setErr] = useState<string | null>(null);

  function reset() {
    setForm({
      slug: "",
      issuer: "",
      client_id: "",
      client_secret_vault_key: "",
      scopes: DEFAULT_SCOPES,
      claim_mapping: { email: "email", name: "name", sub: "sub" },
    });
    setClaimMappingRaw(DEFAULT_CLAIM_MAPPING);
    setErr(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    let parsed: Record<string, string>;
    try {
      parsed = JSON.parse(claimMappingRaw);
    } catch {
      setErr("Claim mapping must be valid JSON.");
      return;
    }
    try {
      await create.mutateAsync({ ...form, claim_mapping: parsed });
      toast(`Created provider "${form.slug}"`, "success");
      reset();
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add OIDC provider" size="md">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="create-sso-form"
      >
        <Field label="Slug" htmlFor="sso-slug" required hint="unique, lower-case">
          <Input
            id="sso-slug"
            value={form.slug}
            onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
            placeholder="okta"
            autoFocus
            required
            data-testid="create-sso-slug"
          />
        </Field>
        <Field label="Issuer URL" htmlFor="sso-issuer" required>
          <Input
            id="sso-issuer"
            value={form.issuer}
            onChange={(e) => setForm((f) => ({ ...f, issuer: e.target.value }))}
            placeholder="https://your-idp.example.com"
            required
            data-testid="create-sso-issuer"
          />
        </Field>
        <Field label="Client ID" htmlFor="sso-client-id" required>
          <Input
            id="sso-client-id"
            value={form.client_id}
            onChange={(e) =>
              setForm((f) => ({ ...f, client_id: e.target.value }))
            }
            placeholder="client_123"
            required
            data-testid="create-sso-client-id"
          />
        </Field>
        <Field
          label="Vault key for secret"
          htmlFor="sso-vault-key"
          required
          hint="Vault secret holding the client secret"
        >
          <Input
            id="sso-vault-key"
            value={form.client_secret_vault_key}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                client_secret_vault_key: e.target.value,
              }))
            }
            placeholder="iam.oidc.acme.secret"
            required
            data-testid="create-sso-vault-key"
          />
        </Field>
        <Field label="Scopes" htmlFor="sso-scopes">
          <Input
            id="sso-scopes"
            value={form.scopes ?? ""}
            onChange={(e) =>
              setForm((f) => ({ ...f, scopes: e.target.value }))
            }
            placeholder={DEFAULT_SCOPES}
            data-testid="create-sso-scopes"
          />
        </Field>
        <Field
          label="Claim mapping (JSON)"
          htmlFor="sso-claim"
          hint="maps IdP claims to local fields"
        >
          <Textarea
            id="sso-claim"
            value={claimMappingRaw}
            onChange={(e) => setClaimMappingRaw(e.target.value)}
            rows={4}
            className="font-mono"
            data-testid="create-sso-claim"
          />
        </Field>
        {err && (
          <p className="text-xs" style={{ color: "var(--danger)" }}>
            {err}
          </p>
        )}
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-sso-submit"
          >
            Save provider
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function DeleteProviderDialog({
  provider,
  onClose,
}: {
  provider: OidcProvider | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const del = useDeleteOidcProvider();

  async function onConfirm() {
    if (!provider) return;
    try {
      await del.mutateAsync(provider.id);
      toast(`Deleted provider "${provider.slug}"`, "success");
      onClose();
    } catch (e) {
      toast(e instanceof ApiClientError ? e.message : String(e), "error");
    }
  }

  return (
    <ConfirmDialog
      open={provider !== null}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Delete OIDC provider"
      description={
        provider
          ? `This removes the provider "${provider.slug}". Users signed in through it will need to re-authenticate.`
          : undefined
      }
      confirmLabel="Delete"
      tone="danger"
      loading={del.isPending}
      testId="confirm-delete-sso"
    />
  );
}
