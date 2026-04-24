"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listOrganizations, createOrganization } from "@/lib/api";
import type { Organization, OrgCreate } from "@/types/api";

type OrgsState =
  | { status: "loading" }
  | { status: "ok"; items: Organization[] }
  | { status: "error"; message: string };

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<OrgsState>({ status: "loading" });
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<OrgCreate>({ name: "", slug: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function reload() {
    listOrganizations({ q: q || undefined })
      .then((items) => setOrgs({ status: "ok", items }))
      .catch((err: unknown) => setOrgs({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    let cancelled = false;
    setOrgs({ status: "loading" });
    listOrganizations({ q: q || undefined })
      .then((items) => { if (!cancelled) setOrgs({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setOrgs({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [q]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createOrganization(formData);
      setShowForm(false);
      setFormData({ name: "", slug: "" });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create organization");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Organizations</h1>
          <p className="page-subtitle">Companies and teams in your network</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Organization"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>New Organization</h3>
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="erp-form-group">
                <label className="erp-label">Name *</label>
                <input className="erp-input" required value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Slug *</label>
                <input className="erp-input" required value={formData.slug} onChange={e => setFormData({ ...formData, slug: e.target.value })} placeholder="lowercase-with-hyphens" />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Industry</label>
                <input className="erp-input" value={formData.industry ?? ""} onChange={e => setFormData({ ...formData, industry: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Website</label>
                <input className="erp-input" value={formData.website ?? ""} onChange={e => setFormData({ ...formData, website: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Phone</label>
                <input className="erp-input" value={formData.phone ?? ""} onChange={e => setFormData({ ...formData, phone: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Email</label>
                <input type="email" className="erp-input" value={formData.email ?? ""} onChange={e => setFormData({ ...formData, email: e.target.value || undefined })} />
              </div>
            </div>
            {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create Organization"}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="filter-bar">
        <div className="filter-group" style={{ flex: 1 }}>
          <span className="filter-label">Search</span>
          <input
            className="erp-input"
            style={{ maxWidth: 280 }}
            placeholder="Organization name…"
            value={q}
            onChange={e => setQ(e.target.value)}
          />
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {orgs.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading organizations…</p>}
        {orgs.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)" }}>
            Failed to load organizations: {orgs.message}
          </div>
        )}
        {orgs.status === "ok" && orgs.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 13 }}>No organizations found.</div>
        )}
        {orgs.status === "ok" && orgs.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Industry</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Website</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Contacts</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Deals</th>
                </tr>
              </thead>
              <tbody>
                {orgs.items.map((org) => (
                  <tr key={org.id} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium">
                      <Link href={`/organizations/${org.id}`} className="hover:underline" style={{ color: "var(--text-primary)" }}>
                        {org.name}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{org.industry ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{org.website ?? "—"}</td>
                    <td className="px-4 py-2.5 text-center font-mono text-sm" style={{ color: "var(--text-secondary)" }}>{org.contact_count}</td>
                    <td className="px-4 py-2.5 text-center font-mono text-sm" style={{ color: "var(--text-secondary)" }}>{org.deal_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
