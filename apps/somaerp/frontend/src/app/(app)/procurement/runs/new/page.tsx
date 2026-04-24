"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createProcurementRun,
  listKitchens,
  listSuppliers,
} from "@/lib/api";
import type { Kitchen, Supplier } from "@/types/api";

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

export default function NewProcurementRunPage() {
  const router = useRouter();
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [kitchenId, setKitchenId] = useState<string>("");
  const [supplierId, setSupplierId] = useState<string>("");
  const [runDate, setRunDate] = useState<string>(today());
  const [currency, setCurrency] = useState<string>("INR");
  const [notes, setNotes] = useState<string>("");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (cancelled) return;
        setKitchens(items);
        if (items.length > 0) setKitchenId(items[0].id);
      })
      .catch(() => undefined);
    listSuppliers()
      .then((items) => {
        if (cancelled) return;
        setSuppliers(items);
        if (items.length > 0) {
          setSupplierId(items[0].id);
          setCurrency(items[0].default_currency_code);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!kitchenId || !supplierId) {
      setSubmit({ status: "error", message: "Pick a kitchen and supplier" });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      const created = await createProcurementRun({
        kitchen_id: kitchenId,
        supplier_id: supplierId,
        run_date: runDate,
        currency_code: currency.trim().toUpperCase(),
        notes: notes.trim() === "" ? null : notes.trim(),
      });
      router.push(`/procurement/runs/${created.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          New Procurement Run
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Kitchen
          </label>
          <select
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
            disabled={disabled}
            required
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            {kitchens.length === 0 && (
              <option value="" disabled>
                No kitchens — create one first
              </option>
            )}
            {kitchens.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Supplier
          </label>
          <select
            value={supplierId}
            onChange={(e) => {
              setSupplierId(e.target.value);
              const s = suppliers.find((x) => x.id === e.target.value);
              if (s) setCurrency(s.default_currency_code);
            }}
            disabled={disabled}
            required
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            {suppliers.length === 0 && (
              <option value="" disabled>
                No suppliers — create one first
              </option>
            )}
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Run Date
            </label>
            <input
              type="date"
              value={runDate}
              onChange={(e) => setRunDate(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Currency
            </label>
            <input
              type="text"
              maxLength={3}
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 font-mono text-sm uppercase shadow-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Notes
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled}
            placeholder="Morning Bowenpally trip"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={disabled || !kitchenId || !supplierId}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Run"}
          </button>
          <Link
            href="/procurement/runs"
            className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}
