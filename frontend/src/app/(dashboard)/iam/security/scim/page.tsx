"use client";

import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
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

  const origin = typeof window !== "undefined" ? window.location.origin : "";

  return (
    <>
      <PageHeader
        title="SCIM Provisioning"
        description="Bearer tokens that let SCIM 2.0 IdPs (Okta, Azure AD, OneLogin) provision users and groups."
        testId="heading-iam-scim"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            data-testid="btn-new-scim"
            onClick={() => setCreateOpen(true)}
          >
            + Create token
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-8 py-6 space-y-6"
        data-testid="iam-scim-body"
      >
        {newToken && (
          <div
            className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm dark:border-emerald-800/50 dark:bg-emerald-950/40"
            data-testid="scim-new-token-banner"
          >
            <p className="font-medium text-emerald-900 dark:text-emerald-100">
              Token created — copy it now. It won&apos;t be shown again.
            </p>
            <code
              className="mt-2 block select-all break-all rounded bg-white/70 px-2 py-1 font-mono text-xs text-emerald-950 dark:bg-emerald-900/60 dark:text-emerald-100"
              data-testid="scim-new-token"
            >
              {newToken}
            </code>
            <div className="mt-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setNewToken(null)}
              >
                Dismiss
              </Button>
            </div>
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
                <TH>Created</TH>
                <TH>Last used</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {tokens.map((t) => (
                <TR key={t.id} data-testid={`scim-row-${t.id}`}>
                  <TD>
                    <span className="font-medium">{t.label}</span>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {new Date(t.created_at).toLocaleDateString()}
                    </span>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
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
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30"
                    >
                      Revoke
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}

        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-xs text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-400">
          <p className="font-medium text-zinc-800 dark:text-zinc-200">
            SCIM 2.0 endpoint base URL
          </p>
          <code className="mt-1 block font-mono">
            {origin}/scim/v2/&#123;org-slug&#125;
          </code>
          <p className="mt-1">
            Users: <code className="font-mono">/Users</code> · Groups:{" "}
            <code className="font-mono">/Groups</code>
          </p>
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
        {err && <p className="text-xs text-red-600">{err}</p>}
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
