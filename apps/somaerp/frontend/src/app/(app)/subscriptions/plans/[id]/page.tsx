"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  addSubscriptionPlanItem,
  deleteSubscriptionPlanItem,
  getSubscriptionPlan,
  listProducts,
} from "@/lib/api";
import type {
  Product,
  SubscriptionPlan,
  SubscriptionPlanItem,
} from "@/types/api";

type PlanState =
  | { status: "loading" }
  | { status: "ok"; plan: SubscriptionPlan; items: SubscriptionPlanItem[] }
  | { status: "error"; message: string };

export default function PlanDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [state, setState] = useState<PlanState>({ status: "loading" });
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState("");
  const [qty, setQty] = useState("1");
  const [notes, setNotes] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    setState({ status: "loading" });
    try {
      const detail = await getSubscriptionPlan(id);
      setState({
        status: "ok",
        plan: detail.plan,
        items: detail.items,
      });
    } catch (err: unknown) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  useEffect(() => {
    reload();
    listProducts().then(setProducts).catch(() => undefined);
  }, [id]);

  const onAddItem = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setAdding(true);
    setError(null);
    try {
      if (!productId) throw new Error("Choose a product.");
      await addSubscriptionPlanItem(id, {
        product_id: productId,
        qty_per_delivery: Number.parseFloat(qty),
        notes: notes || undefined,
      });
      setProductId("");
      setQty("1");
      setNotes("");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setAdding(false);
    }
  };

  const onRemoveItem = async (itemId: string) => {
    if (!confirm("Remove this plan item?")) return;
    try {
      await deleteSubscriptionPlanItem(id, itemId);
      await reload();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        {state.status === "ok" && (
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {state.plan.name}
          </h1>
        )}
      </div>

      {state.status === "loading" && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading plan…</p>
      )}
      {state.status === "error" && (
        <p className="text-red-700">{state.message}</p>
      )}

      {state.status === "ok" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Plan Info
            </h2>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="">Slug</dt>
              <dd className="font-mono">{state.plan.slug}</dd>
              <dt className="">Frequency</dt>
              <dd>{state.plan.frequency_name ?? "—"}</dd>
              <dt className="">Deliveries / wk</dt>
              <dd className="font-mono">{state.plan.deliveries_per_week ?? "—"}</dd>
              <dt className="">Price / delivery</dt>
              <dd className="font-mono">
                {state.plan.price_per_delivery !== null
                  ? `${state.plan.currency_code} ${state.plan.price_per_delivery}`
                  : "custom"}
              </dd>
              <dt className="">Status</dt>
              <dd>{state.plan.status}</dd>
              <dt className="">Items</dt>
              <dd className="font-mono">{state.plan.item_count}</dd>
            </dl>
            {state.plan.description && (
              <p className="mt-3 text-sm ">
                {state.plan.description}
              </p>
            )}
          </div>

          <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide ">
              Items ({state.items.length})
            </h2>
            {state.items.length === 0 && (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No items yet.</p>
            )}
            {state.items.length > 0 && (
              <ul >
                {state.items.map((it) => (
                  <li
                    key={it.id}
                    className="flex items-center justify-between py-2 text-sm"
                  >
                    <div>
                      <div className="font-medium ">
                        {it.product_name ?? it.product_id}
                        {it.variant_name && (
                          <span className="ml-1 text-sm" style={{ color: "var(--text-muted)" }}>
                            ({it.variant_name})
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                        qty/delivery: {it.qty_per_delivery}
                        {it.line_price !== null && (
                          <span> · line: {it.currency_code} {it.line_price}</span>
                        )}
                      </div>
                      {it.notes && (
                        <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>{it.notes}</div>
                      )}
                    </div>
                    <button
                      onClick={() => onRemoveItem(it.id)}
                      className="text-xs font-medium text-red-700 hover:underline"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <form
              onSubmit={onAddItem}
              className="mt-4 space-y-3 border-t border-slate-200 pt-4"
            >
              <h3 className="text-xs font-semibold uppercase tracking-wide ">
                Add Item
              </h3>
              <select
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                required
              >
                <option value="">Choose product…</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <div className="flex gap-2">
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="w-32 rounded border px-3 py-2 font-mono text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                  placeholder="qty"
                  required
                />
                <input
                  className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="notes"
                />
              </div>
              {error && (
                <p className="rounded border border-red-300 bg-red-50 p-2 text-xs text-red-700">
                  {error}
                </p>
              )}
              <button
                type="submit"
                disabled={adding}
                className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {adding ? "Adding…" : "Add Item"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
