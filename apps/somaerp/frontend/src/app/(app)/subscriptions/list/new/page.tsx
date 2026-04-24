"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import {
  createSubscription,
  listCustomers,
  listServiceZones,
  listSubscriptionPlans,
} from "@/lib/api";
import type {
  Customer,
  ServiceZone,
  SubscriptionPlan,
} from "@/types/api";

export default function NewSubscriptionPage() {
  return (
    <Suspense fallback={<div className="p-10 text-sm" style={{ color: "var(--text-muted)" }}>Loading…</div>}>
      <NewSubscriptionForm />
    </Suspense>
  );
}

function NewSubscriptionForm() {
  const router = useRouter();
  const search = useSearchParams();
  const presetCustomerId = search.get("customer_id") ?? "";

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [zones, setZones] = useState<ServiceZone[]>([]);

  const [customerId, setCustomerId] = useState(presetCustomerId);
  const [planId, setPlanId] = useState("");
  const [serviceZoneId, setServiceZoneId] = useState("");
  const [startDate, setStartDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [billingCycle, setBillingCycle] = useState("weekly");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCustomers().then(setCustomers).catch(() => undefined);
    listSubscriptionPlans({ status: "active" })
      .then(setPlans)
      .catch(() => undefined);
    listServiceZones().then(setZones).catch(() => undefined);
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (!customerId) throw new Error("Choose a customer.");
      if (!planId) throw new Error("Choose a plan.");
      const created = await createSubscription({
        customer_id: customerId,
        plan_id: planId,
        service_zone_id: serviceZoneId || undefined,
        start_date: startDate,
        billing_cycle: billingCycle || undefined,
      });
      router.push(`/subscriptions/list/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          New Subscription
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <Field label="Customer" required>
          <select
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            required
          >
            <option value="">Choose…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Plan" required>
          <select
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={planId}
            onChange={(e) => setPlanId(e.target.value)}
            required
          >
            <option value="">Choose…</option>
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.frequency_name})
              </option>
            ))}
          </select>
        </Field>
        <Field label="Service Zone (optional)">
          <select
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={serviceZoneId}
            onChange={(e) => setServiceZoneId(e.target.value)}
          >
            <option value="">(none)</option>
            {zones.map((z) => (
              <option key={z.id} value={z.id}>
                {z.name} ({z.kitchen_name})
              </option>
            ))}
          </select>
        </Field>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Start Date" required>
            <input
              type="date"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </Field>
          <Field label="Billing Cycle">
            <select
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={billingCycle}
              onChange={(e) => setBillingCycle(e.target.value)}
            >
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="prepaid">Prepaid</option>
            </select>
          </Field>
        </div>

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
            {submitting ? "Creating…" : "Create Subscription"}
          </button>
          <Link
            href="/subscriptions/list"
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
