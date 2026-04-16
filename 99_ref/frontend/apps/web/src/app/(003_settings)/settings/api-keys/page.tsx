"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Label,
  Badge,
} from "@kcontrol/ui";
import {
  Plus,
  Copy,
  Check,
  RotateCcw,
  Trash2,
  AlertCircle,
  Key,
  XCircle,
  CheckCircle2,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  listApiKeys,
  createApiKey,
  rotateApiKey,
  revokeApiKey,
  deleteApiKey,
} from "@/lib/api/apikeys";
import type { ApiKeyResponse, CreateApiKeyResponse } from "@/lib/api/apikeys";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── Raw key reveal banner ──────────────────────────────────────────────────

function NewKeyBanner({
  rawKey,
  onDismiss,
}: {
  rawKey: string;
  onDismiss: () => void;
}) {
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="rounded-xl border border-green-500/40 bg-green-500/5 p-4 space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
          <p className="text-sm font-semibold text-green-600 dark:text-green-400">
            API key created. Copy it now — it will not be shown again.
          </p>
        </div>
        <button
          onClick={onDismiss}
          className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
        >
          <XCircle className="h-4 w-4" />
        </button>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 rounded-lg border border-border bg-muted px-3 py-2 font-mono text-sm text-foreground">
          {visible ? rawKey : "•".repeat(Math.min(rawKey.length, 48))}
        </div>
        <button
          onClick={() => setVisible((v) => !v)}
          className="p-2 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
          title={visible ? "Hide key" : "Show key"}
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
        <Button size="sm" variant="outline" onClick={handleCopy} className="gap-1.5 shrink-0">
          {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </div>
  );
}

// ── Create form ────────────────────────────────────────────────────────────

const EXPIRY_OPTIONS = [
  { label: "No expiration", value: "" },
  { label: "30 days", value: "30" },
  { label: "60 days", value: "60" },
  { label: "90 days", value: "90" },
  { label: "180 days", value: "180" },
  { label: "1 year", value: "365" },
] as const;

