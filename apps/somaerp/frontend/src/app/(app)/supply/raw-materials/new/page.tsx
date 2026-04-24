"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createRawMaterial,
  listRawMaterialCategories,
  listUnitsOfMeasure,
} from "@/lib/api";
import type {
  RawMaterialCategory,
  RawMaterialStatus,
  UnitOfMeasure,
} from "@/types/api";

type CategoriesState =
  | { status: "loading" }
  | { status: "ok"; items: RawMaterialCategory[] }
  | { status: "error"; message: string };

type UnitsState =
  | { status: "loading" }
  | { status: "ok"; items: UnitOfMeasure[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<RawMaterialStatus> = [
  "active",
  "paused",
  "discontinued",
];

export default function NewRawMaterialPage() {
  const router = useRouter();

  const [categories, setCategories] = useState<CategoriesState>({
    status: "loading",
  });
  const [units, setUnits] = useState<UnitsState>({ status: "loading" });

  const [categoryId, setCategoryId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [defaultUnitId, setDefaultUnitId] = useState<string>("");
  const [shelfLifeHours, setShelfLifeHours] = useState<string>("");
  const [requiresLotTracking, setRequiresLotTracking] =
    useState<boolean>(true);
  const [targetUnitCost, setTargetUnitCost] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState<string>("INR");
  const [status, setStatus] = useState<RawMaterialStatus>("active");

  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listRawMaterialCategories()
      .then((items) => {
        if (cancelled) return;
        setCategories({ status: "ok", items });
        if (items.length > 0) setCategoryId(String(items[0].id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setCategories({ status: "error", message });
      });
    listUnitsOfMeasure()
      .then((items) => {
        if (cancelled) return;
        setUnits({ status: "ok", items });
        if (items.length > 0) setDefaultUnitId(String(items[0].id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setUnits({ status: "error", message });
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

    const unitNum = Number.parseInt(defaultUnitId, 10);
    if (!Number.isFinite(unitNum)) {
      setSubmit({ status: "error", message: "Pick a default unit" });
      return;
    }

    const shelfNum =
      shelfLifeHours.trim() === "" ? undefined
        : Number.parseInt(shelfLifeHours, 10);
    if (shelfNum !== undefined && !Number.isFinite(shelfNum)) {
      setSubmit({ status: "error", message: "Shelf life must be an integer" });
      return;
    }

    const costNum =
      targetUnitCost.trim() === "" ? undefined
        : Number.parseFloat(targetUnitCost);
    if (costNum !== undefined && !Number.isFinite(costNum)) {
      setSubmit({
        status: "error",
        message: "Target unit cost must be a number",
      });
      return;
    }

    const currency = currencyCode.trim().toUpperCase();
    if (currency.length !== 3) {
      setSubmit({
        status: "error",
        message: "Currency must be a 3-letter ISO code",
      });
      return;
    }

    setSubmit({ status: "submitting" });
    try {
      await createRawMaterial({
        category_id: catNum,
        name: name.trim(),
        slug: slug.trim(),
        default_unit_id: unitNum,
        default_shelf_life_hours: shelfNum,
        requires_lot_tracking: requiresLotTracking,
        target_unit_cost: costNum,
        currency_code: currency,
        status,
      });
      router.push("/supply/raw-materials");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          New Raw Material
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {categories.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading categories…</p>
        )}
        {categories.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load categories: {categories.message}
          </div>
        )}
        {categories.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Category
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {categories.items.length === 0 && (
                <option value="" disabled>
                  No categories seeded
                </option>
              )}
              {categories.items.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.name} ({c.code})
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
            placeholder="Spinach"
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
            placeholder="spinach"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Auto-derived from name. Edit to override.
          </p>
        </div>

        {units.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading units…</p>
        )}
        {units.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load units: {units.message}
          </div>
        )}
        {units.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Default Unit
            </label>
            <select
              value={defaultUnitId}
              onChange={(e) => setDefaultUnitId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {units.items.length === 0 && (
                <option value="" disabled>
                  No units seeded
                </option>
              )}
              {units.items.map((u) => (
                <option key={u.id} value={String(u.id)}>
                  {u.name} ({u.code}) · {u.dimension}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Default Shelf Life (hours)
          </label>
          <input
            type="number"
            inputMode="numeric"
            value={shelfLifeHours}
            onChange={(e) => setShelfLifeHours(e.target.value)}
            disabled={disabled}
            placeholder="48"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="inline-flex cursor-pointer items-center gap-2 text-sm ">
            <input
              type="checkbox"
              checked={requiresLotTracking}
              onChange={(e) => setRequiresLotTracking(e.target.checked)}
              disabled={disabled}
              className="h-4 w-4 rounded border-slate-300"
            />
            Requires lot tracking
          </label>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Target Unit Cost
            </label>
            <input
              type="number"
              step="0.01"
              inputMode="decimal"
              value={targetUnitCost}
              onChange={(e) => setTargetUnitCost(e.target.value)}
              disabled={disabled}
              placeholder="25.00"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Currency
            </label>
            <input
              type="text"
              value={currencyCode}
              onChange={(e) => setCurrencyCode(e.target.value.toUpperCase())}
              disabled={disabled}
              required
              maxLength={3}
              placeholder="INR"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as RawMaterialStatus)}
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

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={
              disabled ||
              categories.status !== "ok" ||
              units.status !== "ok" ||
              categoryId === "" ||
              defaultUnitId === ""
            }
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Raw Material"}
          </button>
          <Link
            href="/supply/raw-materials"
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
