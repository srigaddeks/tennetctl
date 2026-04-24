"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createSupplier,
  listLocations,
  listSupplierSourceTypes,
} from "@/lib/api";
import type {
  Location,
  SupplierSourceType,
  SupplierStatus,
} from "@/types/api";

type SourceTypesState =
  | { status: "loading" }
  | { status: "ok"; items: SupplierSourceType[] }
  | { status: "error"; message: string };

type LocationsState =
  | { status: "loading" }
  | { status: "ok"; items: Location[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<SupplierStatus> = [
  "active",
  "paused",
  "blacklisted",
];

const PAYMENT_TERMS: ReadonlyArray<string> = [
  "cash_on_delivery",
  "net_7",
  "net_30",
  "prepaid",
];

const QUALITY_RATINGS: ReadonlyArray<number> = [1, 2, 3, 4, 5];

export default function NewSupplierPage() {
  const router = useRouter();

  const [sourceTypes, setSourceTypes] = useState<SourceTypesState>({
    status: "loading",
  });
  const [locations, setLocations] = useState<LocationsState>({
    status: "loading",
  });

  const [sourceTypeId, setSourceTypeId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [locationId, setLocationId] = useState<string>("");
  const [contactJson, setContactJson] = useState<string>("");
  const [paymentTerms, setPaymentTerms] = useState<string>("");
  const [defaultCurrencyCode, setDefaultCurrencyCode] = useState<string>("INR");
  const [qualityRating, setQualityRating] = useState<string>("");
  const [status, setStatus] = useState<SupplierStatus>("active");

  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listSupplierSourceTypes()
      .then((items) => {
        if (cancelled) return;
        setSourceTypes({ status: "ok", items });
        if (items.length > 0) setSourceTypeId(String(items[0].id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setSourceTypes({ status: "error", message });
      });
    listLocations()
      .then((items) => {
        if (!cancelled) setLocations({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setLocations({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function onNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const stNum = Number.parseInt(sourceTypeId, 10);
    if (!Number.isFinite(stNum)) {
      setSubmit({ status: "error", message: "Pick a source type" });
      return;
    }

    let contact: Record<string, unknown> | undefined;
    if (contactJson.trim() !== "") {
      try {
        const parsed: unknown = JSON.parse(contactJson);
        if (
          parsed === null ||
          typeof parsed !== "object" ||
          Array.isArray(parsed)
        ) {
          setSubmit({
            status: "error",
            message: "Contact must be a JSON object",
          });
          return;
        }
        contact = parsed as Record<string, unknown>;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Invalid JSON";
        setSubmit({
          status: "error",
          message: `Contact JSON parse failed: ${message}`,
        });
        return;
      }
    }

    const currency = defaultCurrencyCode.trim().toUpperCase();
    if (currency.length !== 3) {
      setSubmit({
        status: "error",
        message: "Currency must be a 3-letter ISO code",
      });
      return;
    }

    const qNum = qualityRating === "" ? undefined : Number.parseInt(qualityRating, 10);
    if (qNum !== undefined && !Number.isFinite(qNum)) {
      setSubmit({ status: "error", message: "Quality rating invalid" });
      return;
    }

    setSubmit({ status: "submitting" });
    try {
      await createSupplier({
        source_type_id: stNum,
        name: name.trim(),
        slug: slug.trim(),
        location_id: locationId === "" ? undefined : locationId,
        contact_jsonb: contact,
        payment_terms: paymentTerms === "" ? undefined : paymentTerms,
        default_currency_code: currency,
        quality_rating: qNum,
        status,
      });
      router.push("/supply/suppliers");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Supplier</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {sourceTypes.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading source types…</p>
        )}
        {sourceTypes.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load source types: {sourceTypes.message}
          </div>
        )}
        {sourceTypes.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Source Type
            </label>
            <select
              value={sourceTypeId}
              onChange={(e) => setSourceTypeId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {sourceTypes.items.length === 0 && (
                <option value="" disabled>
                  No source types seeded
                </option>
              )}
              {sourceTypes.items.map((s) => (
                <option key={s.id} value={String(s.id)}>
                  {s.name} ({s.code})
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
            placeholder="Bowenpally Wholesale Market"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Slug
          </label>
          <input
            type="text"
            value={slug}
            onChange={(e) => {
              setSlugTouched(true);
              setSlug(e.target.value);
            }}
            disabled={disabled}
            required
            placeholder="bowenpally-wholesale-market"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Auto-derived from name. Edit to override.
          </p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Location
          </label>
          <select
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            disabled={disabled}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">— none —</option>
            {locations.status === "ok" &&
              locations.items.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
          </select>
          {locations.status === "error" && (
            <p className="mt-1 text-xs text-red-700">
              Locations failed to load: {locations.message}
            </p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Contact (JSON)
          </label>
          <textarea
            rows={4}
            value={contactJson}
            onChange={(e) => setContactJson(e.target.value)}
            disabled={disabled}
            placeholder={`{"phone":"...","whatsapp":"...","name":"..."}`}
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Optional. Must be a valid JSON object.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Payment Terms
            </label>
            <select
              value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value)}
              disabled={disabled}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              <option value="">— none —</option>
              {PAYMENT_TERMS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Default Currency
            </label>
            <input
              type="text"
              value={defaultCurrencyCode}
              onChange={(e) =>
                setDefaultCurrencyCode(e.target.value.toUpperCase())
              }
              disabled={disabled}
              required
              maxLength={3}
              placeholder="INR"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Quality Rating
            </label>
            <select
              value={qualityRating}
              onChange={(e) => setQualityRating(e.target.value)}
              disabled={disabled}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              <option value="">—</option>
              {QUALITY_RATINGS.map((q) => (
                <option key={q} value={String(q)}>
                  {q} / 5
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as SupplierStatus)}
              disabled={disabled}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={
              disabled || sourceTypes.status !== "ok" || sourceTypeId === ""
            }
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Supplier"}
          </button>
          <Link
            href="/supply/suppliers"
            className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
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
