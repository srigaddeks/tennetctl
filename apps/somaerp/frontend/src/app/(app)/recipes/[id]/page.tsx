"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createRecipeIngredient,
  createRecipeStep,
  deleteRecipeIngredient,
  deleteRecipeStep,
  getRecipe,
  getRecipeCost,
  listRawMaterials,
  listRecipeIngredients,
  listRecipeSteps,
  listUnitsOfMeasure,
} from "@/lib/api";
import type {
  RawMaterial,
  Recipe,
  RecipeCostSummary,
  RecipeIngredient,
  RecipeStep,
  RecipeStatus,
  UnitOfMeasure,
} from "@/types/api";

type RecipeState =
  | { status: "loading" }
  | { status: "ok"; recipe: Recipe }
  | { status: "error"; message: string };

type IngredientsState =
  | { status: "loading" }
  | { status: "ok"; items: RecipeIngredient[] }
  | { status: "error"; message: string };

type StepsState =
  | { status: "loading" }
  | { status: "ok"; items: RecipeStep[] }
  | { status: "error"; message: string };

type CostState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ok"; data: RecipeCostSummary }
  | { status: "error"; message: string };

type NewIngredient = {
  raw_material_id: string;
  quantity: string;
  unit_id: string;
  position: string;
};

type NewStep = {
  step_number: string;
  name: string;
  duration_min: string;
  instructions: string;
};

