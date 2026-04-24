"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createQcCheckpoint,
  listKitchens,
  listProducts,
  listQcCheckTypes,
  listQcStages,
  listRawMaterials,
  listRecipeSteps,
  listRecipes,
} from "@/lib/api";
import type {
  Kitchen,
  Product,
  QcCheckType,
  QcCheckpointScopeKind,
  QcCheckpointStatus,
  QcStage,
  RawMaterial,
  Recipe,
  RecipeStep,
} from "@/types/api";

type Option = { value: string; label: string };

type LookupsState =
  | { status: "loading" }
  | {
      status: "ok";
      stages: QcStage[];
      checkTypes: QcCheckType[];
    }
  | { status: "error"; message: string };

type SubmitState =
  | { status: "idle" }
  | { status: "submitting" }
  | { status: "error"; message: string };

const SCOPE_KINDS: ReadonlyArray<QcCheckpointScopeKind> = [
  "universal",
  "recipe_step",
  "raw_material",
  "kitchen",
  "product",
];
const STATUSES: ReadonlyArray<QcCheckpointStatus> = [
  "active",
  "paused",
  "archived",
];

export default function NewQcCheckpointPage() {
  const router = useRouter();
  const [lookups, setLookups] = useState<LookupsState>({ status: "loading" });

  const [stageId, setStageId] = useState<string>("");
  const [checkTypeId, setCheckTypeId] = useState<string>("");
  const [scopeKind, setScopeKind] = useState<QcCheckpointScopeKind>("universal");

  // scope_ref candidates per scope_kind
  const [rawMaterials, setRawMaterials] = useState<RawMaterial[]>([]);
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selectedRecipeId, setSelectedRecipeId] = useState<string>("");
  const [recipeSteps, setRecipeSteps] = useState<RecipeStep[]>([]);
  const [scopeRefId, setScopeRefId] = useState<string>("");

  const [name, setName] = useState<string>("");
  const [criteriaText, setCriteriaText] = useState<string>("{}");
  const [required, setRequired] = useState<boolean>(true);
  const [status, setStatus] = useState<QcCheckpointStatus>("active");
  const [submit, setSubmit] = useState<SubmitState>({ status: "idle" });

  // Load stages + check types on mount.
  useEffect(() => {
    let cancelled = false;
    Promise.all([listQcStages(), listQcCheckTypes()])
      .then(([stages, checkTypes]) => {
        if (cancelled) return;
        setLookups({ status: "ok", stages, checkTypes });
        if (stages.length > 0) setStageId(String(stages[0].id));
        if (checkTypes.length > 0) setCheckTypeId(String(checkTypes[0].id));
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setLookups({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Load scope-kind-specific candidates when scope_kind changes.
  useEffect(() => {
    let cancelled = false;
    setScopeRefId("");
    setSelectedRecipeId("");
    setRecipeSteps([]);
    if (scopeKind === "raw_material") {
      listRawMaterials()
        .then((items) => {
          if (!cancelled) setRawMaterials(items);
        })
        .catch(() => {
          if (!cancelled) setRawMaterials([]);
        });
    } else if (scopeKind === "kitchen") {
      listKitchens()
        .then((items) => {
          if (!cancelled) setKitchens(items);
        })
        .catch(() => {
          if (!cancelled) setKitchens([]);
        });
    } else if (scopeKind === "product") {
      listProducts()
        .then((items) => {
          if (!cancelled) setProducts(items);
        })
        .catch(() => {
          if (!cancelled) setProducts([]);
        });
    } else if (scopeKind === "recipe_step") {
      listRecipes()
        .then((items) => {
          if (!cancelled) setRecipes(items);
        })
        .catch(() => {
          if (!cancelled) setRecipes([]);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [scopeKind]);

  // When recipe chosen, fetch its steps.
  useEffect(() => {
    let cancelled = false;
    if (scopeKind !== "recipe_step" || selectedRecipeId === "") {
      setRecipeSteps([]);
      return;
    }
    listRecipeSteps(selectedRecipeId)
      .then((items) => {
        if (cancelled) return;
        setRecipeSteps(items);
        if (items.length > 0) setScopeRefId(items[0].id);
      })
      .catch(() => {
        if (!cancelled) setRecipeSteps([]);
      });
    return () => {
      cancelled = true;
    };
  }, [scopeKind, selectedRecipeId]);

  const scopeRefOptions = buildScopeRefOptions({
    scopeKind,
    rawMaterials,
    kitchens,
    products,
    recipeSteps,
  });

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const stageNum = Number.parseInt(stageId, 10);
    const checkTypeNum = Number.parseInt(checkTypeId, 10);
    if (!Number.isFinite(stageNum) || !Number.isFinite(checkTypeNum)) {
      setSubmit({ status: "error", message: "Pick a stage and a check type" });
      return;
    }
    let criteria: Record<string, unknown> = {};
    try {
      const parsed = JSON.parse(criteriaText === "" ? "{}" : criteriaText);
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Criteria must be a JSON object");
      }
      criteria = parsed as Record<string, unknown>;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Invalid JSON";
      setSubmit({ status: "error", message: `Criteria: ${msg}` });
      return;
    }
    if (scopeKind !== "universal" && scopeRefId.trim() === "") {
      setSubmit({
        status: "error",
        message: `scope_ref_id required for scope_kind=${scopeKind}`,
      });
      return;
    }
    setSubmit({ status: "submitting" });
    try {
      await createQcCheckpoint({
        stage_id: stageNum,
        check_type_id: checkTypeNum,
        scope_kind: scopeKind,
        scope_ref_id: scopeKind === "universal" ? null : scopeRefId,
        name: name.trim(),
        criteria_jsonb: criteria,
        required,
        status,
      });
      router.push("/quality/checkpoints");
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
          New Checkpoint
        </h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        {lookups.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading lookups…</p>
        )}
        {lookups.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            Failed to load lookups: {lookups.message}
          </div>
        )}

        {lookups.status === "ok" && (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Stage
                </label>
                <select
                  value={stageId}
                  onChange={(e) => setStageId(e.target.value)}
                  disabled={disabled}
                  required
                  className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                >
                  {lookups.stages.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Check Type
                </label>
                <select
                  value={checkTypeId}
                  onChange={(e) => setCheckTypeId(e.target.value)}
                  disabled={disabled}
                  required
                  className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                >
                  {lookups.checkTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <fieldset>
              <legend className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                Scope Kind
              </legend>
              <div className="flex flex-wrap gap-3">
                {SCOPE_KINDS.map((sk) => (
                  <label
                    key={sk}
                    className="inline-flex items-center gap-2 text-sm "
                  >
                    <input
                      type="radio"
                      name="scope_kind"
                      value={sk}
                      checked={scopeKind === sk}
                      onChange={() => setScopeKind(sk)}
                      disabled={disabled}
                    />
                    <span>{sk}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            {scopeKind === "recipe_step" && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                    Recipe
                  </label>
                  <select
                    value={selectedRecipeId}
                    onChange={(e) => setSelectedRecipeId(e.target.value)}
                    disabled={disabled}
                    required
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  >
                    <option value="">— pick a recipe —</option>
                    {recipes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.product_name ?? r.id} (v{r.version}, {r.status})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                    Step
                  </label>
                  <select
                    value={scopeRefId}
                    onChange={(e) => setScopeRefId(e.target.value)}
                    disabled={disabled || recipeSteps.length === 0}
                    required
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  >
                    <option value="">— pick a step —</option>
                    {recipeSteps.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.step_number}. {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {scopeKind !== "universal" && scopeKind !== "recipe_step" && (
              <div>
                <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Scope Ref ({scopeKind})
                </label>
                <select
                  value={scopeRefId}
                  onChange={(e) => setScopeRefId(e.target.value)}
                  disabled={disabled}
                  required
                  className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                >
                  <option value="">— pick a {scopeKind} —</option>
                  {scopeRefOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
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
                onChange={(e) => setName(e.target.value)}
                disabled={disabled}
                required
                placeholder="Spinach color & freshness"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                Criteria (JSON)
              </label>
              <textarea
                rows={5}
                value={criteriaText}
                onChange={(e) => setCriteriaText(e.target.value)}
                disabled={disabled}
                placeholder='{"min_temp_c": 2, "max_temp_c": 8}'
                className="w-full rounded border px-3 py-2 font-mono text-xs focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="inline-flex items-center gap-2 text-sm ">
                <input
                  type="checkbox"
                  checked={required}
                  onChange={(e) => setRequired(e.target.checked)}
                  disabled={disabled}
                />
                <span>Required (failure blocks batch)</span>
              </label>
              <div>
                <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as QcCheckpointStatus)}
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
          </>
        )}

        {submit.status === "error" && (
          <div className="rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            {submit.message}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={disabled || lookups.status !== "ok"}
            className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            {disabled ? "Creating…" : "Create Checkpoint"}
          </button>
          <Link
            href="/quality/checkpoints"
            className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function buildScopeRefOptions({
  scopeKind,
  rawMaterials,
  kitchens,
  products,
  recipeSteps,
}: {
  scopeKind: QcCheckpointScopeKind;
  rawMaterials: RawMaterial[];
  kitchens: Kitchen[];
  products: Product[];
  recipeSteps: RecipeStep[];
}): Option[] {
  switch (scopeKind) {
    case "raw_material":
      return rawMaterials.map((r) => ({ value: r.id, label: r.name }));
    case "kitchen":
      return kitchens.map((k) => ({ value: k.id, label: k.name }));
    case "product":
      return products.map((p) => ({ value: p.id, label: p.name }));
    case "recipe_step":
      return recipeSteps.map((s) => ({
        value: s.id,
        label: `${s.step_number}. ${s.name}`,
      }));
    default:
      return [];
  }
}