function CreateKeyForm({
  onCreated,
  onCancel,
}: {
  onCreated: (key: CreateApiKeyResponse) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [expiryDays, setExpiryDays] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const payload: { name: string; expires_at?: string } = { name: name.trim() };
      if (expiryDays) {
        const d = new Date();
        d.setDate(d.getDate() + Number(expiryDays));
        payload.expires_at = d.toISOString();
      }
      const key = await createApiKey(payload);
      onCreated(key);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="border-primary/30">
      <CardHeader>
        <CardTitle className="text-base">Create API Key</CardTitle>
        <CardDescription>Give this key a descriptive name for identification.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label htmlFor="key-name">Name</Label>
              <Input
                id="key-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CI/CD Pipeline, Local Dev"
                required
                autoFocus
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="key-expiry">Expiration</Label>
              <select
                id="key-expiry"
                value={expiryDays}
                onChange={(e) => setExpiryDays(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {EXPIRY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button type="submit" size="sm" disabled={loading || !name.trim()}>
              {loading ? "Creating…" : "Create key"}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={loading}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

// ── Key row ────────────────────────────────────────────────────────────────

function KeyRow({
  apiKey,
  onRevoke,
  onRotate,
  onDelete,
}: {
  apiKey: ApiKeyResponse;
  onRevoke: (id: string) => Promise<void>;
  onRotate: (id: string) => Promise<CreateApiKeyResponse>;
  onDelete: (id: string) => Promise<void>;
}) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [rotatedKey, setRotatedKey] = useState<CreateApiKeyResponse | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function handleRevoke() {
    setActionLoading("revoke");
    try { await onRevoke(apiKey.id); } finally { setActionLoading(null); }
  }

  async function handleRotate() {
    setActionLoading("rotate");
    try {
      const newKey = await onRotate(apiKey.id);
      setRotatedKey(newKey);
    } finally { setActionLoading(null); }
  }

  async function handleDelete() {
    setActionLoading("delete");
    try { await onDelete(apiKey.id); } finally { setActionLoading(null); }
  }

  return (
    <div className="space-y-3">
      {rotatedKey && (
        <NewKeyBanner rawKey={rotatedKey.raw_key} onDismiss={() => setRotatedKey(null)} />
      )}
      <div className="flex items-center justify-between gap-4 rounded-xl border border-border bg-background px-4 py-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Key className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-foreground">{apiKey.name}</span>
              <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {apiKey.key_prefix}…
              </code>
              {apiKey.is_active ? (
                <Badge variant="outline" className="text-xs text-green-500 border-green-500/30">
                  Active
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs text-red-500 border-red-500/30">
                  Revoked
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Created {formatDate(apiKey.created_at)}
              {apiKey.last_used_at && ` · Last used ${formatDate(apiKey.last_used_at)}`}
              {apiKey.expires_at && ` · Expires ${formatDate(apiKey.expires_at)}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {apiKey.is_active && (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                disabled={actionLoading !== null}
                onClick={handleRotate}
                title="Rotate key"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Rotate
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 gap-1.5 text-xs text-amber-500 hover:text-amber-600 hover:bg-amber-500/10"
                disabled={actionLoading !== null}
                onClick={handleRevoke}
                title="Revoke key"
              >
                <XCircle className="h-3.5 w-3.5" />
                Revoke
              </Button>
            </>
          )}
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <span className="text-xs text-muted-foreground">Delete?</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs text-red-500 hover:bg-red-500/10"
                disabled={actionLoading !== null}
                onClick={handleDelete}
              >
                Yes
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => setConfirmDelete(false)}
              >
                No
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 gap-1.5 text-xs text-red-500 hover:text-red-600 hover:bg-red-500/10"
              disabled={actionLoading !== null}
              onClick={() => setConfirmDelete(true)}
              title="Delete key"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyBanner, setNewKeyBanner] = useState<CreateApiKeyResponse | null>(null);

  const fetchKeys = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listApiKeys();
      setKeys(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  async function handleCreated(key: CreateApiKeyResponse) {
    setShowCreate(false);
    setNewKeyBanner(key);
    await fetchKeys();
  }

  async function handleRevoke(id: string) {
    await revokeApiKey(id);
    await fetchKeys();
  }

  async function handleRotate(id: string): Promise<CreateApiKeyResponse> {
    const newKey = await rotateApiKey(id);
    await fetchKeys();
    return newKey;
  }

  async function handleDelete(id: string) {
    await deleteApiKey(id);
    await fetchKeys();
  }

  const activeKeys = keys.filter((k) => k.is_active);
  const revokedKeys = keys.filter((k) => !k.is_active);

  return (
    <div className="max-w-2xl space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">API Keys</h2>
          <p className="text-sm text-muted-foreground">
            Create and manage API keys for programmatic access.
          </p>
        </div>
        {!showCreate && (
          <Button size="sm" onClick={() => setShowCreate(true)} className="shrink-0 gap-1.5">
            <Plus className="h-4 w-4" />
            New key
          </Button>
        )}
      </div>

      {/* New key banner */}
      {newKeyBanner && (
        <NewKeyBanner rawKey={newKeyBanner.raw_key} onDismiss={() => setNewKeyBanner(null)} />
      )}

      {/* Create form */}
      {showCreate && (
        <CreateKeyForm
          onCreated={handleCreated}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />
          ))}
        </div>
      )}

      {/* Active keys */}
      {!loading && (
        <div className="space-y-6">
          {activeKeys.length === 0 && revokedKeys.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card py-16 gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                <Key className="h-6 w-6 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">No API keys yet</p>
                <p className="text-xs text-muted-foreground">Create a key to access the API programmatically.</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => setShowCreate(true)} className="gap-1.5 mt-1">
                <Plus className="h-3.5 w-3.5" /> Create your first key
              </Button>
            </div>
          ) : (
            <>
              {activeKeys.length > 0 && (
                <section className="space-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                    Active — {activeKeys.length}
                  </h3>
                  {activeKeys.map((k) => (
                    <KeyRow
                      key={k.id}
                      apiKey={k}
                      onRevoke={handleRevoke}
                      onRotate={handleRotate}
                      onDelete={handleDelete}
                    />
                  ))}
                </section>
              )}

              {revokedKeys.length > 0 && (
                <section className="space-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                    Revoked — {revokedKeys.length}
                  </h3>
                  {revokedKeys.map((k) => (
                    <KeyRow
                      key={k.id}
                      apiKey={k}
                      onRevoke={handleRevoke}
                      onRotate={handleRotate}
                      onDelete={handleDelete}
                    />
                  ))}
                </section>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
