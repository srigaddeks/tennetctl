"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
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
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
} from "@/features/auth/hooks/use-api-keys";
import type { ApiKeyScope } from "@/types/api";

const SCOPE_OPTIONS: { code: ApiKeyScope; label: string; help: string }[] = [
  { code: "notify:send", label: "notify:send", help: "Call POST /v1/notify/send" },
  { code: "notify:read", label: "notify:read", help: "Read deliveries, templates, preferences" },
  { code: "audit:read",  label: "audit:read",  help: "Read audit events" },
];

export default function ApiKeysPage() {
  const { data, isLoading, isError, error } = useApiKeys();
  const revoke = useRevokeApiKey();
  const [dialogOpen, setDialogOpen] = useState(false);

  const items = data?.items ?? [];

  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-zinc-200 bg-white px-8 py-6 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight" data-testid="api-keys-heading">API Keys</h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Scoped tokens for backend-to-backend calls. Full token shown once at creation.
            </p>
          </div>
          <Button data-testid="btn-new-api-key" onClick={() => setDialogOpen(true)}>+ New key</Button>
        </div>
      </div>

      <div className="mx-auto w-full max-w-4xl px-8 py-6">
        {isLoading && <Skeleton className="h-16 w-full" />}
        {isError && <ErrorState message={error instanceof Error ? error.message : "Load failed"} />}
        {!isLoading && items.length === 0 && (
          <EmptyState title="No API keys" description="Issue a key to call TennetCTL APIs from backend services." />
        )}
        {items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Label</TH>
                <TH>Prefix</TH>
                <TH>Scopes</TH>
                <TH>Last used</TH>
                <TH>Expires</TH>
                <TH>Actions</TH>
              </tr>
            </THead>
            <TBody>
              {items.map((k) => (
                <TR key={k.id} data-testid={`api-key-row-${k.id}`}>
                  <TD>{k.label}</TD>
                  <TD><span className="font-mono text-xs">nk_{k.key_id}…</span></TD>
                  <TD>
                    <div className="flex flex-wrap gap-1">
                      {k.scopes.map((s) => (
                        <Badge key={s} tone="blue"><span className="font-mono text-[10px]">{s}</span></Badge>
                      ))}
                    </div>
                  </TD>
                  <TD><span className="text-xs">{k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "—"}</span></TD>
                  <TD><span className="text-xs">{k.expires_at ? new Date(k.expires_at).toLocaleDateString() : "never"}</span></TD>
                  <TD>
                    <button
                      type="button"
                      data-testid={`api-key-revoke-${k.id}`}
                      disabled={revoke.isPending}
                      onClick={() => {
                        if (confirm(`Revoke API key "${k.label}"? This cannot be undone.`)) revoke.mutate(k.id);
                      }}
                      className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <NewKeyDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  );
}

function NewKeyDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const create = useCreateApiKey();
  const [label, setLabel] = useState("");
  const [scopes, setScopes] = useState<string[]>(["notify:send"]);
  const [err, setErr] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  function toggle(s: string) {
    setScopes((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));
  }

  function reset() {
    setLabel("");
    setScopes(["notify:send"]);
    setErr(null);
    setToken(null);
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    if (!label) {
      setErr("Label is required.");
      return;
    }
    if (scopes.length === 0) {
      setErr("Pick at least one scope.");
      return;
    }
    create.mutate(
      { label, scopes },
      {
        onSuccess: (r) => setToken(r.token),
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={handleClose} title={token ? "Copy your API key" : "New API key"} size="md">
      {token ? (
        <div className="flex flex-col gap-4">
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
            <p className="font-semibold">This is the only time you will see this token.</p>
            <p className="mt-1">Copy it now and store it in your secrets manager. It cannot be recovered later.</p>
          </div>
          <div className="rounded-md border border-zinc-200 bg-zinc-50 p-3 font-mono text-xs break-all dark:border-zinc-800 dark:bg-zinc-900">
            {token}
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              data-testid="btn-copy-api-key"
              onClick={() => navigator.clipboard.writeText(token).catch(() => {})}
            >
              Copy
            </Button>
            <Button data-testid="btn-close-token-dialog" onClick={handleClose}>Done</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field label="Label" htmlFor="ak-label">
            <Input
              id="ak-label"
              data-testid="input-api-key-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="CI bot, zapier integration, etc."
            />
          </Field>
          <div>
            <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">Scopes</label>
            <div className="mt-2 flex flex-col gap-2">
              {SCOPE_OPTIONS.map((s) => (
                <label key={s.code} className="flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    data-testid={`scope-${s.code}`}
                    checked={scopes.includes(s.code)}
                    onChange={() => toggle(s.code)}
                  />
                  <span>
                    <span className="font-mono text-xs">{s.label}</span>
                    <span className="ml-2 text-xs text-zinc-500">{s.help}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
          {err && <p className="text-xs text-red-500">{err}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={handleClose}>Cancel</Button>
            <Button type="submit" data-testid="btn-create-api-key" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create key"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
