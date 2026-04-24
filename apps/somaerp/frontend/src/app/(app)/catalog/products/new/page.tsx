"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createProduct, listProductLines, listTags } from "@/lib/api";
import type {
  ProductLine,
  ProductStatus,
  ProductTag,
} from "@/types/api";

type LinesState =
  | { status: "loading" }
  | { status: "ok"; items: ProductLine[] }
  | { status: "error"; message: string };

type TagsState =
  | { status: "loading" }
  | { status: "ok"; items: ProductTag[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<ProductStatus> = [
  "active",
  "paused",
  "discontinued",
];

export default function NewProductPage() {
  const router = useRouter();

  const [lines, setLines] = useState<LinesState>({ status: "loading" });
  const [tags, setTags] = useState<TagsState>({ status: "loading" });

  const [productLineId, setProductLineId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [description, setDescription] = useState<string>("");
  const [targetBenefit, setTargetBenefit] = useState<string>("");
  const [servingSizeMl, setServingSizeMl] = useState<string>("");
  const [shelfLifeHours, setShelfLifeHours] = useState<string>("");
  const [targetCogs, setTargetCogs] = useState<string>("");
  const [defaultPrice, setDefaultPrice] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState<string>("INR");
  const [status, setStatus] = useState<ProductStatus>("active");
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());

  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listProductLines()
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
    listTags()
      .then((items) => {
        if (!cancelled) setTags({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setTags({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function onNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  function toggleTag(code: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (productLineId === "") {
      setSubmit({ status: "error", message: "Pick a product line" });
      return;
    }

    const priceNum = Number.parseFloat(defaultPrice);
    if (!Number.isFinite(priceNum)) {
      setSubmit({ status: "error", message: "Default price must be a number" });
      return;
    }

    const servingNum =
      servingSizeMl.trim() === "" ? undefined : Number.parseFloat(servingSizeMl);
    if (servingNum !== undefined && !Number.isFinite(servingNum)) {
      setSubmit({ status: "error", message: "Serving size must be a number" });
      return;
    }

    const shelfNum =
      shelfLifeHours.trim() === "" ? undefined : Number.parseInt(shelfLifeHours, 10);
    if (shelfNum !== undefined && !Number.isFinite(shelfNum)) {
      setSubmit({ status: "error", message: "Shelf life must be an integer" });
      return;
    }

    const cogsNum =
      targetCogs.trim() === "" ? undefined : Number.parseFloat(targetCogs);
    if (cogsNum !== undefined && !Number.isFinite(cogsNum)) {
      setSubmit({ status: "error", message: "Target COGS must be a number" });
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
      await createProduct({
        product_line_id: productLineId,
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim() === "" ? undefined : description.trim(),
        target_benefit:
          targetBenefit.trim() === "" ? undefined : targetBenefit.trim(),
        default_serving_size_ml: servingNum,
        default_shelf_life_hours: shelfNum,
        target_cogs_amount: cogsNum,
        default_selling_price: priceNum,
        currency_code: currency,
        status,
        tag_codes: Array.from(selectedTags),
      });
      router.push("/catalog/products");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Product</h1>
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
                  No product lines — create one first
                </option>
              )}
              {lines.items.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name} ({l.category_code})
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
            placeholder="Green Morning"
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
            placeholder="green-morning"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Description
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={disabled}
            placeholder="Spinach, cucumber, apple, ginger, lemon"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Target Benefit
          </label>
          <input
            type="text"
            value={targetBenefit}
            onChange={(e) => setTargetBenefit(e.target.value)}
            disabled={disabled}
            placeholder="Morning hydration, micronutrient loading"
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Default Serving Size (ml)
            </label>
            <input
              type="number"
              inputMode="decimal"
              value={servingSizeMl}
              onChange={(e) => setServingSizeMl(e.target.value)}
              disabled={disabled}
              placeholder="300"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
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
              placeholder="24"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Target COGS
            </label>
            <input
              type="number"
              step="0.01"
              inputMode="decimal"
              value={targetCogs}
              onChange={(e) => setTargetCogs(e.target.value)}
              disabled={disabled}
              placeholder="38.30"
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Default Price
            </label>
            <input
              type="number"
              step="0.01"
              inputMode="decimal"
              value={defaultPrice}
              onChange={(e) => setDefaultPrice(e.target.value)}
              disabled={disabled}
              required
              placeholder="99.00"
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
            onChange={(e) => setStatus(e.target.value as ProductStatus)}
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

        <fieldset>
          <legend className="mb-2 block text-sm font-medium ">
            Tags
          </legend>
          {tags.status === "loading" && (
            <p className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>Loading tags…</p>
          )}
          {tags.status === "error" && (
            <p className="text-xs text-red-700">
              Failed to load tags: {tags.message}
            </p>
          )}
          {tags.status === "ok" && (
            <div className="flex flex-wrap gap-2">
              {tags.items.map((tag) => {
                const checked = selectedTags.has(tag.code);
                return (
                  <label
                    key={tag.id}
                    className={`inline-flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-xs ${
                      checked
                        ? "bg-[#2D72D2] text-white border-[#2D72D2]"
                        : "bg-white border-[#E5E8EB] text-[#1C2127]"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleTag(tag.code)}
                      disabled={disabled}
                      className="hidden"
                    />
                    {tag.name}
                  </label>
                );
              })}
            </div>
          )}
        </fieldset>

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={disabled || lines.status !== "ok" || productLineId === ""}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Product"}
          </button>
          <Link
            href="/catalog/products"
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
