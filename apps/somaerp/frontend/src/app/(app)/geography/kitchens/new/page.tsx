"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createKitchen, listLocations } from "@/lib/api";
import type { KitchenStatus, KitchenType, Location } from "@/types/api";

type LocationsState =
  | { status: "loading" }
  | { status: "ok"; items: Location[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const KITCHEN_TYPES: ReadonlyArray<{ value: KitchenType; label: string; hint: string }> = [
  { value: "home", label: "Home", hint: "Single-operator home kitchen" },
  { value: "commissary", label: "Commissary", hint: "Shared commercial kitchen" },
  { value: "satellite", label: "Satellite", hint: "Finishing / handoff site" },
];

const STATUSES: ReadonlyArray<KitchenStatus> = ["active", "paused", "decommissioned"];

export default function NewKitchenPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<LocationsState>({ status: "loading" });
  const [locationId, setLocationId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [kitchenType, setKitchenType] = useState<KitchenType>("home");
  const [geoLat, setGeoLat] = useState<string>("");
  const [geoLng, setGeoLng] = useState<string>("");
  const [status, setStatus] = useState<KitchenStatus>("active");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listLocations()
      .then((items) => {
        if (cancelled) return;
        setLocations({ status: "ok", items });
        if (items.length > 0) setLocationId(items[0].id);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setLocations({ status: "error", message });
      });
    return () => { cancelled = true; };
  }, []);

  function onNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (locationId === "") { setSubmit({ status: "error", message: "Pick a location" }); return; }
    const lat = geoLat.trim() === "" ? undefined : Number.parseFloat(geoLat);
    const lng = geoLng.trim() === "" ? undefined : Number.parseFloat(geoLng);
    if (lat !== undefined && !Number.isFinite(lat)) { setSubmit({ status: "error", message: "Latitude must be a number" }); return; }
    if (lng !== undefined && !Number.isFinite(lng)) { setSubmit({ status: "error", message: "Longitude must be a number" }); return; }
    setSubmit({ status: "submitting" });
    try {
      await createKitchen({ location_id: locationId, name: name.trim(), slug: slug.trim(), kitchen_type: kitchenType, geo_lat: lat, geo_lng: lng, status });
      router.push("/geography/kitchens");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";
  const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

  return (
    <div className="max-w-xl">
      <div className="mb-5">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Kitchen</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-4 rounded border p-6"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {locations.status === "loading" && <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading locations…</p>}
        {locations.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load locations: {locations.message}
          </div>
        )}

        {locations.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Location</label>
            <select value={locationId} onChange={(e) => setLocationId(e.target.value)} disabled={disabled} required className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
              {locations.items.length === 0 && <option value="" disabled>No locations — create one first</option>}
              {locations.items.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.region_code})</option>)}
            </select>
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Name</label>
          <input type="text" value={name} onChange={(e) => onNameChange(e.target.value)} disabled={disabled} required placeholder="KPHB Home Kitchen" className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle} />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Slug</label>
          <input type="text" value={slug} onChange={(e) => { setSlugTouched(true); setSlug(e.target.value); }} disabled={disabled} required placeholder="kphb-home" className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={inputStyle} />
        </div>

        <fieldset>
          <legend className="mb-2 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Kitchen Type</legend>
          <div className="space-y-2">
            {KITCHEN_TYPES.map((opt) => (
              <label key={opt.value} className="flex cursor-pointer items-start gap-3 rounded border p-3" style={{ borderColor: "var(--border)" }}>
                <input type="radio" name="kitchen_type" value={opt.value} checked={kitchenType === opt.value} onChange={() => setKitchenType(opt.value)} disabled={disabled} className="mt-1" />
                <span>
                  <span className="block text-sm font-medium" style={{ color: "var(--text-primary)" }}>{opt.label}</span>
                  <span className="block text-xs" style={{ color: "var(--text-muted)" }}>{opt.hint}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Latitude</label>
            <input type="text" inputMode="decimal" value={geoLat} onChange={(e) => setGeoLat(e.target.value)} disabled={disabled} placeholder="17.493100" className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={inputStyle} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Longitude</label>
            <input type="text" inputMode="decimal" value={geoLng} onChange={(e) => setGeoLng(e.target.value)} disabled={disabled} placeholder="78.391400" className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={inputStyle} />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value as KitchenStatus)} disabled={disabled} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>{submit.message}</div>
        )}

        <div className="flex gap-3 pt-1">
          <button type="submit" disabled={disabled || locations.status !== "ok" || locationId === ""} className="inline-flex items-center justify-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
            {disabled ? "Creating…" : "Create Kitchen"}
          </button>
          <Link href="/geography/kitchens" className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function slugify(value: string): string {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
