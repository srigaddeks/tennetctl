"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  createBatch,
  listKitchens,
  listProducts,
  listRecipeIngredients,
  listRecipes,
} from "@/lib/api";
import type {
  Kitchen,
  Product,
  Recipe,
  RecipeIngredient,
} from "@/types/api";

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string };

export default function NewBatchPage() {
  const router = useRouter();
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([]);

  const [kitchenId, setKitchenId] = useState<string>("");
  const [productId, setProductId] = useState<string>("");
  const [recipeId, setRecipeId] = useState<string>("");
  const [runDate, setRunDate] = useState<string>(
    () => new Date().toISOString().slice(0, 10)
  );
  const [plannedQty, setPlannedQty] = useState<string>("20");
  const [notes, setNotes] = useState<string>("");
  const [submitState, setSubmitState] = useState<LoadState>({ status: "idle" });

  useEffect(() => {
    void listKitchens().then(setKitchens).catch(() => setKitchens([]));
    void listProducts().then(setProducts).catch(() => setProducts([]));
  }, []);

  useEffect(() => {
    if (!productId) {
      setRecipes([]);
      setRecipeId("");
      return;
    }
    void listRecipes({ product_id: productId, limit: 50 })
      .then((rs) => {
        setRecipes(rs);
        const activeRecipe = rs.find((r) => r.status === "active");
        setRecipeId(activeRecipe?.id ?? "");
      })
      .catch(() => setRecipes([]));
  }, [productId]);

  useEffect(() => {
    if (!recipeId) {
      setIngredients([]);
      return;
    }
    void listRecipeIngredients(recipeId)
      .then(setIngredients)
      .catch(() => setIngredients([]));
  }, [recipeId]);

  const activeRecipe = useMemo(
    () => recipes.find((r) => r.id === recipeId) ?? null,
    [recipes, recipeId]
  );

  const plannedQtyNum = Number.parseFloat(plannedQty);
  const canSubmit =
    kitchenId !== "" &&
    productId !== "" &&
    Number.isFinite(plannedQtyNum) &&
    plannedQtyNum > 0;

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitState({ status: "loading" });
    try {
      const created = await createBatch({
        kitchen_id: kitchenId,
        product_id: productId,
        recipe_id: recipeId || undefined,
        run_date: runDate,
        planned_qty: plannedQtyNum,
        notes: notes || undefined,
      });
      router.push(`/production/batches/${created.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setSubmitState({ status: "error", message });
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <Link
          href="/production"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Production
        </Link>
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Batch</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Plan a production batch. Step logs and consumption lines will be
          auto-created from the recipe.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block font-medium ">
              Kitchen
            </span>
            <select
              value={kitchenId}
              onChange={(e) => setKitchenId(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              required
            >
              <option value="">Select a kitchen…</option>
              {kitchens.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium ">
              Product
            </span>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              required
            >
              <option value="">Select a product…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block font-medium ">
              Recipe
            </span>
            <select
              value={recipeId}
              onChange={(e) => setRecipeId(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              disabled={!productId}
            >
              <option value="">
                {productId
                  ? recipes.length === 0
                    ? "No recipes for this product"
                    : "Auto-pick active recipe"
                  : "Select a product first"}
              </option>
              {recipes.map((r) => (
                <option key={r.id} value={r.id}>
                  v{r.version} · {r.status}
                  {r.status === "active" ? " ✓" : ""}
                </option>
              ))}
            </select>
            {activeRecipe && (
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                Using recipe v{activeRecipe.version} ({activeRecipe.status}).
              </p>
            )}
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium ">
              Run date
            </span>
            <input
              type="date"
              value={runDate}
              onChange={(e) => setRunDate(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              required
            />
          </label>

          <label className="text-sm">
            <span className="mb-1 block font-medium ">
              Planned qty (bottles)
            </span>
            <input
              type="number"
              min="1"
              step="1"
              value={plannedQty}
              onChange={(e) => setPlannedQty(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              required
            />
          </label>

          <label className="text-sm sm:col-span-2">
            <span className="mb-1 block font-medium ">Notes</span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              placeholder="Optional operator notes"
            />
          </label>
        </div>

        {ingredients.length > 0 && Number.isFinite(plannedQtyNum) && (
          <div className="rounded border border-slate-200 bg-slate-50 p-3">
            <h2 className="mb-2 text-sm font-semibold ">
              Auto-planned ingredients ({ingredients.length})
            </h2>
            <ul className="space-y-1 text-xs ">
              {ingredients.map((i) => {
                const qty = Number.parseFloat(i.quantity) * plannedQtyNum;
                return (
                  <li key={i.id} className="flex justify-between">
                    <span>{i.raw_material_name ?? "—"}</span>
                    <span className="font-mono">
                      {qty.toFixed(2)} {i.unit_code ?? ""}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {submitState.status === "error" && (
          <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {submitState.message}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={!canSubmit || submitState.status === "loading"}
            className="rounded-md bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitState.status === "loading" ? "Creating…" : "Create Batch"}
          </button>
          <Link
            href="/production/batches"
            className="text-sm" style={{ color: "var(--text-secondary)" }}
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
