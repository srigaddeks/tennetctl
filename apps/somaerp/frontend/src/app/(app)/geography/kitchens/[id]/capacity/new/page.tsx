"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createKitchenCapacity,
  getKitchen,
  listProductLines,
  listUnitsOfMeasure,
} from "@/lib/api";
import type {
  Kitchen,
  ProductLine,
  UnitOfMeasure,
} from "@/types/api";

type KitchenState =
  | { status: "loading" }
  | { status: "ok"; kitchen: Kitchen }
  | { status: "error"; message: string };

type LinesState =
  | { status: "loading" }
  | { status: "ok"; items: ProductLine[] }
  | { status: "error"; message: string };

type UnitsState =
  | { status: "loading" }
  | { status: "ok"; items: UnitOfMeasure[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

export default function NewKitchenCapacityPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const kitchenId = params?.id ?? ""

  const [kitchen, setKitchen] = useState<KitchenState>({ status: "loading" });
  const [lines, setLines] = useState<LinesState>({ status: "loading" });
  const [units, setUnits] = useState<UnitsState>({ status: "loading" });

  const [productLineId, setProductLineId] = useState<string>("");
  const [capacityValue, setCapacityValue] = useState<string>("");
  const [capacityUnitId, setCapacityUnitId] = useState<string>("");
  const [windowStart, setWindowStart] = useState<string>("04:00");
  const [windowEnd, setWindowEnd] = useState<string>("08:00");
  const [validFrom, setValidFrom] = useState<string>(today());
  const [validTo, setValidTo] = useState<string>("");
  const [notes, setNotes] = useState<string>("");

  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    if (!kitchenId) return;
    let cancelled = false;
    getKitchen(kitchenId)
      .then((k) => {
        if (!cancelled) setKitchen({ status: "ok", kitchen: k });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setKitchen({ status: "error", message });
      });
    listProductLines({ status: "active" })
      .then((items) => {
        if (cancelled) return;
        setLines({ status: "ok", items });
        if (items.length > 0) setProductLineId(items[0].id);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setLines({ status: "error", message });
      });
    listUnitsOfMeasure()
      .then((items) => {
        if (cancelled) return;
        setUnits({ status: "ok", items });
        // Prefer a count-dimension unit (bottles / count) as default for drinks.
        const pref =
          items.find((u) => u.code === "bottle") ?? ""
          items.find((u) => u.dimension === "count") ?? ""
          items[0];
        if (pref) setCapacityUnitId(String(pref.id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setUnits({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [kitchenId]);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const capNum = Number.parseFloat(capacityValue);
    if (!Number.isFinite(capNum) || capNum <= 0) {
      setSubmit({
        status: "error",
        message: "Capacity value must be a positive number",
      });
      return;
    }

    const unitNum = Number.parseInt(capacityUnitId, 10);
    if (!Number.isFinite(unitNum)) {
      setSubmit({ status: "error", message: "Pick a capacity unit" });
      return;
    }

    if (!productLineId) {
      setSubmit({ status: "error", message: "Pick a product line" });
      return;
    }

    if (windowStart >= windowEnd) {
      setSubmit({
        status: "error",
        message: "Time window end must be after start",
      });
      return;
    }

    if (validTo && validTo <= validFrom) {
      setSubmit({
        status: "error",
        message: "Valid-to must be greater than valid-from",
      });
      return;
    }

    const properties: Record<string, unknown> = {};
    if (notes.trim() !== "") properties.notes = notes.trim();

    setSubmit({ status: "submitting" });
    try {
      await createKitchenCapacity(kitchenId, {
        product_line_id: productLineId,
        capacity_value: capNum,
        capacity_unit_id: unitNum,
        // Backend expects "HH:MM:SS" or "HH:MM" — send with :00 for clarity.
        time_window_start: `${windowStart}:00`,
        time_window_end: `${windowEnd}:00`,
        valid_from: validFrom,
        valid_to: validTo.trim() === "" ? null : validTo,
        properties,
      });
      router.push(`/geography/kitchens/${kitchenId}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      // Surface the specific overlap error with a friendlier hint.
      const friendly = message.includes("CAPACITY_WINDOW_CONFLICT")
        ? "A capacity row already exists for this product line in that time window. Close the existing one first."
        : message;
      setSubmit({ status: "error", message: friendly });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          Add Capacity
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {lines.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading product lines…</p>
        )}
        {lines.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load product lines: {lines.message}
          </div>
        )}
        {lines.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Product Line
            </label>
            <select
              value={productLineId}
              onChange={(e) => setProductLineId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {lines.items.length === 0 && (
                <option value="" disabled>
                  No active product lines
                </option>
              )}
              {lines.items.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name} ({l.category_name})
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Capacity Value
            </label>
            <input
              type="number"
              step="0.01"
              inputMode="decimal"
              value={capacityValue}
              onChange={(e) => setCapacityValue(e.target.value)}
              disabled={disabled}
              required
              placeholder="50"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Capacity Unit
            </label>
            {units.status === "loading" && (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading units…</p>
            )}
            {units.status === "error" && (
              <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
                Failed to load units: {units.message}
              </div>
            )}
            {units.status === "ok" && (
              <select
                value={capacityUnitId}
                onChange={(e) => setCapacityUnitId(e.target.value)}
                disabled={disabled}
                required
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                {units.items.map((u) => (
                  <option key={u.id} value={String(u.id)}>
                    {u.name} ({u.code}) · {u.dimension}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Time Window Start
            </label>
            <input
              type="time"
              value={windowStart}
              onChange={(e) => setWindowStart(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Time Window End
            </label>
            <input
              type="time"
              value={windowEnd}
              onChange={(e) => setWindowEnd(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Valid From
            </label>
            <input
              type="date"
              value={validFrom}
              onChange={(e) => setValidFrom(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Valid To (optional)
            </label>
            <input
              type="date"
              value={validTo}
              onChange={(e) => setValidTo(e.target.value)}
              disabled={disabled}
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Leave blank for currently-active row.
            </p>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Notes (optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={disabled}
            placeholder="KPHB Home Kitchen Stage 1 capacity"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Stored under properties.notes.
          </p>
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
              lines.status !== "ok" ||
              units.status !== "ok" ||
              productLineId === "" ||
              capacityUnitId === ""
            }
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Capacity"}
          </button>
          <Link
            href={`/geography/kitchens/${kitchenId}`}
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
