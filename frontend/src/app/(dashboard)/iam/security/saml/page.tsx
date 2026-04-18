"use client";

import { useState } from "react";

import {
  useCreateSamlProvider,
  useDeleteSamlProvider,
  useSamlProviders,
} from "@/features/iam/hooks/use-saml-providers";
import type { SamlProviderCreateBody } from "@/types/api";

const EMPTY_FORM: SamlProviderCreateBody = {
  idp_entity_id: "",
  sso_url: "",
  x509_cert: "",
  sp_entity_id: "",
  enabled: true,
};

export default function SAMLPage() {
  const { data: providers = [], isLoading } = useSamlProviders();
  const createMutation = useCreateSamlProvider();
  const deleteMutation = useDeleteSamlProvider();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<SamlProviderCreateBody>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  function handleInput(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await createMutation.mutateAsync(form);
      setShowForm(false);
      setForm(EMPTY_FORM);
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
      <h1 className="text-2xl font-semibold mb-1">SAML 2.0 SSO</h1>
      <p className="text-sm text-gray-500 mb-6">
        Configure SAML 2.0 Identity Providers for SP-initiated SSO.
      </p>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading…</p>
      ) : providers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
          No SAML providers configured yet. Add one below.
        </div>
      ) : (
        <table className="w-full text-sm border rounded-lg overflow-hidden mb-6">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-2">IdP Entity ID</th>
              <th className="text-left px-4 py-2">SSO URL</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="px-4 py-2 font-mono text-xs truncate max-w-xs">{p.idp_entity_id}</td>
                <td className="px-4 py-2 text-gray-600 truncate max-w-xs">{p.sso_url}</td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {p.enabled ? "Enabled" : "Disabled"}
                  </span>
                </td>
                <td className="px-4 py-2 flex gap-2">
                  <a
                    href={`/v1/auth/saml/${p.org_slug}/metadata`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline text-xs"
                  >
                    Metadata
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
        <form onSubmit={handleSubmit} className="border rounded-lg p-6 bg-gray-50 space-y-4">
          <h2 className="text-base font-semibold">Add SAML Provider</h2>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          {[
            { label: "IdP Entity ID", name: "idp_entity_id", placeholder: "https://idp.example.com/saml2/metadata" },
            { label: "IdP SSO URL", name: "sso_url", placeholder: "https://idp.example.com/saml2/sso" },
            { label: "SP Entity ID", name: "sp_entity_id", placeholder: "https://tennetctl.example.com" },
          ].map(({ label, name, placeholder }) => (
            <div key={name}>
              <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
              <input
                name={name}
                value={(form as unknown as Record<string, string>)[name] ?? ""}
                onChange={handleInput}
                placeholder={placeholder}
                required
                className="w-full border rounded px-3 py-1.5 text-sm"
              />
            </div>
          ))}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              IdP x509 Certificate (PEM)
            </label>
            <textarea
              name="x509_cert"
              value={form.x509_cert}
              onChange={handleInput}
              rows={6}
              required
              placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
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
