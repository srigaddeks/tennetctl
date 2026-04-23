"use client";

import { useState } from "react";

type JobStatus = {
  id: string;
  kind: string;
  status: string;
  requested_at: string;
  completed_at: string | null;
  hard_erase_at: string | null;
} | null;

type GdprStatusData = {
  export: JobStatus;
  erase: JobStatus;
};

async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error?.message ?? "Request failed");
  return data.data;
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-elevated)",
  border: "1px solid var(--border)",
  borderRadius: "6px",
  padding: "9px 12px",
  fontSize: "13px",
  color: "var(--text-primary)",
  outline: "none",
  transition: "border-color 0.15s, box-shadow 0.15s",
  fontFamily: "var(--font-sans)",
};

const sectionStyle: React.CSSProperties = {
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  padding: "20px 24px",
};

export default function PrivacyPage() {
  const [exportBanner, setExportBanner] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [focusedField, setFocusedField] = useState<string | null>(null);

  function fieldStyle(name: string): React.CSSProperties {
    return {
      ...inputStyle,
      borderColor: focusedField === name ? "var(--accent)" : "var(--border)",
      boxShadow: focusedField === name ? "0 0 0 3px var(--accent-muted)" : "none",
    };
  }

  async function handleExport() {
    setExportBanner(null);
    setExportError(null);
    try {
      await apiFetch("/v1/account/data-export", { method: "POST" });
      setExportBanner("Preparing your data export — you will receive an email when it is ready.");
    } catch (err: unknown) {
      setExportError(err instanceof Error ? err.message : "Export request failed");
    }
  }

  async function handleDeleteSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (deleteConfirm !== "DELETE") {
      setDeleteError('You must type "DELETE" to confirm.');
      return;
    }
    setSubmitting(true);
    setDeleteError(null);
    try {
      await apiFetch("/v1/account/delete-me", {
        method: "POST",
        body: JSON.stringify({
          password: deletePassword,
          totp_code: totpCode || undefined,
          confirm: "DELETE",
        }),
      });
      setDeleteSuccess(true);
      setShowDeleteModal(false);
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Deletion request failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (deleteSuccess) {
    return (
      <div
        className="flex flex-1 flex-col items-center justify-center px-8 py-12 animate-fade-in"
        style={{ background: "var(--bg-base)" }}
      >
        <div
          className="w-full max-w-md rounded-lg px-8 py-10 text-center"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--danger)",
          }}
        >
          <div
            className="inline-flex h-12 w-12 items-center justify-center rounded-full text-xl mb-4"
            style={{ background: "var(--danger-muted)", color: "var(--danger)" }}
          >
            ⚠
          </div>
          <h2
            className="text-lg font-semibold mb-2"
            style={{ color: "var(--danger)" }}
          >
            Account deletion requested
          </h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Your account has been pseudonymized and your sessions revoked. You have{" "}
            <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>30 days</span>{" "}
            to recover your account via the link in your confirmation email. After 30 days all
            remaining personal data will be permanently purged.
          </p>
        </div>
      </div>
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
        <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
          Account
        </div>
        <h1
          className="text-xl font-semibold tracking-tight"
          style={{ color: "var(--text-primary)" }}
        >
          Privacy
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Your data rights under GDPR — export or permanently delete your account.
        </p>
      </div>

      <div className="mx-auto w-full max-w-2xl px-8 py-6 space-y-5">

        {/* GDPR info banner */}
        <div
          className="flex items-start gap-3 rounded px-4 py-3 text-xs"
          style={{
            background: "var(--info-muted)",
            border: "1px solid var(--info)",
            color: "var(--text-secondary)",
          }}
        >
          <span style={{ color: "var(--info)", fontSize: "14px", flexShrink: 0 }}>ⓘ</span>
          <span>
            Under GDPR Articles 15 and 17, you have the right to access all personal data we hold
            and to request permanent erasure. Export requests are processed within 72 hours.
          </span>
        </div>

        {/* Export section */}
        <section style={sectionStyle}>
          <div className="label-caps mb-1" style={{ color: "var(--text-muted)" }}>
            GDPR Article 15 — Right of access
          </div>
          <h2 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
            Download my data
          </h2>
          <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
            Request a copy of all personal data we hold about you. You will receive an email with
            a download link when the export is ready (within 72 hours).
          </p>

          {exportBanner && (
            <div
              className="flex items-center gap-2 rounded px-3 py-2 text-xs mb-3"
              style={{
                background: "var(--success-muted)",
                border: "1px solid var(--success)",
                color: "var(--success)",
              }}
            >
              <span>✓</span>
              {exportBanner}
            </div>
          )}
          {exportError && (
            <div
              className="flex items-center gap-2 rounded px-3 py-2 text-xs mb-3"
              style={{
                background: "var(--danger-muted)",
                border: "1px solid var(--danger)",
                color: "var(--danger)",
              }}
            >
              <span>⚠</span>
              {exportError}
            </div>
          )}

          <button
            onClick={handleExport}
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-bright)",
              borderRadius: "6px",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 500,
              color: "var(--text-primary)",
              cursor: "pointer",
              transition: "border-color 0.15s, background 0.15s",
              fontFamily: "var(--font-sans)",
            }}
          >
            Download my data
          </button>
        </section>

        {/* Erasure section */}
        <section
          style={{
            ...sectionStyle,
            borderColor: "rgba(255,63,85,0.25)",
          }}
        >
          <div className="label-caps mb-1" style={{ color: "var(--danger)" }}>
            GDPR Article 17 — Right to erasure
          </div>
          <h2 className="text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
            Delete my account
          </h2>
          <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
            Permanently delete your account and all personal data. A{" "}
            <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>30-day recovery window</span>{" "}
            applies — after that all data is irreversibly purged and cannot be recovered.
          </p>
          <button
            onClick={() => setShowDeleteModal(true)}
            style={{
              background: "var(--danger-muted)",
              border: "1px solid var(--danger)",
              borderRadius: "6px",
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 500,
              color: "var(--danger)",
              cursor: "pointer",
              transition: "background 0.15s",
              fontFamily: "var(--font-sans)",
            }}
          >
            Delete my account
          </button>
        </section>

      </div>

      {/* Delete modal */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
        >
          <div
            className="w-full max-w-md rounded-lg shadow-2xl animate-slide-up"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--danger)",
            }}
          >
            {/* Modal header */}
            <div
              className="flex items-center gap-3 px-6 py-4 border-b"
              style={{ borderColor: "rgba(255,63,85,0.2)" }}
            >
              <div
                className="flex h-8 w-8 items-center justify-center rounded text-sm"
                style={{ background: "var(--danger-muted)", color: "var(--danger)" }}
              >
                ⚠
              </div>
              <h3 className="text-sm font-semibold" style={{ color: "var(--danger)" }}>
                Confirm account deletion
              </h3>
            </div>

            <div className="px-6 py-5">
              <p className="text-xs mb-5" style={{ color: "var(--text-secondary)" }}>
                This will immediately revoke all your sessions and pseudonymize your account. You
                have{" "}
                <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>30 days</span> to
                recover before permanent purge. This action cannot be undone after the recovery
                window.
              </p>

              <form onSubmit={handleDeleteSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label
                    className="label-caps"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Current password
                  </label>
                  <input
                    type="password"
                    required
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    onFocus={() => setFocusedField("deletePassword")}
                    onBlur={() => setFocusedField(null)}
                    style={fieldStyle("deletePassword")}
                    placeholder="Your current password"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label
                    className="label-caps"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    TOTP code{" "}
                    <span style={{ color: "var(--text-muted)", textTransform: "none", letterSpacing: "normal" }}>
                      (if enrolled)
                    </span>
                  </label>
                  <input
                    type="text"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value)}
                    onFocus={() => setFocusedField("totpCode")}
                    onBlur={() => setFocusedField(null)}
                    style={{
                      ...fieldStyle("totpCode"),
                      fontFamily: "var(--font-mono)",
                      letterSpacing: "0.2em",
                    }}
                    placeholder="000000"
                    maxLength={6}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label
                    className="label-caps"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    Type{" "}
                    <code
                      className="font-mono-data normal-case"
                      style={{
                        background: "var(--danger-muted)",
                        border: "1px solid var(--danger)",
                        borderRadius: "3px",
                        padding: "1px 5px",
                        color: "var(--danger)",
                        letterSpacing: "0.15em",
                      }}
                    >
                      DELETE
                    </code>
                    {" "}to confirm
                  </label>
                  <input
                    type="text"
                    required
                    value={deleteConfirm}
                    onChange={(e) => setDeleteConfirm(e.target.value)}
                    onFocus={() => setFocusedField("deleteConfirm")}
                    onBlur={() => setFocusedField(null)}
                    style={{
                      ...fieldStyle("deleteConfirm"),
                      borderColor: deleteConfirm && deleteConfirm !== "DELETE"
                        ? "var(--danger)"
                        : focusedField === "deleteConfirm"
                        ? "var(--accent)"
                        : "var(--border)",
                      fontFamily: "var(--font-mono)",
                      letterSpacing: "0.1em",
                    }}
                    placeholder="DELETE"
                  />
                </div>

                {deleteError && (
                  <p className="text-xs" style={{ color: "var(--danger)" }}>
                    ⚠ {deleteError}
                  </p>
                )}

                <div className="flex gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setShowDeleteModal(false);
                      setDeleteError(null);
                      setDeletePassword("");
                      setTotpCode("");
                      setDeleteConfirm("");
                    }}
                    style={{
                      flex: 1,
                      background: "var(--bg-elevated)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      padding: "9px 16px",
                      fontSize: "13px",
                      color: "var(--text-secondary)",
                      cursor: "pointer",
                      fontFamily: "var(--font-sans)",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || deleteConfirm !== "DELETE"}
                    style={{
                      flex: 1,
                      background: "var(--danger)",
                      border: "none",
                      borderRadius: "6px",
                      padding: "9px 16px",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "white",
                      cursor: (submitting || deleteConfirm !== "DELETE") ? "not-allowed" : "pointer",
                      opacity: (submitting || deleteConfirm !== "DELETE") ? 0.5 : 1,
                      transition: "opacity 0.15s",
                      fontFamily: "var(--font-sans)",
                    }}
                  >
                    {submitting ? "Deleting…" : "Delete my account"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
