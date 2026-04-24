"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  getContact, updateContact,
  getContactTimeline,
  listAddresses, createAddress,
  createActivity, createNote, updateNote,
} from "@/lib/api";
import type {
  Contact, ContactUpdate,
  Address, AddressCreate,
  ActivityCreate, NoteCreate,
  TimelineItem,
} from "@/types/api";

type Tab = "timeline" | "overview" | "addresses";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

// ── Activity type config ────────────────────────────────────────────────────
const TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  whatsapp: { icon: "💬", color: "#16A34A", bg: "#F0FDF4" },
  call:     { icon: "📞", color: "#2563EB", bg: "#EFF6FF" },
  email:    { icon: "✉",  color: "#7C3AED", bg: "#F5F3FF" },
  meeting:  { icon: "📅", color: "#D97706", bg: "#FFFBEB" },
  task:     { icon: "✓",  color: "#6B7280", bg: "#F9FAFB" },
  note:     { icon: "📝", color: "#B45309", bg: "#FFFBEB" },
  sample:   { icon: "🎁", color: "#0891B2", bg: "#ECFEFF" },
};

function typeConfig(item: TimelineItem) {
  if (item.item_type === "note") return TYPE_CONFIG.note;
  const t = item.activity_type ?? "task";
  return TYPE_CONFIG[t] ?? TYPE_CONFIG.task;
}

function formatRelativeDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return `Today ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  if (diffDays === 1) return `Yesterday ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString([], { day: "numeric", month: "short", year: diffDays > 365 ? "numeric" : undefined });
}

