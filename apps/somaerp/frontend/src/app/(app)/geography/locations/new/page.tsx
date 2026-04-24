"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createLocation, listRegions } from "@/lib/api";
import type { Region } from "@/types/api";

type RegionsState =
  | { status: "loading" }
  | { status: "ok"; items: Region[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

export default function NewLocationPage() {
  const router = useRouter();
  const [regions, setRegions] = useState<RegionsState>({ status: "loading" });
  const [regionId, setRegionId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [timezone, setTimezone] = useState<string>("");
  const [tzTouched, setTzTouched] = useState<boolean>(false);
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listRegions()
      .then((items) => {
        if (cancelled) return;
        setRegions({ status: "ok", items });
        if (items.length > 0) {
          setRegionId(String(items[0].id));
          if (!tzTouched) setTimezone(items[0].default_timezone);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setRegions({ status: "error", message });
      });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (regions.status !== "ok" || regionId === "") return;
    const r = regions.items.find((x) => String(x.id) === regionId);
    if (r && !tzTouched) setTimezone(r.default_timezone);
  }, [regionId, regions, tzTouched]);

  function onNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const regionNum = Number.parseInt(regionId, 10);
    if (!Number.isFinite(regionNum)) {
      setSubmit({ status: "error", message: "Pick a region" });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      await createLocation({
        region_id: regionNum,
        name: name.trim(),
        slug: slug.trim(),
        timezone: timezone.trim(),
      });
      router.push("/geography/locations");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-xl">
      <div className="mb-5">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          New Location
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-4 rounded border p-6"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {regions.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading regions…</p>
        )}
        {regions.status === "error" && (
          <div
            className="rounded border p-3 text-sm"
            style={{
              borderColor: "var(--status-error)",
              backgroundColor: "var(--status-error-bg)",
              color: "var(--status-error)",
            }}
          >
            Failed to load regions: {regions.message}
          </div>
        )}

        {regions.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Region
            </label>
            <select
              value={regionId}
              onChange={(e) => setRegionId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm transition-colors focus:outline-none"
              style={{
                borderColor: "var(--border)",
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
              }}
            >
              {regions.items.length === 0 && (
                <option value="" disabled>No regions seeded</option>
              )}
              {regions.items.map((r) => (
                <option key={r.id} value={String(r.id)}>
                  {r.code} — {r.state_name} ({r.country_code})
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            disabled={disabled}
            required
            placeholder="Hyderabad HQ"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
            }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Slug
          </label>
          <input
            type="text"
            value={slug}
            onChange={(e) => { setSlugTouched(true); setSlug(e.target.value); }}
            disabled={disabled}
            required
            placeholder="hyderabad-hq"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
            }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Auto-derived from name. Edit to override.
          </p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Timezone
          </label>
          <input
            type="text"
            value={timezone}
            onChange={(e) => { setTzTouched(true); setTimezone(e.target.value); }}
            disabled={disabled}
            required
            placeholder="Asia/Kolkata"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--bg-card)",
              color: "var(--text-primary)",
            }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Defaults from the selected region.
          </p>
        </div>

        {submit.status === "error" && (
          <div
            className="rounded border p-3 text-sm"
            style={{
              borderColor: "var(--status-error)",
              backgroundColor: "var(--status-error-bg)",
              color: "var(--status-error)",
            }}
          >
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="submit"
            disabled={disabled || regions.status !== "ok"}
            className="inline-flex items-center justify-center rounded px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
            style={{
              backgroundColor: "var(--accent)",
              color: "var(--accent-text)",
            }}
          >
            {disabled ? "Creating…" : "Create Location"}
          </button>
          <Link
            href="/geography/locations"
            className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium transition-colors"
            style={{
              borderColor: "var(--border)",
              backgroundColor: "var(--bg-card)",
              color: "var(--text-secondary)",
            }}
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
