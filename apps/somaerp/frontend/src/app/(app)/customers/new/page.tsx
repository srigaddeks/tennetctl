"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createCustomer, listLocations } from "@/lib/api";
import type { CustomerStatus, Location } from "@/types/api";

export default function NewCustomerPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [locationId, setLocationId] = useState("");
  const [addressJson, setAddressJson] = useState("{}");
  const [deliveryNotes, setDeliveryNotes] = useState("");
  const [acquisitionSource, setAcquisitionSource] = useState("");
  const [status, setStatus] = useState<CustomerStatus>("active");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listLocations().then(setLocations).catch(() => undefined);
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
      let addr: Record<string, unknown> = {};
      if (addressJson.trim()) {
        try {
          addr = JSON.parse(addressJson);
        } catch {
          throw new Error("Address JSON is invalid.");
        }
      }
      const created = await createCustomer({
        location_id: locationId || undefined,
        name,
        slug,
        email: email || undefined,
        phone: phone || undefined,
        address_jsonb: addr,
        delivery_notes: deliveryNotes || undefined,
        acquisition_source: acquisitionSource || undefined,
        status,
      });
      router.push(`/customers/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Customer</h1>
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

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Email">
            <input
              type="email"
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field label="Phone">
            <input
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </Field>
        </div>

        <Field label="Location">
          <select
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
          >
            <option value="">(none — add later)</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Address (JSON)">
          <textarea
            rows={4}
            className="w-full rounded border px-3 py-2 font-mono text-xs focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={addressJson}
            onChange={(e) => setAddressJson(e.target.value)}
            placeholder='{"line1":"...","pincode":"500072"}'
          />
        </Field>

        <Field label="Delivery Notes">
          <textarea
            rows={2}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            value={deliveryNotes}
            onChange={(e) => setDeliveryNotes(e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Acquisition Source">
            <input
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={acquisitionSource}
              onChange={(e) => setAcquisitionSource(e.target.value)}
              placeholder="e.g. ig_ad, word_of_mouth"
            />
          </Field>

          <Field label="Status">
            <select
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              value={status}
              onChange={(e) => setStatus(e.target.value as CustomerStatus)}
            >
              <option value="prospect">Prospect</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="churned">Churned</option>
              <option value="blocked">Blocked</option>
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
            {submitting ? "Creating…" : "Create Customer"}
          </button>
          <Link
            href="/customers"
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
