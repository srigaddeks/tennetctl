"use client";

import { useState } from "react";

import {
  useCreateOidcProvider,
  useDeleteOidcProvider,
  useOidcProviders,
} from "@/features/iam/hooks/use-oidc-providers";
import type { OidcProviderCreateBody } from "@/types/api";

const DEFAULT_CLAIM_MAPPING = JSON.stringify(
  { email: "email", name: "name", sub: "sub" },
  null,
  2,
);
const DEFAULT_SCOPES = "openid email profile";

export default function SSOPage() {
  const { data: providers = [], isLoading } = useOidcProviders();
  const createMutation = useCreateOidcProvider();
  const deleteMutation = useDeleteOidcProvider();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<OidcProviderCreateBody>({
    slug: "",
    issuer: "",
    client_id: "",
    client_secret_vault_key: "",
    scopes: DEFAULT_SCOPES,
    claim_mapping: { email: "email", name: "name", sub: "sub" },
  });
  const [claimMappingRaw, setClaimMappingRaw] =
    useState(DEFAULT_CLAIM_MAPPING);
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  function handleInput(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    if (name === "claim_mapping_raw") {
      setClaimMappingRaw(value);
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    let parsedMapping: Record<string, string>;
    try {
      parsedMapping = JSON.parse(claimMappingRaw);
    } catch {
      setFormError("Claim mapping must be valid JSON.");
      return;
    }
    try {
      await createMutation.mutateAsync({ ...form, claim_mapping: parsedMapping });
      setShowForm(false);
      setForm({
        slug: "", issuer: "", client_id: "", client_secret_vault_key: "",
        scopes: DEFAULT_SCOPES,
        claim_mapping: { email: "email", name: "name", sub: "sub" },
      });
      setClaimMappingRaw(DEFAULT_CLAIM_MAPPING);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create provider.");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync(id);
    } catch {
      // silent
    } finally {
      setConfirmDeleteId(null);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-semibold mb-1">Single Sign-On</h1>
      <p className="text-sm text-gray-500 mb-6">
        Configure OIDC providers for your organisation.
      </p>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : providers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
          No OIDC providers configured yet. Add one below.
        </div>
      ) : (
        <table className="w-full text-sm border rounded-lg overflow-hidden mb-6">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-2">Slug</th>
              <th className="text-left px-4 py-2">Issuer</th>
              <th className="text-left px-4 py-2">Client ID</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="px-4 py-2 font-mono">{p.slug}</td>
                <td className="px-4 py-2 text-gray-600 truncate max-w-xs">{p.issuer}</td>
                <td className="px-4 py-2 font-mono text-xs">{p.client_id}</td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.enabled
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {p.enabled ? "Enabled" : "Disabled"}
                  </span>
                </td>
                <td className="px-4 py-2 flex gap-2">
                  <a
                    href={`/v1/auth/oidc/${p.org_slug ?? "default"}/initiate?provider=${p.slug}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline text-xs"
                  >
                    Test
                  </a>
                  {confirmDeleteId === p.id ? (
                    <>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="text-red-600 text-xs hover:underline"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => setConfirmDeleteId(null)}
                        className="text-gray-500 text-xs hover:underline"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setConfirmDeleteId(p.id)}
                      className="text-red-500 text-xs hover:underline"
                    >
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <button
        onClick={() => setShowForm((v) => !v)}
        className="mb-4 text-sm font-medium text-blue-600 hover:underline"
      >
        {showForm ? "Cancel" : "+ Add Provider"}
      </button>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="border rounded-lg p-6 bg-gray-50 space-y-4"
        >
          <h2 className="text-base font-semibold">Add OIDC Provider</h2>
          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}
          {[
            { label: "Provider slug", name: "slug", placeholder: "okta" },
            { label: "Issuer URL", name: "issuer", placeholder: "https://your-idp.example.com" },
            { label: "Client ID", name: "client_id", placeholder: "client_123" },
            {
              label: "Vault key for secret",
              name: "client_secret_vault_key",
              placeholder: "iam.oidc.acme.secret",
            },
            {
              label: "Scopes",
              name: "scopes",
              placeholder: "openid email profile",
            },
          ].map(({ label, name, placeholder }) => (
            <div key={name}>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {label}
              </label>
              <input
                name={name}
                value={(form as unknown as Record<string, string>)[name] ?? ""}
                onChange={handleInput}
                placeholder={placeholder}
                required={name !== "scopes"}
                className="w-full border rounded px-3 py-1.5 text-sm"
              />
            </div>
          ))}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Claim mapping (JSON)
            </label>
            <textarea
              name="claim_mapping_raw"
              value={claimMappingRaw}
              onChange={handleInput}
              rows={4}
              className="w-full border rounded px-3 py-1.5 text-sm font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {createMutation.isPending ? "Saving…" : "Save Provider"}
          </button>
        </form>
      )}
    </div>
  );
}
