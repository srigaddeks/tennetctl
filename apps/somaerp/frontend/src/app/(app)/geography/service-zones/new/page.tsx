"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createServiceZone, listKitchens } from "@/lib/api";
import type { Kitchen } from "@/types/api";

type KitchensState = { status: "loading" } | { status: "ok"; items: Kitchen[] } | { status: "error"; message: string };
type SubmitState = { status: "idle" } | { status: "submitting" } | { status: "error"; message: string };

const DEFAULT_POLYGON = `{\n  "pincodes": ["500072"]\n}`;

export default function NewServiceZonePage() {
  const router = useRouter();
  const [kitchens, setKitchens] = useState<KitchensState>({ status: "loading" });
  const [kitchenId, setKitchenId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [polygonText, setPolygonText] = useState<string>(DEFAULT_POLYGON);
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (cancelled) return;
        setKitchens({ status: "ok", items });
        const firstActive = items.find((k) => k.status === "active");
        if (firstActive) setKitchenId(firstActive.id);
        else if (items.length > 0) setKitchenId(items[0].id);
      })
      .catch((err: unknown) => { if (!cancelled) setKitchens({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (kitchenId === "") { setSubmit({ status: "error", message: "Pick a kitchen" }); return; }
    let polygon: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(polygonText);
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Polygon must be a JSON object");
      polygon = parsed as Record<string, unknown>;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Polygon is not valid JSON";
      setSubmit({ status: "error", message: `Invalid polygon JSON: ${message}` });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      await createServiceZone({ kitchen_id: kitchenId, name: name.trim(), polygon_jsonb: polygon });
      router.push("/geography/service-zones");
    } catch (err: unknown) {
      setSubmit({ status: "error", message: err instanceof Error ? err.message : "Unknown error" });
    }
  }

  const disabled = submit.status === "submitting";
  const selectedKitchen = kitchens.status === "ok" ? kitchens.items.find((k) => k.id === kitchenId) : undefined;
  const showNonActiveWarning = selectedKitchen !== undefined && selectedKitchen.status !== "active";
  const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

  return (
    <div className="max-w-xl">
      <div className="mb-5">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Service Zone</h1>
      </div>

      <form onSubmit={onSubmit} className="space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {kitchens.status === "loading" && <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading kitchens…</p>}
        {kitchens.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load kitchens: {kitchens.message}
          </div>
        )}

        {kitchens.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Kitchen</label>
            <select value={kitchenId} onChange={(e) => setKitchenId(e.target.value)} disabled={disabled} required className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
              {kitchens.items.length === 0 && <option value="" disabled>No kitchens — create one first</option>}
              {kitchens.items.map((k) => <option key={k.id} value={k.id}>{k.name} ({k.status})</option>)}
            </select>
            {showNonActiveWarning && (
              <p className="mt-1 text-xs" style={{ color: "var(--status-paused)" }}>
                Warning: only active kitchens accept new service zones. The API will reject a zone on a {selectedKitchen?.status} kitchen.
              </p>
            )}
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} disabled={disabled} required placeholder="KPHB Cluster 1" className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle} />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Polygon (JSON)</label>
          <textarea value={polygonText} onChange={(e) => setPolygonText(e.target.value)} disabled={disabled} required rows={10} spellCheck={false} className="w-full rounded border px-3 py-2 font-mono text-xs focus:outline-none" style={inputStyle} />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Accepts GeoJSON polygon or pincode set. Map picker is a future enhancement.
          </p>
        </div>

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>{submit.message}</div>
        )}

        <div className="flex gap-3 pt-1">
          <button type="submit" disabled={disabled || kitchens.status !== "ok" || kitchenId === ""} className="inline-flex items-center justify-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
            {disabled ? "Creating…" : "Create Service Zone"}
          </button>
          <Link href="/geography/service-zones" className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
