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
} from "@/components/ui";
import {
  useCreateScimToken,
  useRevokeScimToken,
  useScimTokens,
} from "@/features/iam-security/hooks/use-scim";
import { ApiClientError } from "@/lib/api";
import type { ScimToken } from "@/types/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "SCIM" },
];

export default function SCIMPage() {
  const { data: tokens = [], isLoading, isError, error, refetch } =
    useScimTokens();
  const [createOpen, setCreateOpen] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<ScimToken | null>(null);
  const [newToken, setNewToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [appId, setAppId] = useState<string | null>(null);

  const origin = typeof window !== "undefined" ? window.location.origin : "";

  async function handleCopy() {
    if (!newToken) return;
    await navigator.clipboard.writeText(newToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <>
      <PageHeader
        title="SCIM Provisioning"
        description="Bearer tokens that let SCIM 2.0 IdPs (Okta, Azure AD, OneLogin) provision users and groups."
        testId="heading-iam-scim"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            variant="primary"
            data-testid="btn-new-scim"
            onClick={() => setCreateOpen(true)}
          >
            + Create token
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in space-y-5"
        data-testid="iam-scim-body"
      >
        <ApplicationScopeBar appId={appId} onChange={setAppId} label="SCIM tokens for application" />

        {/* New token banner */}
        {newToken && (
          <div
            className="rounded border p-4"
            style={{
              background: "var(--success-muted)",
              borderColor: "var(--success)",
            }}
            data-testid="scim-new-token-banner"
          >
            <div className="mb-2 flex items-center justify-between">
              <p
                className="text-xs font-semibold"
                style={{ color: "var(--success)" }}
              >
                Token created — copy it now. It will not be shown again.
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCopy}
                  style={{ color: "var(--success)" }}
                >
                  {copied ? "Copied!" : "Copy"}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setNewToken(null)}
                  style={{ color: "var(--text-muted)" }}
                >
                  Dismiss
                </Button>
              </div>
            </div>
            <code
              className="font-mono-data block select-all break-all rounded border px-3 py-2 text-xs"
              style={{
                background: "var(--bg-base)",
                borderColor: "var(--success)",
                color: "var(--success)",
              }}
              data-testid="scim-new-token"
            >
              {newToken}
            </code>
          </div>
        )}

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
        {!isLoading && !isError && tokens.length === 0 && (
          <EmptyState
            title="No SCIM tokens"
            description="Create a token to let an IdP push user/group updates into your org."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + Create token
              </Button>
            }
          />
        )}
        {tokens.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Label</TH>
                <TH>Status</TH>
                <TH>Created</TH>
                <TH>Last used</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {tokens.map((t) => (
                <TR key={t.id} data-testid={`scim-row-${t.id}`}>
                  <TD>
                    <span
                      className="text-xs font-medium"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {t.label}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone="success" dot>active</Badge>
                  </TD>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {new Date(t.created_at).toLocaleDateString()}
                    </span>
                  </TD>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {t.last_used_at
                        ? new Date(t.last_used_at).toLocaleDateString()
                        : "—"}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      type="button"
                      data-testid={`scim-delete-${t.id}`}
                      onClick={() => setRevokeTarget(t)}
                      style={{ color: "var(--danger)" }}
                    >
                      Revoke
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}

        {/* Endpoint reference */}
        <div
          className="rounded border p-4"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
          }}
        >
          <p
            className="label-caps mb-2 text-[11px]"
            style={{ color: "var(--text-muted)" }}
          >
            SCIM 2.0 endpoint base URL
          </p>
          <code
            className="font-mono-data block rounded border px-3 py-2 text-xs"
            style={{
              background: "var(--bg-base)",
              borderColor: "var(--border-bright)",
              color: "var(--accent)",
            }}
          >
            {origin}/scim/v2/&#123;org-slug&#125;
          </code>
          <div
            className="mt-2 flex gap-4 text-[11px]"
            style={{ color: "var(--text-secondary)" }}
          >
            <span>
              Users:{" "}
              <code
                className="font-mono-data"
                style={{ color: "var(--text-primary)" }}
              >
                /Users
              </code>
            </span>
            <span>
              Groups:{" "}
              <code
                className="font-mono-data"
                style={{ color: "var(--text-primary)" }}
              >
                /Groups
              </code>
            </span>
          </div>
        </div>
      </div>

      <CreateTokenDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(token) => setNewToken(token)}
      />
      <RevokeTokenDialog
        token={revokeTarget}
        onClose={() => setRevokeTarget(null)}
      />
    </>
  );
}

function CreateTokenDialog({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (token: string) => void;
}) {
  const { toast } = useToast();
  const create = useCreateScimToken();
  const [label, setLabel] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const result = await create.mutateAsync({ label });
      toast(`Created token "${label}"`, "success");
      onCreated(result.token);
      setLabel("");
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Create SCIM token" size="sm">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="create-scim-form"
      >
        <Field label="Label" htmlFor="scim-label" required>
          <Input
            id="scim-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="okta-prod"
            autoFocus
            required
            data-testid="create-scim-label"
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
            disabled={!label}
            data-testid="create-scim-submit"
          >
            Create token
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RevokeTokenDialog({
  token,
  onClose,
}: {
  token: ScimToken | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const revoke = useRevokeScimToken();

  async function onConfirm() {
    if (!token) return;
    try {
      await revoke.mutateAsync(token.id);
      toast(`Revoked token "${token.label}"`, "success");
      onClose();
    } catch (e) {
      toast(e instanceof ApiClientError ? e.message : String(e), "error");
    }
  }

  return (
    <ConfirmDialog
      open={token !== null}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Revoke SCIM token"
      description={
        token
          ? `This immediately blocks requests authenticated with "${token.label}". IdPs using it will stop syncing.`
          : undefined
      }
      confirmLabel="Revoke"
      tone="danger"
      loading={revoke.isPending}
      testId="confirm-revoke-scim"
    />
  );
}