export default function RecipeDetailPage() {
  const params = useParams<{ id: string }>();
  const recipeId = params?.id ?? ""

  const [recipe, setRecipe] = useState<RecipeState>({ status: "loading" });
  const [ingredients, setIngredients] = useState<IngredientsState>({ status: "loading" });
  const [steps, setSteps] = useState<StepsState>({ status: "loading" });
  const [materials, setMaterials] = useState<RawMaterial[]>([]);
  const [units, setUnits] = useState<UnitOfMeasure[]>([]);
  const [serverCost, setServerCost] = useState<CostState>({ status: "idle" });

  const [draftIngredient, setDraftIngredient] = useState<NewIngredient>({
    raw_material_id: "",
    quantity: "",
    unit_id: "",
    position: "",
  });
  const [draftStep, setDraftStep] = useState<NewStep>({
    step_number: "",
    name: "",
    duration_min: "",
    instructions: "",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  const loadRecipe = useCallback(() => {
    if (!recipeId) return;
    setRecipe({ status: "loading" });
    getRecipe(recipeId)
      .then((r) => setRecipe({ status: "ok", recipe: r }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setRecipe({ status: "error", message });
      });
  }, [recipeId]);

  const loadIngredients = useCallback(() => {
    if (!recipeId) return;
    setIngredients({ status: "loading" });
    listRecipeIngredients(recipeId)
      .then((items) => setIngredients({ status: "ok", items }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setIngredients({ status: "error", message });
      });
  }, [recipeId]);

  const loadSteps = useCallback(() => {
    if (!recipeId) return;
    setSteps({ status: "loading" });
    listRecipeSteps(recipeId)
      .then((items) => setSteps({ status: "ok", items }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setSteps({ status: "error", message });
      });
  }, [recipeId]);

  const loadCost = useCallback(() => {
    if (!recipeId) return;
    setServerCost({ status: "loading" });
    getRecipeCost(recipeId)
      .then((data) => setServerCost({ status: "ok", data }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setServerCost({ status: "error", message });
      });
  }, [recipeId]);

  useEffect(() => {
    loadRecipe();
    loadIngredients();
    loadSteps();
    loadCost();
    listRawMaterials()
      .then(setMaterials)
      .catch(() => undefined);
    listUnitsOfMeasure()
      .then(setUnits)
      .catch(() => undefined);
  }, [loadRecipe, loadIngredients, loadSteps, loadCost]);

  // Live client-side cost (re-computed as ingredients load).
  const clientCost = useMemo(() => {
    if (ingredients.status !== "ok") {
      return { total: 0, currency: "INR", lines: [] as ClientLine[], hasUnconvertible: false };
    }
    const lines: ClientLine[] = [];
    let total = 0;
    let hasUnconvertible = false;
    let currency = "INR";
    for (const ing of ingredients.items) {
      const qty = Number.parseFloat(ing.quantity);
      const unitFactor = Number.parseFloat(
        units.find((u) => u.id === ing.unit_id)?.to_base_factor ?? "0"
      );
      const material = materials.find((m) => m.id === ing.raw_material_id);
      const defUnit = units.find((u) => u.id === material?.default_unit_id);
      const defFactor = Number.parseFloat(defUnit?.to_base_factor ?? "0");
      const unitCost = material?.target_unit_cost
        ? Number.parseFloat(material.target_unit_cost)
        : null;
      let lineCost: number | null = null;
      let unconvertible = true;
      if (
        unitCost !== null &&
        defUnit !== undefined &&
        ing.unit_dimension === defUnit.dimension &&
        defFactor > 0
      ) {
        lineCost = qty * (unitFactor / defFactor) * unitCost;
        unconvertible = false;
        total += lineCost;
      } else {
        hasUnconvertible = true;
      }
      if (material?.currency_code) currency = material.currency_code;
      lines.push({
        ingredient_id: ing.id,
        raw_material_name: ing.raw_material_name ?? material?.name ?? ing.raw_material_id,
        quantity: qty,
        unit_code: ing.unit_code ?? "",
        unit_cost: unitCost,
        line_cost: lineCost,
        unconvertible,
      });
    }
    return { total, currency, lines, hasUnconvertible };
  }, [ingredients, materials, units]);

  async function onCreateIngredient() {
    setFormError(null);
    const qty = Number.parseFloat(draftIngredient.quantity);
    const unitId = Number.parseInt(draftIngredient.unit_id, 10);
    const pos = draftIngredient.position.trim() === "" ? 1
      : Number.parseInt(draftIngredient.position, 10);
    if (!draftIngredient.raw_material_id) {
      setFormError("Pick a raw material");
      return;
    }
    if (!Number.isFinite(qty) || qty <= 0) {
      setFormError("Quantity must be a positive number");
      return;
    }
    if (!Number.isFinite(unitId)) {
      setFormError("Pick a unit");
      return;
    }
    setBusy(true);
    try {
      await createRecipeIngredient(recipeId, {
        raw_material_id: draftIngredient.raw_material_id,
        quantity: qty,
        unit_id: unitId,
        position: pos,
      });
      setDraftIngredient({ raw_material_id: "", quantity: "", unit_id: "", position: "" });
      loadIngredients();
      loadCost();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteIngredient(ingredientId: string) {
    setBusy(true);
    try {
      await deleteRecipeIngredient(recipeId, ingredientId);
      loadIngredients();
      loadCost();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  async function onCreateStep() {
    setFormError(null);
    const num = Number.parseInt(draftStep.step_number, 10);
    if (!Number.isFinite(num) || num <= 0) {
      setFormError("Step number must be a positive integer");
      return;
    }
    if (draftStep.name.trim() === "") {
      setFormError("Step name required");
      return;
    }
    const dur = draftStep.duration_min.trim() === "" ? null
      : Number.parseInt(draftStep.duration_min, 10);
    setBusy(true);
    try {
      await createRecipeStep(recipeId, {
        step_number: num,
        name: draftStep.name.trim(),
        duration_min: dur ?? undefined,
        instructions: draftStep.instructions.trim() || undefined,
      });
      setDraftStep({ step_number: "", name: "", duration_min: "", instructions: "" });
      loadSteps();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteStep(stepId: string) {
    setBusy(true);
    try {
      await deleteRecipeStep(recipeId, stepId);
      loadSteps();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          {recipe.status === "ok"
            ? `${recipe.recipe.product_name ?? "Recipe"} v${recipe.recipe.version}`
            : "Recipe"}
        </h1>
      </div>

      {/* Info panel */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {recipe.status === "loading" && <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading recipe…</p>}
        {recipe.status === "error" && (
          <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load recipe</p>
            <p className="mt-1 text-sm opacity-80">{recipe.message}</p>
          </div>
        )}
        {recipe.status === "ok" && (
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <InfoField label="Product" value={recipe.recipe.product_name ?? recipe.recipe.product_id} />
            <InfoField label="Version" value={<code className="font-mono">v{recipe.recipe.version}</code>} />
            <InfoField label="Status" value={<StatusBadge status={recipe.recipe.status} />} />
            <InfoField label="Effective From" value={recipe.recipe.effective_from ?? "—"} />
            {recipe.recipe.notes && (
              <div className="sm:col-span-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
                  Notes
                </dt>
                <dd className="mt-1 text-sm ">{recipe.recipe.notes}</dd>
              </div>
            )}
          </dl>
        )}
      </div>

      {/* Live cost panel */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>BOM Cost (live)</h2>
        </div>
        <div className="flex items-baseline gap-3">
          <p className="text-3xl font-bold ">
            {clientCost.currency} {clientCost.total.toFixed(2)}
          </p>
          <span className="text-sm" style={{ color: "var(--text-muted)" }}>per batch</span>
        </div>
        {clientCost.hasUnconvertible && (
          <p className="mt-2 text-xs text-yellow-700">
            Some ingredients have unit dimensions that can&apos;t be converted; those lines are excluded from total.
          </p>
        )}
        {clientCost.lines.length > 0 && (
          <table className="mt-4 min-w-full divide-y divide-slate-200 text-sm">
            <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Ingredient</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit Cost</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Line Cost</th>
              </tr>
            </thead>
            <tbody >
              {clientCost.lines.map((l) => (
                <tr key={l.ingredient_id}>
                  <td className="px-3 py-2 ">{l.raw_material_name}</td>
                  <td className="px-3 py-2 font-mono ">
                    {l.quantity} {l.unit_code}
                  </td>
                  <td className="px-3 py-2 font-mono ">
                    {l.unit_cost !== null ? l.unit_cost.toFixed(2) : "—"}
                  </td>
                  <td className="px-3 py-2 font-mono ">
                    {l.unconvertible ? (
                      <span className="text-yellow-700">unconvertible</span>
                    ) : l.line_cost !== null ? (
                      l.line_cost.toFixed(2)
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Ingredients editable table */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Ingredients</h2>
        </div>
        {ingredients.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading ingredients…</p>
        )}
        {ingredients.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load ingredients</p>
            <p className="mt-1 text-sm opacity-80">{ingredients.message}</p>
          </div>
        )}
        {ingredients.status === "ok" && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Pos</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}></th>
                </tr>
              </thead>
              <tbody >
                {ingredients.items.map((ing) => (
                  <tr key={ing.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{ing.position}</td>
                    <td className="px-4 py-3 ">
                      {ing.raw_material_name ?? ing.raw_material_id}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{ing.quantity}</td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{ing.unit_code}</td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => onDeleteIngredient(ing.id)}
                        disabled={busy}
                        className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium  shadow-sm hover:bg-slate-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {/* Add-row */}
                <tr className="bg-slate-50/50">
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={1}
                      value={draftIngredient.position}
                      onChange={(e) =>
                        setDraftIngredient((prev) => ({ ...prev, position: e.target.value }))
                      }
                      placeholder="#"
                      className="w-16 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={draftIngredient.raw_material_id}
                      onChange={(e) =>
                        setDraftIngredient((prev) => ({
                          ...prev,
                          raw_material_id: e.target.value,
                        }))
                      }
                      className="w-full rounded border px-2 py-1 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    >
                      <option value="">Pick…</option>
                      {materials.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      step="0.001"
                      value={draftIngredient.quantity}
                      onChange={(e) =>
                        setDraftIngredient((prev) => ({ ...prev, quantity: e.target.value }))
                      }
                      placeholder="200"
                      className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={draftIngredient.unit_id}
                      onChange={(e) =>
                        setDraftIngredient((prev) => ({ ...prev, unit_id: e.target.value }))
                      }
                      className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    >
                      <option value="">Unit…</option>
                      {units.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={onCreateIngredient}
                      disabled={busy}
                      className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
                    >
                      Add
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Steps</h2>
        </div>
        {steps.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading steps…</p>}
        {steps.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load steps</p>
            <p className="mt-1 text-sm opacity-80">{steps.message}</p>
          </div>
        )}
        {steps.status === "ok" && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Duration (min)</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Instructions</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}></th>
                </tr>
              </thead>
              <tbody >
                {steps.items.map((s) => (
                  <tr key={s.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{s.step_number}</td>
                    <td className="px-4 py-3 ">{s.name}</td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{s.duration_min ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{s.instructions ?? "—"}</td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => onDeleteStep(s.id)}
                        disabled={busy}
                        className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium  shadow-sm hover:bg-slate-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {/* Add-row */}
                <tr className="bg-slate-50/50">
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={1}
                      value={draftStep.step_number}
                      onChange={(e) =>
                        setDraftStep((prev) => ({ ...prev, step_number: e.target.value }))
                      }
                      placeholder="#"
                      className="w-16 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={draftStep.name}
                      onChange={(e) =>
                        setDraftStep((prev) => ({ ...prev, name: e.target.value }))
                      }
                      placeholder="Wash all produce"
                      className="w-full rounded border px-2 py-1 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={0}
                      value={draftStep.duration_min}
                      onChange={(e) =>
                        setDraftStep((prev) => ({ ...prev, duration_min: e.target.value }))
                      }
                      placeholder="10"
                      className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={draftStep.instructions}
                      onChange={(e) =>
                        setDraftStep((prev) => ({ ...prev, instructions: e.target.value }))
                      }
                      placeholder="Triple rinse"
                      className="w-full rounded border px-2 py-1 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={onCreateStep}
                      disabled={busy}
                      className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
                    >
                      Add
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {formError !== null && (
        <div className="mb-6 rounded border border-red-300 bg-red-50 p-4">
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{formError}</p>
        </div>
      )}
    </div>
  );
}

type ClientLine = {
  ingredient_id: string;
  raw_material_name: string;
  quantity: number;
  unit_code: string;
  unit_cost: number | null;
  line_cost: number | null;
  unconvertible: boolean;
};

function InfoField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </dt>
      <dd className="mt-1 text-sm ">{value}</dd>
    </div>
  );
}

function StatusBadge({ status }: { status: RecipeStatus }) {
  const styles: Record<RecipeStatus, string> = {
    draft: "bg-slate-100  border-slate-200",
    active: "bg-green-100 text-green-800 border-green-200",
    archived: "bg-yellow-100 text-yellow-800 border-yellow-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}
