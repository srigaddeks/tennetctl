"use client";

import { useState } from "react";

type Props = {
  orgId: string;
  userId: string;
  roles: { id: string; label: string | null; code: string | null }[];
  onAssign: (roleId: string, expiresAt: string | null) => Promise<void>;
  onClose: () => void;
};

export function RoleAssignDialog({ orgId: _orgId, userId: _userId, roles, onAssign, onClose }: Props) {
  const [roleId, setRoleId] = useState(roles[0]?.id ?? "");
  const [expiresAt, setExpiresAt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await onAssign(roleId, expiresAt ? new Date(expiresAt).toISOString() : null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign role");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold mb-4">Assign Role</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              required
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label ?? r.code ?? r.id}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Expires at <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="datetime-local"
              className="w-full border rounded px-3 py-2 text-sm"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
            <p className="text-xs text-gray-400 mt-1">Leave blank for a permanent assignment.</p>
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded">
              Cancel
            </button>
            <button
              type="submit"
              disabled={pending}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
            >
              Assign
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
