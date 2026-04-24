"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createProductLine, listCategories } from "@/lib/api";
import type { ProductCategory, ProductLineStatus } from "@/types/api";

type CategoriesState =
  | { status: "loading" }
  | { status: "ok"; items: ProductCategory[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<ProductLineStatus> = [
  "active",
  "paused",
  "discontinued",
];

export default function NewProductLinePage() {
  const router = useRouter();

  const [categories, setCategories] = useState<CategoriesState>({
    status: "loading",
  });
  const [categoryId, setCategoryId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [slug, setSlug] = useState<string>("");
  const [slugTouched, setSlugTouched] = useState<boolean>(false);
  const [status, setStatus] = useState<ProductLineStatus>("active");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listCategories()
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
    const categoryNum = Number.parseInt(categoryId, 10);
    if (!Number.isFinite(categoryNum)) {
      setSubmit({ status: "error", message: "Pick a category" });
      return;
    }

    setSubmit({ status: "submitting" });
    try {
      await createProductLine({
        category_id: categoryNum,
        name: name.trim(),
        slug: slug.trim(),
        status,
      });
      router.push("/catalog/product-lines");
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
          New Product Line
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
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
            placeholder="Cold-Pressed Drinks"
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
            placeholder="cold-pressed-drinks"
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Auto-derived from name. Edit to override.
          </p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ProductLineStatus)}
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
            disabled={disabled || categories.status !== "ok" || categoryId === ""}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Product Line"}
          </button>
          <Link
            href="/catalog/product-lines"
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