// ── Main page ───────────────────────────────────────────────────────────────
export default function ContactDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [tab, setTab] = useState<Tab>("timeline");
  const [contact, setContact] = useState<State<Contact>>({ status: "loading" });
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<ContactUpdate>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [timeline, setTimeline] = useState<State<TimelineItem[]>>({ status: "loading" });
  const [addresses, setAddresses] = useState<State<Address[]>>({ status: "loading" });

  // Quick-add panel state
  const [addMode, setAddMode] = useState<null | "activity" | "note">(null);
  const [activityForm, setActivityForm] = useState<ActivityCreate>({ activity_type_id: 2, title: "" });
  const [noteForm, setNoteForm] = useState<NoteCreate>({ entity_type: "contact", entity_id: id, content: "" });
  const [addrForm, setAddrForm] = useState<AddressCreate | null>(null);

  useEffect(() => {
    getContact(id)
      .then((data) => { setContact({ status: "ok", data }); })
      .catch((err: unknown) => setContact({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [id]);

  function refreshTimeline() {
    setTimeline({ status: "loading" });
    getContactTimeline(id)
      .then((data) => setTimeline({ status: "ok", data }))
      .catch((err: unknown) => setTimeline({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    if (tab === "timeline") refreshTimeline();
    if (tab === "addresses") {
      listAddresses({ entity_type: "contact", entity_id: id })
        .then((items) => setAddresses({ status: "ok", data: items }))
        .catch((err: unknown) => setAddresses({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    } finally { setSaving(false); }
  }

  async function handleAddActivity(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createActivity({ ...activityForm, entity_type: "contact", entity_id: id });
      setAddMode(null);
      setActivityForm({ activity_type_id: 2, title: "" });
      refreshTimeline();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to log");
    } finally { setSaving(false); }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createNote({ ...noteForm, entity_type: "contact", entity_id: id });
      setAddMode(null);
      setNoteForm({ entity_type: "contact", entity_id: id, content: "" });
      refreshTimeline();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add note");
    } finally { setSaving(false); }
  }

  async function handlePinToggle(item: TimelineItem) {
    if (item.item_type !== "note") return;
    await updateNote(item.id, { is_pinned: !item.is_pinned });
    refreshTimeline();
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
    } finally { setSaving(false); }
  }

  if (contact.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading…</div>;
  if (contact.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{contact.message}</div>;

  const c = contact.data;

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 className="page-title">{c.full_name}</h1>
          <p className="page-subtitle">
            {[c.job_title, c.company_name ?? c.organization_name, c.lead_source ? `via ${c.lead_source.replace(/_/g, " ")}` : null].filter(Boolean).join(" · ")}
          </p>
          {/* Quick contact info pills */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
            {c.phone && <a href={`tel:${c.phone}`} style={{ fontSize: 12, color: "#2563EB", textDecoration: "none", background: "#EFF6FF", borderRadius: 20, padding: "2px 10px" }}>📞 {c.phone}</a>}
            {c.email && <a href={`mailto:${c.email}`} style={{ fontSize: 12, color: "#7C3AED", textDecoration: "none", background: "#F5F3FF", borderRadius: 20, padding: "2px 10px" }}>✉ {c.email}</a>}
            <span style={{ fontSize: 12, background: c.status === "active" ? "#ECFDF5" : "#F9FAFB", color: c.status === "active" ? "#059669" : "#6B7280", borderRadius: 20, padding: "2px 10px", fontWeight: 600 }}>{c.status}</span>
          </div>
        </div>
        {/* Quick-add buttons */}
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          <button className="btn-primary" style={{ fontSize: 12, padding: "6px 12px" }} onClick={() => { setAddMode("activity"); setTab("timeline"); }}>
            + Log Interaction
          </button>
          <button className="btn-secondary" style={{ fontSize: 12, padding: "6px 12px" }} onClick={() => { setAddMode("note"); setTab("timeline"); }}>
            + Note
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)", marginBottom: 24 }}>
        {([
          { key: "timeline", label: "Timeline" },
          { key: "overview", label: "Details" },
          { key: "addresses", label: "Addresses" },
        ] as { key: Tab; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => { setTab(key); setFormError(null); setAddMode(null); }}
            style={{
              padding: "8px 18px",
              fontSize: 13,
              fontWeight: tab === key ? 700 : 500,
              border: "none",
              background: "none",
              cursor: "pointer",
              borderBottom: tab === key ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === key ? "var(--accent)" : "var(--text-secondary)",
            }}
          >
            {label}
            {key === "timeline" && timeline.status === "ok" && (
              <span style={{ marginLeft: 6, fontSize: 11, background: "var(--accent)", color: "#fff", borderRadius: 10, padding: "1px 6px" }}>
                {timeline.data.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── TIMELINE TAB ─────────────────────────────────────────────────── */}
      {tab === "timeline" && (
        <div>
          {/* Quick-add form inline at top */}
          {addMode === "activity" && (
            <form onSubmit={handleAddActivity} className="rounded border p-4 mb-6"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", borderLeft: "3px solid #2563EB" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, color: "var(--text-primary)" }}>Log Interaction</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div className="erp-form-group">
                  <label className="erp-label">Type</label>
                  <select className="erp-select" value={activityForm.activity_type_id}
                    onChange={e => setActivityForm({ ...activityForm, activity_type_id: parseInt(e.target.value) })}>
                    <option value="6">💬 WhatsApp</option>
                    <option value="2">📞 Call</option>
                    <option value="3">✉ Email</option>
                    <option value="4">📅 Meeting / Trial Delivery</option>
                    <option value="1">✓ Task</option>
                    <option value="5">📝 Note</option>
                  </select>
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Title *</label>
                  <input className="erp-input" required placeholder="e.g. WhatsApp — intro sent"
                    value={activityForm.title}
                    onChange={e => setActivityForm({ ...activityForm, title: e.target.value })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Date / Time</label>
                  <input type="datetime-local" className="erp-input"
                    onChange={e => setActivityForm({ ...activityForm, due_at: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Duration (min)</label>
                  <input type="number" className="erp-input" placeholder="e.g. 15"
                    onChange={e => setActivityForm({ ...activityForm, duration_minutes: e.target.value ? parseInt(e.target.value) : undefined })} />
                </div>
                <div className="erp-form-group" style={{ gridColumn: "1 / -1" }}>
                  <label className="erp-label">What happened?</label>
                  <textarea className="erp-textarea" placeholder="Details of the interaction…"
                    onChange={e => setActivityForm({ ...activityForm, description: e.target.value || undefined })} />
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Log It"}</button>
                <button type="button" className="btn-secondary" onClick={() => setAddMode(null)}>Cancel</button>
              </div>
            </form>
          )}

          {addMode === "note" && (
            <form onSubmit={handleAddNote} className="rounded border p-4 mb-6"
              style={{ backgroundColor: "#FFFBEB", borderColor: "#FDE68A", borderLeft: "3px solid #D97706" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "var(--text-primary)" }}>Add Note</div>
              <textarea className="erp-textarea" required style={{ minHeight: 80 }}
                placeholder="Write a note about this customer…"
                value={noteForm.content}
                onChange={e => setNoteForm({ ...noteForm, content: e.target.value })} />
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, margin: "8px 0" }}>{formError}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Save Note"}</button>
                <button type="button" className="btn-secondary" onClick={() => setAddMode(null)}>Cancel</button>
              </div>
            </form>
          )}

          {/* Timeline feed */}
          {timeline.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading timeline…</p>}
          {timeline.status === "error" && <p style={{ color: "var(--status-error)", fontSize: 13 }}>{timeline.message}</p>}
          {timeline.status === "ok" && timeline.data.length === 0 && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)", fontSize: 13 }}>
              No interactions yet. Log the first one above.
            </div>
          )}
          {timeline.status === "ok" && (
            <div style={{ position: "relative" }}>
              {/* Vertical line */}
              <div style={{ position: "absolute", left: 19, top: 0, bottom: 0, width: 2, backgroundColor: "var(--border)", zIndex: 0 }} />

              {timeline.data.map((item, i) => {
                const cfg = typeConfig(item);
                const isNote = item.item_type === "note";
                const isPinned = item.is_pinned === true;
                const context = item.deal_title
                  ? `Deal: ${item.deal_title}`
                  : item.lead_title
                  ? `Lead: ${item.lead_title}`
                  : null;

                return (
                  <div key={item.id} style={{ display: "flex", gap: 14, marginBottom: 20, position: "relative", zIndex: 1 }}>
                    {/* Icon bubble */}
                    <div style={{
                      width: 38, height: 38, borderRadius: "50%", flexShrink: 0,
                      backgroundColor: cfg.bg, border: `2px solid ${cfg.color}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 16, boxShadow: "0 0 0 3px var(--bg-main)",
                    }}>
                      {item.item_type === "note" ? "📝" : (item.activity_type_icon ?? "•")}
                    </div>

                    {/* Card */}
                    <div style={{
                      flex: 1,
                      backgroundColor: isPinned ? "#FFFBEB" : "var(--bg-card)",
                      border: `1px solid ${isPinned ? "#FDE68A" : "var(--border)"}`,
                      borderLeft: `3px solid ${cfg.color}`,
                      borderRadius: 8,
                      padding: "10px 14px",
                    }}>
                      {/* Header row */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          {!isNote && (
                            <span style={{ fontSize: 12, fontWeight: 700, color: cfg.color }}>
                              {item.activity_type_label ?? item.activity_type}
                            </span>
                          )}
                          {isNote && <span style={{ fontSize: 12, fontWeight: 700, color: cfg.color }}>Note</span>}
                          {isPinned && <span style={{ fontSize: 10, background: "#FEF3C7", color: "#B45309", borderRadius: 4, padding: "1px 6px", fontWeight: 700 }}>📌 PINNED</span>}
                          {item.status && item.status !== "done" && (
                            <span style={{
                              fontSize: 10, fontWeight: 600, borderRadius: 4, padding: "1px 6px",
                              background: item.status === "pending" ? "#FEF9C3" : "#EFF6FF",
                              color: item.status === "pending" ? "#B45309" : "#2563EB",
                              textTransform: "uppercase",
                            }}>{item.status}</span>
                          )}
                          {context && (
                            <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>
                              ↳ {context}
                            </span>
                          )}
                        </div>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
                          <span style={{ fontSize: 11, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                            {formatRelativeDate(item.event_at)}
                          </span>
                          {isNote && (
                            <button onClick={() => handlePinToggle(item)}
                              style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: "0 4px" }}>
                              {isPinned ? "Unpin" : "Pin"}
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Title (activities) */}
                      {item.title && (
                        <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--text-primary)", marginBottom: item.body ? 4 : 0 }}>
                          {item.title}
                        </div>
                      )}

                      {/* Body */}
                      {item.body && (
                        <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                          {item.body}
                        </div>
                      )}

                      {/* Footer: duration */}
                      {item.duration_minutes && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                          ⏱ {item.duration_minutes} min
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── OVERVIEW TAB ────────────────────────────────────────────────── */}
      {tab === "overview" && (
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          {editing ? (
            <form onSubmit={handleSaveContact}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {([
                  { label: "First Name",  key: "first_name"   as const, defaultVal: c.first_name },
                  { label: "Last Name",   key: "last_name"    as const, defaultVal: c.last_name ?? "" },
                  { label: "Email",       key: "email"        as const, defaultVal: c.email ?? "" },
                  { label: "Phone",       key: "phone"        as const, defaultVal: c.phone ?? "" },
                  { label: "Mobile",      key: "mobile"       as const, defaultVal: c.mobile ?? "" },
                  { label: "Job Title",   key: "job_title"    as const, defaultVal: c.job_title ?? "" },
                  { label: "Company",     key: "company_name" as const, defaultVal: c.company_name ?? "" },
                  { label: "Website",     key: "website"      as const, defaultVal: c.website ?? "" },
                  { label: "LinkedIn",    key: "linkedin_url" as const, defaultVal: c.linkedin_url ?? "" },
                  { label: "Twitter",     key: "twitter_handle" as const, defaultVal: c.twitter_handle ?? "" },
                ]).map(({ label, key, defaultVal }) => (
                  <div className="erp-form-group" key={key}>
                    <label className="erp-label">{label}</label>
                    <input className="erp-input" defaultValue={defaultVal}
                      onChange={e => setEditData({ ...editData, [key]: e.target.value || undefined })} />
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
            <>
              <div className="flex justify-end mb-4">
                <button className="btn-secondary" style={{ fontSize: 12 }} onClick={() => setEditing(true)}>Edit Details</button>
              </div>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
                {([
                  { label: "Full Name",    value: c.full_name },
                  { label: "Email",        value: c.email },
                  { label: "Phone",        value: c.phone },
                  { label: "Mobile",       value: c.mobile },
                  { label: "Job Title",    value: c.job_title },
                  { label: "Company",      value: c.company_name },
                  { label: "Organization", value: c.organization_name },
                  { label: "Website",      value: c.website },
                  { label: "LinkedIn",     value: c.linkedin_url },
                  { label: "Twitter",      value: c.twitter_handle },
                  { label: "Lead Source",  value: c.lead_source },
                  { label: "Status",       value: c.status },
                ] as { label: string; value: string | null | undefined }[]).map(({ label, value }) => value ? (
                  <div key={label}>
                    <dt style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 2 }}>{label}</dt>
                    <dd style={{ fontSize: 13.5, color: "var(--text-primary)" }}>{value}</dd>
                  </div>
                ) : null)}
              </dl>
            </>
          )}
        </div>
      )}

      {/* ── ADDRESSES TAB ───────────────────────────────────────────────── */}
      {tab === "addresses" && (
        <div>
          <div className="flex justify-end mb-4">
            <button className="btn-primary" onClick={() => setAddrForm({ entity_type: "contact", entity_id: id, address_type_id: 4 })}>
              + Add Address
            </button>
          </div>

          {addrForm && (
            <form onSubmit={handleAddAddress} className="rounded border p-4 mb-4"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                {([
                  { label: "Street",      key: "street"      as const },
                  { label: "City",        key: "city"        as const },
                  { label: "State",       key: "state"       as const },
                  { label: "Country",     key: "country"     as const },
                  { label: "Postal Code", key: "postal_code" as const },
                ] as { label: string; key: keyof AddressCreate }[]).map(({ label, key }) => (
                  <div className="erp-form-group" key={key as string}>
                    <label className="erp-label">{label}</label>
                    <input className="erp-input"
                      onChange={e => setAddrForm({ ...addrForm, [key]: e.target.value || undefined })} />
                  </div>
                ))}
                <div className="erp-form-group">
                  <label className="erp-label">Type</label>
                  <select className="erp-select" value={addrForm.address_type_id}
                    onChange={e => setAddrForm({ ...addrForm, address_type_id: parseInt(e.target.value) })}>
                    <option value="1">Home</option>
                    <option value="2">Office</option>
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
            <div key={addr.id} className="rounded border p-4 mb-3"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 4 }}>
                {addr.address_type.replace(/_/g, " ")}{addr.is_primary ? " · Primary" : ""}
              </div>
              <div style={{ fontSize: 13.5, color: "var(--text-primary)" }}>
                {addr.full_address ?? [addr.street, addr.city, addr.state, addr.country].filter(Boolean).join(", ")}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
