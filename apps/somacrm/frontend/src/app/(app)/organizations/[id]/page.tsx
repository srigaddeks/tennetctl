"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getOrganization, updateOrganization,
  listContacts,
  listAddresses, createAddress,
  listDeals,
} from "@/lib/api";
import type {
  Organization, OrgUpdate,
  Contact,
  Address, AddressCreate,
  Deal,
} from "@/types/api";

type Tab = "overview" | "contacts" | "addresses" | "deals";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

export default function OrgDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [tab, setTab] = useState<Tab>("overview");
  const [org, setOrg] = useState<State<Organization>>({ status: "loading" });
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<OrgUpdate>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [contacts, setContacts] = useState<State<Contact[]>>({ status: "loading" });
  const [addresses, setAddresses] = useState<State<Address[]>>({ status: "loading" });
  const [deals, setDeals] = useState<State<Deal[]>>({ status: "loading" });
  const [addrForm, setAddrForm] = useState<AddressCreate | null>(null);

  useEffect(() => {
    getOrganization(id)
      .then((data) => { setOrg({ status: "ok", data }); setEditData({}); })
      .catch((err: unknown) => setOrg({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [id]);

  useEffect(() => {
    if (tab === "contacts") {
      listContacts({ organization_id: id })
        .then((items) => setContacts({ status: "ok", data: items }))
        .catch((err: unknown) => setContacts({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
    if (tab === "addresses") {
      listAddresses({ entity_type: "organization", entity_id: id })
        .then((items) => setAddresses({ status: "ok", data: items }))
        .catch((err: unknown) => setAddresses({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
    if (tab === "deals") {
      listDeals({ organization_id: id })
        .then((items) => setDeals({ status: "ok", data: items }))
        .catch((err: unknown) => setDeals({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
  }, [tab, id]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const updated = await updateOrganization(id, editData);
      setOrg({ status: "ok", data: updated });
      setEditing(false);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to update");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddAddress(e: React.FormEvent) {
    e.preventDefault();
    if (!addrForm) return;
    setSaving(true);
    setFormError(null);
    try {
      await createAddress(addrForm);
      setAddrForm(null);
      listAddresses({ entity_type: "organization", entity_id: id })
        .then((items) => setAddresses({ status: "ok", data: items }))
        .catch(() => {});
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add address");
    } finally {
      setSaving(false);
    }
  }

  if (org.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading…</div>;
  if (org.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{org.message}</div>;

  const o = org.data;

  return (
    <div className="max-w-4xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">{o.name}</h1>
          <p className="page-subtitle">{o.industry ?? ""}{o.website ? ` · ${o.website}` : ""}</p>
        </div>
        <button className="btn-secondary" onClick={() => { setEditing(!editing); setFormError(null); }}>
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      <div className="flex gap-1 mb-6" style={{ borderBottom: "1px solid var(--border)" }}>
        {(["overview", "contacts", "addresses", "deals"] as Tab[]).map((t) => (
          <button key={t} onClick={() => { setTab(t); setFormError(null); }} style={{ padding: "8px 16px", fontSize: 13, fontWeight: 600, border: "none", background: "none", cursor: "pointer", borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent", color: tab === t ? "var(--accent)" : "var(--text-secondary)", textTransform: "capitalize" }}>
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          {editing ? (
            <form onSubmit={handleSave}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {[
                  { label: "Name", key: "name" as const, defaultVal: o.name },
                  { label: "Slug", key: "slug" as const, defaultVal: o.slug },
                  { label: "Industry", key: "industry" as const, defaultVal: o.industry ?? "" },
                  { label: "Website", key: "website" as const, defaultVal: o.website ?? "" },
                  { label: "Phone", key: "phone" as const, defaultVal: o.phone ?? "" },
                  { label: "Email", key: "email" as const, defaultVal: o.email ?? "" },
                ].map(({ label, key, defaultVal }) => (
                  <div className="erp-form-group" key={key}>
                    <label className="erp-label">{label}</label>
                    <input className="erp-input" defaultValue={defaultVal} onChange={e => setEditData({ ...editData, [key]: e.target.value || undefined })} />
                  </div>
                ))}
                <div className="erp-form-group col-span-2">
                  <label className="erp-label">Description</label>
                  <textarea className="erp-textarea" defaultValue={o.description ?? ""} onChange={e => setEditData({ ...editData, description: e.target.value || undefined })} />
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
              <div className="flex gap-3">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Save Changes"}</button>
                <button type="button" className="btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </form>
          ) : (
            <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
              {[
                { label: "Name", value: o.name },
                { label: "Slug", value: o.slug },
                { label: "Industry", value: o.industry },
                { label: "Website", value: o.website },
                { label: "Phone", value: o.phone },
                { label: "Email", value: o.email },
                { label: "Employee Count", value: o.employee_count?.toString() },
                { label: "Annual Revenue", value: o.annual_revenue ? `$${o.annual_revenue.toLocaleString()}` : null },
                { label: "Contacts", value: o.contact_count.toString() },
                { label: "Deals", value: o.deal_count.toString() },
              ].map(({ label, value }) => value ? (
                <div key={label}>
                  <dt style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 2 }}>{label}</dt>
                  <dd style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{value}</dd>
                </div>
              ) : null)}
              {o.description && (
                <div className="col-span-2">
                  <dt style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 2 }}>Description</dt>
                  <dd style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{o.description}</dd>
                </div>
              )}
            </dl>
          )}
        </div>
      )}

      {tab === "contacts" && (
        <div>
          {contacts.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {contacts.status === "ok" && contacts.data.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No linked contacts.</p>
          )}
          {contacts.status === "ok" && contacts.data.map((c) => (
            <div key={c.id} className="rounded border p-4 mb-3 flex items-center justify-between" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--text-primary)" }}>{c.full_name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.email ?? ""}{c.job_title ? ` · ${c.job_title}` : ""}</div>
              </div>
              <Link href={`/contacts/${c.id}`} style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none" }}>View →</Link>
            </div>
          ))}
        </div>
      )}

      {tab === "addresses" && (
        <div>
          <div className="flex justify-end mb-4">
            <button className="btn-primary" onClick={() => setAddrForm({ entity_type: "organization", entity_id: id, address_type_id: 2 })}>
              + Add Address
            </button>
          </div>
          {addrForm && (
            <form onSubmit={handleAddAddress} className="rounded border p-4 mb-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                {(["street", "city", "state", "country", "postal_code"] as const).map((key) => (
                  <div className="erp-form-group" key={key}>
                    <label className="erp-label">{key.replace("_", " ")}</label>
                    <input className="erp-input" onChange={e => setAddrForm({ ...addrForm, [key]: e.target.value || undefined })} />
                  </div>
                ))}
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Add Address"}</button>
                <button type="button" className="btn-secondary" onClick={() => setAddrForm(null)}>Cancel</button>
              </div>
            </form>
          )}
          {addresses.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {addresses.status === "ok" && addresses.data.map((addr) => (
            <div key={addr.id} className="rounded border p-4 mb-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 4 }}>{addr.address_type}</div>
              <div style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{addr.full_address ?? [addr.street, addr.city, addr.state, addr.country].filter(Boolean).join(", ")}</div>
            </div>
          ))}
        </div>
      )}

      {tab === "deals" && (
        <div>
          {deals.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {deals.status === "ok" && deals.data.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No linked deals.</p>
          )}
          {deals.status === "ok" && deals.data.map((deal) => (
            <div key={deal.id} className="rounded border p-4 mb-3 flex items-center justify-between" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--text-primary)" }}>{deal.title}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  {deal.stage_name ?? "No stage"} · {deal.value ? `$${deal.value.toLocaleString()}` : "No value"} · {deal.status}
                </div>
              </div>
              <Link href={`/deals`} style={{ fontSize: 12, color: "var(--accent)", textDecoration: "none" }}>View</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
