"use client";

import { useState } from "react";

import {
  useCreateScimToken,
  useRevokeScimToken,
  useScimTokens,
} from "@/features/iam/hooks/use-scim-tokens";

export default function SCIMPage() {
  const { data: tokens = [], isLoading } = useScimTokens();
  const createMutation = useCreateScimToken();
  const revokeMutation = useRevokeScimToken();

  const [label, setLabel] = useState("");
  const [newToken, setNewToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNewToken(null);
    try {
      const result = await createMutation.mutateAsync({ label });
      setNewToken(result.token);
      setLabel("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create token.");
    }
  }

  async function handleRevoke(id: string) {
    try {
      await revokeMutation.mutateAsync(id);
      setConfirmId(null);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold">SCIM Provisioning</h1>
        <p className="text-sm text-gray-500 mt-1">
          Generate bearer tokens for SCIM 2.0 identity providers (Okta, Azure AD, etc.).
        </p>
      </div>

      <form onSubmit={handleCreate} className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Token label</label>
          <input
            className="w-full border rounded px-3 py-2 text-sm"
            placeholder="e.g. okta-prod"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            required
            data-testid="scim-token-label"
          />
        </div>
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          data-testid="scim-token-create-btn"
        >
          {createMutation.isPending ? "Creating…" : "Create Token"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {newToken && (
        <div className="border border-green-300 bg-green-50 rounded p-4 text-sm space-y-1">
          <p className="font-medium text-green-800">Token created — copy it now. It won&apos;t be shown again.</p>
          <code className="block font-mono break-all text-green-900 select-all" data-testid="scim-new-token">
            {newToken}
          </code>
          <button className="text-xs text-green-700 underline" onClick={() => setNewToken(null)}>
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-2">
        <h2 className="text-sm font-medium text-gray-700">Active tokens</h2>
        {isLoading && <p className="text-sm text-gray-400">Loading…</p>}
        {!isLoading && tokens.length === 0 && (
          <p className="text-sm text-gray-400">No active SCIM tokens.</p>
        )}
        {tokens.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between border rounded px-4 py-3 text-sm"
            data-testid="scim-token-row"
          >
            <div>
              <p className="font-medium">{t.label}</p>
              <p className="text-gray-400 text-xs">
                Created {new Date(t.created_at).toLocaleDateString()}
                {t.last_used_at && ` · Last used ${new Date(t.last_used_at).toLocaleDateString()}`}
              </p>
            </div>
            {confirmId === t.id ? (
              <div className="flex gap-2">
                <button
                  className="text-red-600 text-xs hover:underline"
                  onClick={() => handleRevoke(t.id)}
                  data-testid="scim-token-confirm-revoke"
                >
                  Confirm revoke
                </button>
                <button className="text-gray-500 text-xs hover:underline" onClick={() => setConfirmId(null)}>
                  Cancel
                </button>
              </div>
            ) : (
              <button
                className="text-red-500 text-xs hover:underline"
                onClick={() => setConfirmId(t.id)}
                data-testid="scim-token-revoke-btn"
              >
                Revoke
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="border-t pt-4 text-xs text-gray-500 space-y-1">
        <p className="font-medium">SCIM 2.0 endpoint base URL</p>
        <code className="block font-mono">{typeof window !== "undefined" ? window.location.origin : ""}/scim/v2/&#123;org-slug&#125;</code>
        <p>Users: <code>/Users</code> · Groups: <code>/Groups</code></p>
      </div>
    </div>
  );
}
