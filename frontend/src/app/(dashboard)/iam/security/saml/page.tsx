"use client";

import { useState } from "react";

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
  useCreateSamlProvider,
  useDeleteSamlProvider,
  useSamlProviders,
} from "@/features/iam-security/hooks/use-saml";
import { ApiClientError } from "@/lib/api";
import type { SamlProvider, SamlProviderCreateBody } from "@/types/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "SAML" },
];

const EMPTY_FORM: SamlProviderCreateBody = {
  idp_entity_id: "",
  sso_url: "",
  x509_cert: "",
  sp_entity_id: "",
  enabled: true,
};

export default function SAMLPage() {
  const { data: providers = [], isLoading, isError, error, refetch } =
    useSamlProviders();
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SamlProvider | null>(null);
  const [expandedCert, setExpandedCert] = useState<string | null>(null);
  const [appId, setAppId] = useState<string | null>(null);

  return (
    <>
      <PageHeader
        title="SAML 2.0 SSO"
        description="SAML 2.0 Identity Providers for SP-initiated SSO."
        testId="heading-iam-saml"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            variant="primary"
            data-testid="btn-new-saml"
            onClick={() => setCreateOpen(true)}
          >
            + Add provider
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in" data-testid="iam-saml-body">
        <div className="mb-5">
          <ApplicationScopeBar appId={appId} onChange={setAppId} label="SAML for application" />
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
            title="No SAML providers"
            description="Add an IdP to accept SAML-signed authentication assertions."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + Add provider
              </Button>
            }
          />
        )}
        {providers.length > 0 && (
          <div className="space-y-3">
            <Table>
              <THead>
                <tr>
                  <TH>IdP Entity ID</TH>
                  <TH>SSO URL</TH>
                  <TH>SP Entity ID</TH>
                  <TH>Status</TH>
                  <TH className="text-right">Actions</TH>
                </tr>
              </THead>
              <TBody>
                {providers.map((p) => (
                  <TR key={p.id} data-testid={`saml-row-${p.id}`}>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--accent)" }}
                      >
                        {p.idp_entity_id}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {p.sso_url}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-muted)" }}
                      >
                        {p.sp_entity_id}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={p.enabled ? "success" : "default"} dot>
                        {p.enabled ? "enabled" : "disabled"}
                      </Badge>
                    </TD>
                    <TD className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          type="button"
                          onClick={() =>
                            setExpandedCert(
                              expandedCert === p.id ? null : p.id,
                            )
                          }
                        >
                          {expandedCert === p.id ? "Hide cert" : "View cert"}
                        </Button>
                        <a
                          href={`/v1/auth/saml/${p.org_slug}/metadata`}
                          target="_blank"
                          rel="noreferrer"
                          data-testid={`saml-metadata-${p.id}`}
                        >
                          <Button variant="ghost" size="sm" type="button">
                            Metadata
                          </Button>
                        </a>
                        <Button
                          variant="ghost"
                          size="sm"
                          type="button"
                          data-testid={`saml-delete-${p.id}`}
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

            {/* Certificate display */}
            {providers.map((p) =>
              expandedCert === p.id ? (
                <div
                  key={`cert-${p.id}`}
                  className="rounded border"
                  style={{
                    background: "var(--bg-base)",
                    borderColor: "var(--border)",
                  }}
                >
                  <div
                    className="flex items-center justify-between border-b px-4 py-2"
                    style={{ borderColor: "var(--border)" }}
                  >
                    <span
                      className="label-caps text-[11px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      x509 Certificate — {p.idp_entity_id}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      type="button"
                      onClick={() => setExpandedCert(null)}
                    >
                      Close
                    </Button>
                  </div>
                  <pre
                    className="overflow-x-auto p-4 font-mono-data text-[11px] leading-relaxed"
                    style={{ color: "var(--success)", whiteSpace: "pre-wrap", wordBreak: "break-all" }}
                  >
                    {p.x509_cert}
                  </pre>
                </div>
              ) : null,
            )}
          </div>
        )}
      </div>

      <CreateSamlDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <DeleteSamlDialog
        provider={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </>
  );
}

function CreateSamlDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateSamlProvider();
  const [form, setForm] = useState<SamlProviderCreateBody>(EMPTY_FORM);
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await create.mutateAsync(form);
      toast("SAML provider added", "success");
      setForm(EMPTY_FORM);
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add SAML provider" size="md">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="create-saml-form"
      >
        <Field label="IdP Entity ID" htmlFor="saml-idp-entity" required>
          <Input
            id="saml-idp-entity"
            value={form.idp_entity_id}
            onChange={(e) =>
              setForm((f) => ({ ...f, idp_entity_id: e.target.value }))
            }
            placeholder="https://idp.example.com/saml2/metadata"
            autoFocus
            required
            data-testid="create-saml-idp-entity"
          />
        </Field>
        <Field label="IdP SSO URL" htmlFor="saml-sso-url" required>
          <Input
            id="saml-sso-url"
            value={form.sso_url}
            onChange={(e) =>
              setForm((f) => ({ ...f, sso_url: e.target.value }))
            }
            placeholder="https://idp.example.com/saml2/sso"
            required
            data-testid="create-saml-sso-url"
          />
        </Field>
        <Field label="SP Entity ID" htmlFor="saml-sp-entity" required>
          <Input
            id="saml-sp-entity"
            value={form.sp_entity_id}
            onChange={(e) =>
              setForm((f) => ({ ...f, sp_entity_id: e.target.value }))
            }
            placeholder="https://tennetctl.example.com"
            required
            data-testid="create-saml-sp-entity"
          />
        </Field>
        <Field
          label="IdP x509 Certificate (PEM)"
          htmlFor="saml-cert"
          required
        >
          <Textarea
            id="saml-cert"
            value={form.x509_cert}
            onChange={(e) =>
              setForm((f) => ({ ...f, x509_cert: e.target.value }))
            }
            rows={6}
            required
            placeholder={"-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"}
            className="font-mono"
            data-testid="create-saml-cert"
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
            data-testid="create-saml-submit"
          >
            Save provider
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function DeleteSamlDialog({
  provider,
  onClose,
}: {
  provider: SamlProvider | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const del = useDeleteSamlProvider();

  async function onConfirm() {
    if (!provider) return;
    try {
      await del.mutateAsync(provider.id);
      toast("SAML provider deleted", "success");
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
      title="Delete SAML provider"
      description={
        provider
          ? `This removes the IdP "${provider.idp_entity_id}". Users authenticating through it will need to re-enrol.`
          : undefined
      }
      confirmLabel="Delete"
      tone="danger"
      loading={del.isPending}
      testId="confirm-delete-saml"
    />
  );
}
