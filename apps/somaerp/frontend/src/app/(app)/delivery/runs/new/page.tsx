"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createDeliveryRun, listDeliveryRoutes, listRiders } from "@/lib/api";
import type { DeliveryRoute, Rider } from "@/types/api";

export default function NewRunPage() {
  const router = useRouter();
  const [routes, setRoutes] = useState<DeliveryRoute[]>([]);
  const [riders, setRiders] = useState<Rider[]>([]);
  const [routeId, setRouteId] = useState("");
  const [riderId, setRiderId] = useState("");
  const [runDate, setRunDate] = useState(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    listDeliveryRoutes({ status: "active", limit: 200 })
      .then(setRoutes)
      .catch(() => setRoutes([]));
    listRiders({ status: "active", limit: 200 })
      .then(setRiders)
      .catch(() => setRiders([]));
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      const created = await createDeliveryRun({
        route_id: routeId,
        rider_id: riderId,
        run_date: runDate,
        notes: notes || null,
      });
      router.push(`/delivery/runs/${created.id}`);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Run</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Plan a run for a route + rider on a date. After creation you can
          generate stops from the route&apos;s customer sequence.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Route</span>
          <select
            required
            value={routeId}
            onChange={(e) => setRouteId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">Select route…</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.customer_count} customers)
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Rider</span>
          <select
            required
            value={riderId}
            onChange={(e) => setRiderId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">Select rider…</option>
            {riders.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} — {r.role_name}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">
            Run date
          </span>
          <input
            type="date"
            required
            value={runDate}
            onChange={(e) => setRunDate(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Notes</span>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>

        {err && (
          <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Link
            href="/delivery/runs"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold  hover:bg-slate-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-400"
          >
            {submitting ? "Creating…" : "Create Run"}
          </button>
        </div>
      </form>
    </div>
  );
}
