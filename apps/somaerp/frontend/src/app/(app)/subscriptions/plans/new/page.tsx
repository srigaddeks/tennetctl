"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createSubscriptionPlan,
  listSubscriptionFrequencies,
} from "@/lib/api";
import type {
  SubscriptionFrequency,
  SubscriptionPlanStatus,
} from "@/types/api";

export default function NewPlanPage() {
  const router = useRouter();
  const [frequencies, setFrequencies] = useState<SubscriptionFrequency[]>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [description, setDescription] = useState("");
  const [frequencyId, setFrequencyId] = useState<string>("");
  const [pricePerDelivery, setPricePerDelivery] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState("INR");
  const [status, setStatus] = useState<SubscriptionPlanStatus>("active");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSubscriptionFrequencies().then(setFrequencies).catch(() => undefined);
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
    setError(null);
    try {
      if (!frequencyId) throw new Error("Please choose a frequency.");
      const created = await createSubscriptionPlan({
        name,
        slug,
        description: description || undefined,
        frequency_id: Number.parseInt(frequencyId, 10),
        price_per_delivery: pricePerDelivery
          ? Number.parseFloat(pricePerDelivery)
          : undefined,
        currency_code: currencyCode,
        status,
      });
      router.push(`/subscriptions/plans/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Plan</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <Field label="Name" required>
          <input
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </Field>
        <Field label="Slug" required>
          <input
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            pattern="^[a-z0-9][a-z0-9-]*$"
            required
          />
        </Field>
        <Field label="Description">
          <textarea
            rows={3}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Field label="Frequency" required>
            <select
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={frequencyId}
              onChange={(e) => setFrequencyId(e.target.value)}
              required
            >
              <option value="">Choose…</option>
              {frequencies.map((f) => (
                <option key={f.id} value={String(f.id)}>
                  {f.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Price / delivery">
            <input
              type="number"
              step="0.01"
              min="0"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={pricePerDelivery}
              onChange={(e) => setPricePerDelivery(e.target.value)}
              placeholder="leave blank for custom"
            />
          </Field>
          <Field label="Currency" required>
            <input
              className="w-full rounded border px-3 py-2 font-mono text-sm uppercase focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={currencyCode}
              onChange={(e) => setCurrencyCode(e.target.value.toUpperCase())}
              minLength={3}
              maxLength={3}
              required
            />
          </Field>
        </div>

        <Field label="Status">
          <select
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={status}
            onChange={(e) =>
              setStatus(e.target.value as SubscriptionPlanStatus)
            }
          >
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </Field>

        {error && (
          <p className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create Plan"}
          </button>
          <Link
            href="/subscriptions/plans"
            className="rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
      </span>
      {children}
    </label>
  );
}
