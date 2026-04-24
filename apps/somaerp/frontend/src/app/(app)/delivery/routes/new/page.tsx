"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createDeliveryRoute, listKitchens } from "@/lib/api";
import type { Kitchen, RouteStatus } from "@/types/api";

export default function NewRoutePage() {
  const router = useRouter();
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [kitchenId, setKitchenId] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [area, setArea] = useState("");
  const [windowStart, setWindowStart] = useState("06:00");
  const [windowEnd, setWindowEnd] = useState("07:30");
  const [status, setStatus] = useState<RouteStatus>("active");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    listKitchens({ status: "active" })
      .then(setKitchens)
      .catch(() => setKitchens([]));
  }, []);

  useEffect(() => {
    if (name && !slug) {
      setSlug(
        name
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-+|-+$/g, ""),
      );
    }
  }, [name, slug]);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      const created = await createDeliveryRoute({
        kitchen_id: kitchenId,
        name,
        slug,
        area: area || null,
        target_window_start: windowStart || null,
        target_window_end: windowEnd || null,
        status,
      });
      router.push(`/delivery/routes/${created.id}`);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Route</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Kitchen</span>
          <select
            required
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">Select kitchen…</option>
            {kitchens.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="Route 1 — KPHB Cluster"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Slug</span>
          <input
            required
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
            pattern="^[a-z0-9][a-z0-9-]*$"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Area</span>
          <input
            value={area}
            onChange={(e) => setArea(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="KPHB Colony"
          />
        </label>

        <div className="grid grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="mb-1 block font-medium ">
              Window start
            </span>
            <input
              type="time"
              value={windowStart}
              onChange={(e) => setWindowStart(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block font-medium ">
              Window end
            </span>
            <input
              type="time"
              value={windowEnd}
              onChange={(e) => setWindowEnd(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as RouteStatus)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="decommissioned">Decommissioned</option>
          </select>
        </label>

        {err && (
          <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Link
            href="/delivery/routes"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold  hover:bg-slate-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-400"
          >
            {submitting ? "Creating…" : "Create Route"}
          </button>
        </div>
      </form>
    </div>
  );
}
