"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  getContact, updateContact,
  listAddresses, createAddress,
  listActivities, createActivity,
  listNotes, createNote, updateNote,
} from "@/lib/api";
import type {
  Contact, ContactUpdate,
  Address, AddressCreate,
  Activity, ActivityCreate,
  Note, NoteCreate,
} from "@/types/api";

type Tab = "overview" | "addresses" | "activities" | "notes";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

export default function ContactDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [tab, setTab] = useState<Tab>("overview");
  const [contact, setContact] = useState<State<Contact>>({ status: "loading" });
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<ContactUpdate>({});
  const [saving, setSaving] = useState(false);

  const [addresses, setAddresses] = useState<State<Address[]>>({ status: "loading" });
  const [activities, setActivities] = useState<State<Activity[]>>({ status: "loading" });
  const [notes, setNotes] = useState<State<Note[]>>({ status: "loading" });

  const [addrForm, setAddrForm] = useState<AddressCreate | null>(null);
  const [activityForm, setActivityForm] = useState<ActivityCreate | null>(null);
  const [noteForm, setNoteForm] = useState<NoteCreate | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    getContact(id)
      .then((data) => { setContact({ status: "ok", data }); setEditData({}); })
      .catch((err: unknown) => setContact({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [id]);

  useEffect(() => {
    if (tab === "addresses") {
      listAddresses({ entity_type: "contact", entity_id: id })
        .then((items) => setAddresses({ status: "ok", data: items }))
        .catch((err: unknown) => setAddresses({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
    if (tab === "activities") {
      listActivities({ entity_type: "contact", entity_id: id })
        .then((items) => setActivities({ status: "ok", data: items }))
        .catch((err: unknown) => setActivities({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
    if (tab === "notes") {
      listNotes({ entity_type: "contact", entity_id: id })
        .then((items) => setNotes({ status: "ok", data: items }))
        .catch((err: unknown) => setNotes({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
  }, [tab, id]);

  async function handleSaveContact(e: React.FormEvent) {
    e.preventDefault();
    if (contact.status !== "ok") return;
    setSaving(true);
    try {
      const updated = await updateContact(id, editData);
      setContact({ status: "ok", data: updated });
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
      listAddresses({ entity_type: "contact", entity_id: id })
        .then((items) => setAddresses({ status: "ok", data: items }))
        .catch(() => {});
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add address");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddActivity(e: React.FormEvent) {
    e.preventDefault();
    if (!activityForm) return;
    setSaving(true);
    setFormError(null);
    try {
      await createActivity({ ...activityForm, entity_type: "contact", entity_id: id });
      setActivityForm(null);
      listActivities({ entity_type: "contact", entity_id: id })
        .then((items) => setActivities({ status: "ok", data: items }))
        .catch(() => {});
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add activity");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    if (!noteForm) return;
    setSaving(true);
    setFormError(null);
    try {
      await createNote({ ...noteForm, entity_type: "contact", entity_id: id });
      setNoteForm(null);
      listNotes({ entity_type: "contact", entity_id: id })
        .then((items) => setNotes({ status: "ok", data: items }))
        .catch(() => {});
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add note");
    } finally {
      setSaving(false);
    }
  }

  async function handlePinNote(noteId: string, isPinned: boolean) {
    await updateNote(noteId, { is_pinned: !isPinned });
    listNotes({ entity_type: "contact", entity_id: id })
      .then((items) => setNotes({ status: "ok", data: items }))
      .catch(() => {});
  }

  if (contact.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading…</div>;
  if (contact.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{contact.message}</div>;

  const c = contact.data;

  return (
    <div className="max-w-4xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">{c.full_name}</h1>
          <p className="page-subtitle">{c.job_title ?? ""}{c.company_name ? ` · ${c.company_name}` : ""}</p>
        </div>
        <button className="btn-secondary" onClick={() => { setEditing(!editing); setFormError(null); }}>
          {editing ? "Cancel" : "Edit"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6" style={{ borderBottom: "1px solid var(--border)" }}>
        {(["overview", "addresses", "activities", "notes"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setFormError(null); }}
            style={{
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 600,
              border: "none",
              background: "none",
              cursor: "pointer",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === t ? "var(--accent)" : "var(--text-secondary)",
              textTransform: "capitalize",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          {editing ? (
            <form onSubmit={handleSaveContact}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {[
                  { label: "First Name", key: "first_name" as const, defaultVal: c.first_name },
                  { label: "Last Name", key: "last_name" as const, defaultVal: c.last_name ?? "" },
                  { label: "Email", key: "email" as const, defaultVal: c.email ?? "" },
                  { label: "Phone", key: "phone" as const, defaultVal: c.phone ?? "" },
                  { label: "Mobile", key: "mobile" as const, defaultVal: c.mobile ?? "" },
                  { label: "Job Title", key: "job_title" as const, defaultVal: c.job_title ?? "" },
                  { label: "Company", key: "company_name" as const, defaultVal: c.company_name ?? "" },
                  { label: "Website", key: "website" as const, defaultVal: c.website ?? "" },
                ].map(({ label, key, defaultVal }) => (
                  <div className="erp-form-group" key={key}>
                    <label className="erp-label">{label}</label>
                    <input
                      className="erp-input"
                      defaultValue={defaultVal}
                      onChange={e => setEditData({ ...editData, [key]: e.target.value || undefined })}
                    />
                  </div>
                ))}
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
                { label: "Full Name", value: c.full_name },
                { label: "Email", value: c.email },
                { label: "Phone", value: c.phone },
                { label: "Mobile", value: c.mobile },
                { label: "Job Title", value: c.job_title },
                { label: "Company", value: c.company_name },
                { label: "Organization", value: c.organization_name },
                { label: "Website", value: c.website },
                { label: "LinkedIn", value: c.linkedin_url },
                { label: "Twitter", value: c.twitter_handle },
                { label: "Lead Source", value: c.lead_source },
                { label: "Status", value: c.status },
              ].map(({ label, value }) => value ? (
                <div key={label}>
                  <dt style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 2 }}>{label}</dt>
                  <dd style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{value}</dd>
                </div>
              ) : null)}
            </dl>
          )}
        </div>
      )}

      {tab === "addresses" && (
        <div>
          <div className="flex justify-end mb-4">
            <button className="btn-primary" onClick={() => setAddrForm({ entity_type: "contact", entity_id: id, address_type_id: 2 })}>
              + Add Address
            </button>
          </div>

          {addrForm && (
            <form onSubmit={handleAddAddress} className="rounded border p-4 mb-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                {[
                  { label: "Street", key: "street" as const },
                  { label: "City", key: "city" as const },
                  { label: "State", key: "state" as const },
                  { label: "Country", key: "country" as const },
                  { label: "Postal Code", key: "postal_code" as const },
                ].map(({ label, key }) => (
                  <div className="erp-form-group" key={key}>
                    <label className="erp-label">{label}</label>
                    <input className="erp-input" onChange={e => setAddrForm({ ...addrForm, [key]: e.target.value || undefined })} />
                  </div>
                ))}
                <div className="erp-form-group">
                  <label className="erp-label">Type</label>
                  <select className="erp-select" onChange={e => setAddrForm({ ...addrForm, address_type_id: parseInt(e.target.value) })}>
                    <option value="1">Home</option>
                    <option value="2" selected>Office</option>
                    <option value="3">Billing</option>
                    <option value="4">Delivery</option>
                    <option value="5">Other</option>
                  </select>
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Add Address"}</button>
                <button type="button" className="btn-secondary" onClick={() => setAddrForm(null)}>Cancel</button>
              </div>
            </form>
          )}

          {addresses.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {addresses.status === "ok" && addresses.data.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No addresses yet.</p>
          )}
          {addresses.status === "ok" && addresses.data.map((addr) => (
            <div key={addr.id} className="rounded border p-4 mb-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 4 }}>
                {addr.address_type}{addr.is_primary ? " · Primary" : ""}
              </div>
              <div style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{addr.full_address ?? [addr.street, addr.city, addr.state, addr.country].filter(Boolean).join(", ")}</div>
            </div>
          ))}
        </div>
      )}

      {tab === "activities" && (
        <div>
          <div className="flex justify-end mb-4">
            <button className="btn-primary" onClick={() => setActivityForm({ activity_type_id: 1, title: "" })}>
              + Add Activity
            </button>
          </div>

          {activityForm && (
            <form onSubmit={handleAddActivity} className="rounded border p-4 mb-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="erp-form-group">
                  <label className="erp-label">Title *</label>
                  <input className="erp-input" required value={activityForm.title} onChange={e => setActivityForm({ ...activityForm, title: e.target.value })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Type</label>
                  <select className="erp-select" onChange={e => setActivityForm({ ...activityForm, activity_type_id: parseInt(e.target.value) })}>
                    <option value="1">Task</option>
                    <option value="2">Call</option>
                    <option value="3">Email</option>
                    <option value="4">Meeting</option>
                    <option value="5">Note</option>
                  </select>
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Due Date</label>
                  <input type="datetime-local" className="erp-input" onChange={e => setActivityForm({ ...activityForm, due_at: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group col-span-2">
                  <label className="erp-label">Description</label>
                  <textarea className="erp-textarea" onChange={e => setActivityForm({ ...activityForm, description: e.target.value || undefined })} />
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Add Activity"}</button>
                <button type="button" className="btn-secondary" onClick={() => setActivityForm(null)}>Cancel</button>
              </div>
            </form>
          )}

          {activities.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {activities.status === "ok" && activities.data.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No activities yet.</p>
          )}
          {activities.status === "ok" && activities.data.map((act) => (
            <div key={act.id} className="rounded border p-4 mb-3 flex gap-3" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <span style={{ fontSize: 20, flexShrink: 0 }}>{act.activity_type_icon}</span>
              <div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--text-primary)" }}>{act.title}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                  {act.activity_type_label} · {act.status}{act.due_at ? ` · Due ${new Date(act.due_at).toLocaleDateString()}` : ""}
                </div>
                {act.description && <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>{act.description}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "notes" && (
        <div>
          <div className="flex justify-end mb-4">
            <button className="btn-primary" onClick={() => setNoteForm({ entity_type: "contact", entity_id: id, content: "" })}>
              + Add Note
            </button>
          </div>

          {noteForm && (
            <form onSubmit={handleAddNote} className="rounded border p-4 mb-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="erp-form-group mb-3">
                <label className="erp-label">Note *</label>
                <textarea className="erp-textarea" required value={noteForm.content} onChange={e => setNoteForm({ ...noteForm, content: e.target.value })} />
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Add Note"}</button>
                <button type="button" className="btn-secondary" onClick={() => setNoteForm(null)}>Cancel</button>
              </div>
            </form>
          )}

          {notes.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</p>}
          {notes.status === "ok" && notes.data.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No notes yet.</p>
          )}
          {notes.status === "ok" && [...notes.data].sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned)).map((note) => (
            <div key={note.id} className="rounded border p-4 mb-3" style={{ backgroundColor: note.is_pinned ? "#FFFBEB" : "var(--bg-card)", borderColor: note.is_pinned ? "#FDE68A" : "var(--border)" }}>
              <div className="flex items-start justify-between">
                <p style={{ fontSize: 13.5, color: "var(--text-primary)", flex: 1 }}>{note.content}</p>
                <button onClick={() => handlePinNote(note.id, note.is_pinned)} style={{ marginLeft: 8, fontSize: 12, color: note.is_pinned ? "#D97706" : "var(--text-muted)", background: "none", border: "none", cursor: "pointer" }}>
                  {note.is_pinned ? "Unpin" : "Pin"}
                </button>
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                {new Date(note.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
