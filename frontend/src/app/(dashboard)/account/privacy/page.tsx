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
      <div className="max-w-xl mx-auto py-12 px-4">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <h2 className="text-lg font-semibold text-red-700 mb-2">Account deletion requested</h2>
          <p className="text-sm text-red-600">
            Your account has been pseudonymized and your sessions revoked. You have 30 days to
            recover your account via the link in your confirmation email. After 30 days all
            remaining personal data will be permanently purged.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto py-12 px-4 space-y-8">
      <h1 className="text-2xl font-bold">Privacy</h1>

      {/* Export */}
      <section className="rounded-lg border border-neutral-200 p-6 space-y-3">
        <h2 className="font-semibold text-base">Download my data</h2>
        <p className="text-sm text-neutral-600">
          Request a copy of all personal data we hold about you (GDPR Article 15). You will
          receive an email with a download link when the export is ready.
        </p>
        {exportBanner && (
          <div className="rounded bg-blue-50 border border-blue-200 px-3 py-2 text-sm text-blue-700">
            {exportBanner}
          </div>
        )}
        {exportError && (
          <div className="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {exportError}
          </div>
        )}
        <button
          onClick={handleExport}
          className="rounded bg-neutral-800 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 transition-colors"
        >
          Download my data
        </button>
      </section>

      {/* Erasure */}
      <section className="rounded-lg border border-red-200 p-6 space-y-3">
        <h2 className="font-semibold text-base text-red-700">Delete my account</h2>
        <p className="text-sm text-neutral-600">
          Permanently delete your account and all personal data (GDPR Article 17). A 30-day
          recovery window applies — after that all data is irreversibly purged.
        </p>
        <button
          onClick={() => setShowDeleteModal(true)}
          className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
        >
          Delete my account
        </button>
      </section>

      {/* Delete modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-red-700">Confirm account deletion</h3>
            <p className="text-sm text-neutral-600">
              This will immediately revoke all your sessions and pseudonymize your account. You
              have 30 days to recover before permanent purge. This action cannot be undone after
              the recovery window.
            </p>
            <form onSubmit={handleDeleteSubmit} className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Current password</label>
                <input
                  type="password"
                  required
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="w-full rounded border border-neutral-300 px-3 py-2 text-sm"
                  placeholder="Your current password"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  TOTP code{" "}
                  <span className="text-neutral-400 font-normal">(if enrolled)</span>
                </label>
                <input
                  type="text"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="w-full rounded border border-neutral-300 px-3 py-2 text-sm"
                  placeholder="6-digit code"
                  maxLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Type <span className="font-mono font-bold">DELETE</span> to confirm
                </label>
                <input
                  type="text"
                  required
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  className="w-full rounded border border-neutral-300 px-3 py-2 text-sm"
                  placeholder="DELETE"
                />
              </div>
              {deleteError && (
                <p className="text-sm text-red-600">{deleteError}</p>
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
                  className="flex-1 rounded border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || deleteConfirm !== "DELETE"}
                  className="flex-1 rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? "Deleting…" : "Delete my account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
