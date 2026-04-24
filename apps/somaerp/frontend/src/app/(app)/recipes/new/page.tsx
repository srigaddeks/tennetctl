"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createRecipe, listProducts } from "@/lib/api";
import type { Product, RecipeStatus } from "@/types/api";

type ProductsState =
  | { status: "loading" }
  | { status: "ok"; items: Product[] }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<RecipeStatus> = ["draft", "active", "archived"];

export default function NewRecipePage() {
  const router = useRouter();
  const [products, setProducts] = useState<ProductsState>({ status: "loading" });
  const [productId, setProductId] = useState<string>("");
  const [version, setVersion] = useState<string>("1");
  const [status, setStatus] = useState<RecipeStatus>("draft");
  const [effectiveFrom, setEffectiveFrom] = useState<string>(today());
  const [notes, setNotes] = useState<string>("");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listProducts()
      .then((items) => {
        if (cancelled) return;
        setProducts({ status: "ok", items });
        if (items.length > 0) setProductId(items[0].id);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setProducts({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (productId === "") {
      setSubmit({ status: "error", message: "Pick a product" });
      return;
    }
    const versionNum = Number.parseInt(version, 10);
    if (!Number.isFinite(versionNum) || versionNum <= 0) {
      setSubmit({ status: "error", message: "Version must be a positive integer" });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      const created = await createRecipe({
        product_id: productId,
        version: versionNum,
        status,
        effective_from: effectiveFrom === "" ? null : effectiveFrom,
        notes: notes.trim() === "" ? null : notes.trim(),
      });
      router.push(`/recipes/${created.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmit({ status: "error", message });
    }
  }

  const disabled = submit.status === "submitting";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Recipe</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {products.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading products…</p>
        )}
        {products.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load products: {products.message}
          </div>
        )}
        {products.status === "ok" && (
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Product
            </label>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {products.items.length === 0 && (
                <option value="" disabled>
                  No products — create one first
                </option>
              )}
              {products.items.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Version
            </label>
            <input
              type="number"
              min={1}
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              disabled={disabled}
              required
              className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as RecipeStatus)}
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

        <div>
          <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
            Effective From
          </label>
          <input
            type="date"
            value={effectiveFrom}
            onChange={(e) => setEffectiveFrom(e.target.value)}
            disabled={disabled}
            className="w-full rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
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
            placeholder="Soma Delights Green Morning v1 — 300ml bottle"
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
            disabled={disabled || products.status !== "ok" || productId === ""}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Recipe"}
          </button>
          <Link
            href="/recipes"
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
