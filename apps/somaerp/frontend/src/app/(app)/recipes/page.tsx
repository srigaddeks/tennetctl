"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listProducts, listRecipes } from "@/lib/api";
import type { Product, Recipe, RecipeStatus } from "@/types/api";

type RecipesState = { status: "loading" } | { status: "ok"; items: Recipe[] } | { status: "error"; message: string };
type ProductsState = { status: "loading" } | { status: "ok"; items: Product[] } | { status: "error"; message: string };

const STATUSES: ReadonlyArray<RecipeStatus | ""> = ["", "draft", "active", "archived"];
const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

export default function RecipesListPage() {
  const [recipes, setRecipes] = useState<RecipesState>({ status: "loading" });
  const [products, setProducts] = useState<ProductsState>({ status: "loading" });
  const [productId, setProductId] = useState<string>("");
  const [status, setStatus] = useState<RecipeStatus | "">("");

  useEffect(() => {
    let cancelled = false;
    listProducts()
      .then((items) => { if (!cancelled) setProducts({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setProducts({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setRecipes({ status: "loading" });
    listRecipes({ product_id: productId || undefined, status: status || undefined })
      .then((items) => { if (!cancelled) setRecipes({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setRecipes({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [productId, status]);

  const productsById = useMemo(() => {
    if (products.status !== "ok") return new Map<string, Product>();
    return new Map(products.items.map((p) => [p.id, p]));
  }, [products]);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Recipes</h1>
          <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>Versioned recipes for each product — play with values, see live BOM cost.</p>
        </div>
        <Link href="/recipes/new" className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>+ New Recipe</Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
          Product
          <select value={productId} onChange={(e) => setProductId(e.target.value)} className="mt-1 rounded border px-3 py-1.5 text-sm" style={inputStyle}>
            <option value="">All products</option>
            {products.status === "ok" && products.items.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value as RecipeStatus | "")} className="mt-1 rounded border px-3 py-1.5 text-sm" style={inputStyle}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === "" ? "All" : s}</option>)}
          </select>
        </label>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {recipes.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading recipes…</p>}
        {recipes.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load recipes</span> <span className="opacity-80">{recipes.message}</span>
          </div>
        )}
        {recipes.status === "ok" && recipes.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No recipes yet.</p>
            <Link href="/recipes/new" className="mt-2 inline-block underline" style={{ color: "var(--text-accent)" }}>Create the first recipe</Link>
          </div>
        )}
        {recipes.status === "ok" && recipes.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Product", "Version", "Status", "Effective From", "Actions"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recipes.items.map((r, idx) => {
                  const productName = r.product_name ?? productsById.get(r.product_id)?.name ?? r.product_id;
                  return (
                    <tr key={r.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                      <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{productName}</td>
                      <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>v{r.version}</td>
                      <td className="px-4 py-2.5"><RecipeStatusPill status={r.status} /></td>
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{r.effective_from ?? "—"}</td>
                      <td className="px-4 py-2.5">
                        <Link href={`/recipes/${r.id}`} className="text-sm underline hover:no-underline" style={{ color: "var(--text-accent)" }}>Open</Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function RecipeStatusPill({ status }: { status: RecipeStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : status === "archived"
    ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
    : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}
