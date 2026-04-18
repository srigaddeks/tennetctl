"use client";

import { useState } from "react";

import type { SiemDestination } from "@/types/api";

const BASE = "/api/v1/iam/siem-destinations";
const KINDS = ["webhook", "splunk_hec", "datadog", "s3"] as const;

function useSiemDestinations(orgId: string) {
  const [destinations, setDestinations] = useState<SiemDestination[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(BASE, { headers: { "x-org-id": orgId } });
      const data = await res.json();
      if (data.ok) setDestinations(data.data);
    } finally {
      setLoading(false);
    }
  }

  return { destinations, loading, load };
}

const PLACEHOLDER_ORG = "default";

export default function SiemPage() {
  const orgId = PLACEHOLDER_ORG;
  const [kind, setKind] = useState<(typeof KINDS)[number]>("webhook");
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [destinations, setDestinations] = useState<SiemDestination[]>([]);
  const [loaded, setLoaded] = useState(false);

  async function fetchAll() {
    const res = await fetch(BASE, { headers: { "x-org-id": orgId } });
    const data = await res.json();
    if (data.ok) {
      setDestinations(data.data);
      setLoaded(true);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const body = { kind, label, config_jsonb: kind === "webhook" ? { url } : {} };
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-org-id": orgId },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!data.ok) { setError(data.error?.message); return; }
    setLabel(""); setUrl("");
    await fetchAll();
  }

  async function handleDelete(id: string) {
    await fetch(`${BASE}/${id}`, { method: "DELETE", headers: { "x-org-id": orgId } });
    await fetchAll();
  }

  if (!loaded) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4">
        <h1 className="text-2xl font-semibold mb-4">SIEM Export</h1>
        <button onClick={fetchAll} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">
          Load destinations
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-semibold mb-6">SIEM Export Destinations</h1>

      <form onSubmit={handleAdd} className="space-y-3 mb-8 border rounded p-4">
        <div className="flex gap-3">
          <select className="border rounded px-3 py-2 text-sm" value={kind}
            onChange={(e) => setKind(e.target.value as typeof kind)}>
            {KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
          </select>
          <input className="border rounded px-3 py-2 text-sm flex-1" placeholder="Label"
            value={label} onChange={(e) => setLabel(e.target.value)} />
        </div>
        {kind === "webhook" && (
          <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Webhook URL"
            value={url} onChange={(e) => setUrl(e.target.value)} required={kind === "webhook"} />
        )}
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded text-sm">
          Add destination
        </button>
      </form>

      {destinations.length === 0 ? (
        <p className="text-gray-400 text-sm">No destinations configured.</p>
      ) : (
        <ul className="divide-y border rounded">
          {destinations.map((d) => (
            <li key={d.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <span className="font-mono text-sm bg-gray-100 px-1 rounded">{d.kind}</span>
                {d.label && <span className="ml-2 text-sm">{d.label}</span>}
                <span className="ml-3 text-xs text-gray-400">
                  {d.failure_count > 0 ? `${d.failure_count} failures` : "healthy"}
                </span>
              </div>
              <button onClick={() => handleDelete(d.id)}
                className="text-red-600 text-sm hover:underline">Remove</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
