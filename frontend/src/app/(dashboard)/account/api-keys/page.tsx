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
  StatCard,
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

  const activeCount = items.length;
  const now = Date.now();
  const expiringSoon = items.filter((k) => {
    if (!k.expires_at) return false;
    const expiresMs = new Date(k.expires_at).getTime();
    return expiresMs > now && expiresMs - now < 7 * 24 * 60 * 60 * 1000;
  }).length;
  const neverExpires = items.filter((k) => !k.expires_at).length;

  function expiryBadge(expiresAt: string | null) {
    if (!expiresAt) return <Badge tone="default">never</Badge>;
    const expiresMs = new Date(expiresAt).getTime();
    if (expiresMs < now) return <Badge tone="red">expired</Badge>;
    if (expiresMs - now < 7 * 24 * 60 * 60 * 1000) return <Badge tone="amber">soon</Badge>;
    return (
      <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
        {new Date(expiresAt).toLocaleDateString()}
      </span>
    );
  }

  return (
    <div className="flex flex-1 flex-col animate-fade-in">
      {/* Page header */}
      <div
        className="border-b px-8 py-5"
        style={{
          background: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
              Account / API
            </div>
            <h1
              className="text-xl font-semibold tracking-tight"
              style={{ color: "var(--text-primary)" }}
              data-testid="api-keys-heading"
            >
              API Keys
            </h1>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Scoped tokens for backend-to-backend calls. Full token shown once at creation.
            </p>
          </div>
          <Button
            variant="primary"
            data-testid="btn-new-api-key"
            onClick={() => setDialogOpen(true)}
          >
            + New key
          </Button>
        </div>
      </div>

      <div className="mx-auto w-full max-w-5xl px-8 py-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="Total Keys"
            value={isLoading ? "—" : String(activeCount)}
            accent="blue"
          />
          <StatCard
            label="Expiring in 7 Days"
            value={isLoading ? "—" : String(expiringSoon)}
            accent={expiringSoon > 0 ? "amber" : "blue"}
            sub={expiringSoon > 0 ? "Rotate soon" : "All clear"}
          />
          <StatCard
            label="No Expiry"
            value={isLoading ? "—" : String(neverExpires)}
            accent="green"
            sub="Consider setting expiry"
          />
        </div>

        {/* Table */}
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {isError && <ErrorState message={error instanceof Error ? error.message : "Load failed"} />}
        {!isLoading && items.length === 0 && (
          <EmptyState
            title="No API keys"
            description="Issue a key to call TennetCTL APIs from backend services."
          />
        )}
        {items.length > 0 && (
          <div
            className="rounded overflow-hidden"
            style={{ border: "1px solid var(--border)" }}
          >
            <Table>
              <THead>
                <tr>
                  <TH>Label</TH>
                  <TH>Key prefix</TH>
                  <TH>Scopes</TH>
                  <TH>Last used</TH>
                  <TH>Expires</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {items.map((k) => (
                  <TR key={k.id} data-testid={`api-key-row-${k.id}`}>
                    <TD>
                      <span
                        className="text-sm font-medium"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {k.label}
                      </span>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs px-2 py-0.5 rounded"
                        style={{
                          background: "var(--bg-elevated)",
                          color: "var(--accent)",
                          border: "1px solid var(--border)",
                        }}
                      >
                        nk_{k.key_id}…
                      </span>
                    </TD>
                    <TD>
                      <div className="flex flex-wrap gap-1">
                        {k.scopes.map((s) => (
                          <Badge key={s} tone="blue">
                            <span className="font-mono text-[10px]">{s}</span>
                          </Badge>
                        ))}
                      </div>
                    </TD>
                    <TD>
                      <span
                        className="font-mono-data text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "—"}
                      </span>
                    </TD>
                    <TD>{expiryBadge(k.expires_at)}</TD>
                    <TD>
                      <button
                        type="button"
                        data-testid={`api-key-revoke-${k.id}`}
                        disabled={revoke.isPending}
                        onClick={() => {
                          if (confirm(`Revoke API key "${k.label}"? This cannot be undone.`)) {
                            revoke.mutate(k.id);
                          }
                        }}
                        style={{
                          background: "none",
                          border: "none",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          color: "var(--danger)",
                          cursor: revoke.isPending ? "not-allowed" : "pointer",
                          opacity: revoke.isPending ? 0.5 : 1,
                          fontFamily: "var(--font-sans)",
                          transition: "background 0.1s",
                        }}
                      >
                        Revoke
                      </button>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </div>
        )}

        {/* Usage note */}
        <div
          className="flex items-start gap-3 rounded px-4 py-3 text-xs"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <span style={{ color: "var(--info)", fontSize: "14px", flexShrink: 0 }}>ⓘ</span>
          <span>
            API keys are scoped bearer tokens. Pass as{" "}
            <code
              className="font-mono-data"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                borderRadius: "3px",
                padding: "1px 5px",
                color: "var(--accent)",
              }}
            >
              Authorization: Bearer nk_…
            </code>
            . Store securely — the full token is shown only at creation.
          </span>
        </div>
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
  const [copied, setCopied] = useState(false);

  function toggle(s: string) {
    setScopes((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));
  }

  function reset() {
    setLabel("");
    setScopes(["notify:send"]);
    setErr(null);
    setToken(null);
    setCopied(false);
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

  async function handleCopy() {
    if (!token) return;
    await navigator.clipboard.writeText(token).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Modal open={open} onClose={handleClose} title={token ? "Copy your API key" : "New API key"} size="md">
      {token ? (
        <div className="flex flex-col gap-4">
          {/* Warning banner */}
          <div
            className="flex items-start gap-3 rounded px-4 py-3 text-xs"
            style={{
              background: "var(--warning-muted)",
              border: "1px solid var(--warning)",
            }}
          >
            <span style={{ color: "var(--warning)", fontSize: "14px", flexShrink: 0 }}>⚠</span>
            <div>
              <p className="font-semibold" style={{ color: "var(--warning)" }}>
                This is the only time you will see this token.
              </p>
              <p className="mt-0.5" style={{ color: "var(--text-secondary)" }}>
                Copy it now and store it in your secrets manager. It cannot be recovered.
              </p>
            </div>
          </div>

          {/* Token display */}
          <div
            className="rounded px-4 py-3 font-mono-data text-xs break-all"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-bright)",
              color: "var(--accent)",
            }}
          >
            {token}
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              data-testid="btn-copy-api-key"
              onClick={handleCopy}
            >
              {copied ? "Copied!" : "Copy token"}
            </Button>
            <Button variant="primary" data-testid="btn-close-token-dialog" onClick={handleClose}>
              Done
            </Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
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
            <div className="label-caps mb-3" style={{ color: "var(--text-secondary)" }}>
              Scopes
            </div>
            <div className="flex flex-col gap-2">
              {SCOPE_OPTIONS.map((s) => (
                <label
                  key={s.code}
                  className="flex items-start gap-3 rounded px-3 py-2.5 cursor-pointer"
                  style={{
                    background: scopes.includes(s.code) ? "var(--accent-muted)" : "var(--bg-elevated)",
                    border: `1px solid ${scopes.includes(s.code) ? "var(--accent-dim)" : "var(--border)"}`,
                    transition: "background 0.1s, border-color 0.1s",
                  }}
                >
                  <input
                    type="checkbox"
                    data-testid={`scope-${s.code}`}
                    checked={scopes.includes(s.code)}
                    onChange={() => toggle(s.code)}
                    style={{ marginTop: "2px", accentColor: "var(--accent)" }}
                  />
                  <span>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--accent)" }}
                    >
                      {s.label}
                    </span>
                    <span
                      className="ml-2 text-xs"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {s.help}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          {err && (
            <p className="text-xs" style={{ color: "var(--danger)" }}>
              {err}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              data-testid="btn-create-api-key"
              disabled={create.isPending}
            >
              {create.isPending ? "Creating…" : "Create key"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
