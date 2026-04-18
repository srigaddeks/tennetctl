"use client";

import { useState } from "react";

import type { TosVersion } from "@/types/api";

const BASE = "/api/v1/tos";

export default function TosPage() {
  const [versions, setVersions] = useState<TosVersion[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [form, setForm] = useState({ version: "", title: "", body_markdown: "" });
  const [effectiveAt, setEffectiveAt] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function fetchAll() {
    const res = await fetch(BASE);
    const data = await res.json();
    if (data.ok) { setVersions(data.data); setLoaded(true); }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (!data.ok) { setError(data.error?.message); return; }
    setForm({ version: "", title: "", body_markdown: "" });
    await fetchAll();
  }

  async function handleMarkEffective(id: string) {
    if (!effectiveAt) return;
    await fetch(`${BASE}/${id}/effective`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ effective_at: new Date(effectiveAt).toISOString() }),
    });
    await fetchAll();
  }

  if (!loaded) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4">
        <h1 className="text-2xl font-semibold mb-4">Terms of Service</h1>
        <button onClick={fetchAll} className="bg-blue-600 text-white px-4 py-2 rounded text-sm">
          Load versions
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-semibold mb-6">Terms of Service Versions</h1>

      <form onSubmit={handleCreate} className="space-y-3 mb-8 border rounded p-4">
        <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Version (e.g. 2026-04)"
          value={form.version} onChange={(e) => setForm({ ...form, version: e.target.value })} required />
        <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Title"
          value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <textarea className="w-full border rounded px-3 py-2 text-sm h-24"
          placeholder="Body (Markdown)"
          value={form.body_markdown} onChange={(e) => setForm({ ...form, body_markdown: e.target.value })} />
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded text-sm">
          Publish version
        </button>
      </form>

      <ul className="divide-y border rounded">
        {versions.map((v) => (
          <li key={v.id} className="px-4 py-3">
            <div className="flex items-start justify-between">
              <div>
                <span className="font-medium text-sm">{v.version}</span>
                <span className="ml-2 text-gray-500 text-sm">{v.title}</span>
                {v.effective_at && (
                  <span className="ml-2 text-xs text-green-600">
                    effective {new Date(v.effective_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              {!v.effective_at && (
                <div className="flex gap-2 items-center">
                  <input type="datetime-local" className="border rounded px-2 py-1 text-xs"
                    value={effectiveAt} onChange={(e) => setEffectiveAt(e.target.value)} />
                  <button onClick={() => handleMarkEffective(v.id)}
                    className="text-blue-600 text-xs hover:underline">
                    Make effective
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
