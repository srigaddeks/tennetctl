"use client";

import { useState } from "react";

import {
  useAddIpAllowlistEntry,
  useIpAllowlist,
  useRemoveIpAllowlistEntry,
} from "@/features/iam/hooks/use-ip-allowlist";

const PLACEHOLDER_ORG_ID = "default";

export default function IpAllowlistPage() {
  const orgId = PLACEHOLDER_ORG_ID;
  const { data: entries = [], isLoading } = useIpAllowlist(orgId);
  const addEntry = useAddIpAllowlistEntry(orgId);
  const removeEntry = useRemoveIpAllowlistEntry(orgId);

  const [cidr, setCidr] = useState("");
  const [label, setLabel] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await addEntry.mutateAsync({ cidr: cidr.trim(), label: label.trim() });
      setCidr("");
      setLabel("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add entry");
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-semibold mb-6">IP Allowlist</h1>
      <p className="text-sm text-gray-500 mb-6">
        When entries are present, only requests from matching IP ranges are
        allowed. An empty list permits all IPs.
      </p>

      <form onSubmit={handleAdd} className="flex gap-3 mb-8">
        <input
          className="border rounded px-3 py-2 text-sm flex-1"
          placeholder="CIDR (e.g. 10.0.0.0/8)"
          value={cidr}
          onChange={(e) => setCidr(e.target.value)}
          required
        />
        <input
          className="border rounded px-3 py-2 text-sm w-40"
          placeholder="Label (optional)"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <button
          type="submit"
          disabled={addEntry.isPending}
          className="bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
        >
          Add
        </button>
      </form>

      {error && (
        <p className="text-red-600 text-sm mb-4">{error}</p>
      )}

      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : entries.length === 0 ? (
        <p className="text-gray-400 text-sm">
          No allowlist entries — all IPs are permitted.
        </p>
      ) : (
        <ul className="divide-y border rounded">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="flex items-center justify-between px-4 py-3"
            >
              <div>
                <span className="font-mono text-sm">{entry.cidr}</span>
                {entry.label && (
                  <span className="ml-3 text-gray-500 text-sm">{entry.label}</span>
                )}
              </div>
              <button
                onClick={() => removeEntry.mutate(entry.id)}
                disabled={removeEntry.isPending}
                className="text-red-600 text-sm hover:underline disabled:opacity-50"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
