"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createEquipment, listEquipmentCategories } from "@/lib/api";
import type { EquipmentCategory, EquipmentStatus } from "@/types/api";

type CatState =
  | { status: "loading" }
  | { status: "ok"; items: EquipmentCategory[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<EquipmentStatus> = ["active", "maintenance", "retired"];

export default function NewEquipmentPage() {
  const router = useRouter();
  const [cats, setCats] = useState<CatState>({ status: "loading" });
  const [categoryId, setCategoryId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [status, setStatus] = useState<EquipmentStatus>("active");
  const [purchaseCost, setPurchaseCost] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState<string>("INR");
  const [purchaseDate, setPurchaseDate] = useState<string>("");
  const [lifespan, setLifespan] = useState<string>("");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listEquipmentCategories()
      .then((items) => {
        if (cancelled) return;
        setCats({ status: "ok", items });
        if (items.length > 0) setCategoryId(String(items[0].id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setCats({ status: "error", message });
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
    const catNum = Number.parseInt(categoryId, 10);
    if (!Number.isFinite(catNum)) {
      setSubmit({ status: "error", message: "Pick a category" });
      return;
    }
    const costNum = purchaseCost.trim() === "" ? undefined : Number.parseFloat(purchaseCost);
    if (costNum !== undefined && !Number.isFinite(costNum)) {
      setSubmit({ status: "error", message: "Purchase cost must be a number" });
      return;
    }
    const lifeNum = lifespan.trim() === "" ? undefined : Number.parseInt(lifespan, 10);
    if (lifeNum !== undefined && !Number.isFinite(lifeNum)) {
      setSubmit({ status: "error", message: "Lifespan must be an integer" });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      await createEquipment({
        category_id: catNum,
        name: name.trim(),
        slug: slug.trim(),
        status,
        purchase_cost: costNum,
        currency_code: currencyCode.trim() === "" ? undefined : currencyCode.toUpperCase(),
        purchase_date: purchaseDate === "" ? null : purchaseDate,
        expected_lifespan_months: lifeNum,
      });
      router.push("/equipment");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Equipment</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {cats.status === "loading" && <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading categories…</p>}
        {cats.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load categories: {cats.message}
          </div>
        )}
        {cats.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Category</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {cats.items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            disabled={disabled}
            required
            placeholder="Cold-Press Juicer"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Slug</label>
          <input
            type="text"
            value={slug}
            onChange={(e) => {
              setSlugTouched(true);
              setSlug(e.target.value);
            }}
            disabled={disabled}
            required
            placeholder="cold-press-juicer"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as EquipmentStatus)}
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

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Purchase Cost</label>
            <input
              type="number"
              step="0.01"
              value={purchaseCost}
              onChange={(e) => setPurchaseCost(e.target.value)}
              disabled={disabled}
              placeholder="25000"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Currency</label>
            <input
              type="text"
              value={currencyCode}
              onChange={(e) => setCurrencyCode(e.target.value.toUpperCase())}
              disabled={disabled}
              maxLength={3}
              placeholder="INR"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Purchase Date</label>
            <input
              type="date"
              value={purchaseDate}
              onChange={(e) => setPurchaseDate(e.target.value)}
              disabled={disabled}
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Expected Lifespan (months)
          </label>
          <input
            type="number"
            min={0}
            value={lifespan}
            onChange={(e) => setLifespan(e.target.value)}
            disabled={disabled}
            placeholder="60"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
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
            disabled={disabled || cats.status !== "ok"}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Equipment"}
          </button>
          <Link
            href="/equipment"
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
