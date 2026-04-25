"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  listPlans,
  listProducts,
  type Product,
  type SubscriptionPlan,
} from "@/lib/api";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

function formatINR(amount: number | string | null | undefined): string {
  if (amount == null) return "—";
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  if (!Number.isFinite(n)) return "—";
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<State<Product[]>>({ status: "loading" });
  const [plans, setPlans] = useState<State<SubscriptionPlan[]>>({ status: "loading" });

  useEffect(() => {
    listProducts()
      .then((data) => setProducts({ status: "ok", data }))
      .catch((e: unknown) =>
        setProducts({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load",
        }),
      );
    listPlans()
      .then((data) => setPlans({ status: "ok", data }))
      .catch((e: unknown) =>
        setPlans({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load",
        }),
      );
  }, []);

  return (
    <div className="space-y-20">
      {/* Plans hero */}
      <section>
        <header className="max-w-reading mb-10">
          <p
            className="text-sm tracking-[0.2em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Subscription plans
          </p>
          <h1 className="font-heading text-4xl font-bold mb-4">Pick your cadence</h1>
          <p style={{ color: "var(--text-secondary)" }}>
            Three plans for three rhythms. All cold-pressed daily, delivered
            before breakfast.
          </p>
        </header>

        {plans.status === "loading" && (
          <div style={{ color: "var(--text-muted)" }}>Loading plans…</div>
        )}
        {plans.status === "ok" && plans.data.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.data.map((p) => (
              <article key={p.id} className="card p-8 flex flex-col">
                <div className="mb-4">
                  <h3 className="font-heading text-2xl font-bold mb-2">{p.name}</h3>
                  <p
                    className="font-mono text-sm uppercase tracking-widest"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {p.frequency_name ?? p.frequency_code ?? "—"}
                  </p>
                </div>
                <p
                  className="text-sm leading-relaxed mb-6 flex-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {p.description}
                </p>
                <div className="mb-6">
                  <span className="font-heading text-3xl font-bold">
                    {formatINR(p.price_per_delivery ?? null)}
                  </span>
                  <span
                    className="text-sm ml-2"
                    style={{ color: "var(--text-muted)" }}
                  >
                    / delivery
                  </span>
                </div>
                <Link href={`/checkout?plan=${p.slug}`} className="btn btn-primary w-full">
                  Subscribe
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Products gallery */}
      <section>
        <header className="max-w-reading mb-10">
          <p
            className="text-sm tracking-[0.2em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Today's pressing
          </p>
          <h2 className="font-heading text-3xl font-bold mb-4">The full menu</h2>
          <p style={{ color: "var(--text-secondary)" }}>
            Bottles + shots, cold-pressed in our Hyderabad kitchen.
          </p>
        </header>

        {products.status === "loading" && (
          <div style={{ color: "var(--text-muted)" }}>Loading products…</div>
        )}
        {products.status === "error" && (
          <div
            className="border-l-2 pl-4 py-2"
            style={{
              borderColor: "var(--status-error)",
              color: "var(--status-error)",
            }}
          >
            {products.message}
          </div>
        )}
        {products.status === "ok" && products.data.length === 0 && (
          <p style={{ color: "var(--text-muted)" }}>No products yet.</p>
        )}
        {products.status === "ok" && products.data.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.data.map((p) => (
              <Link
                key={p.id}
                href={`/products/${p.slug}`}
                className="card p-6 hover:opacity-80 transition-opacity block"
              >
                <p
                  className="text-xs tracking-[0.15em] uppercase mb-3"
                  style={{ color: "var(--text-muted)" }}
                >
                  {p.product_line_name ?? "—"}
                  {p.default_serving_size_ml
                    ? ` · ${Math.round(Number(p.default_serving_size_ml))} ml`
                    : ""}
                </p>
                <h3 className="font-heading text-xl font-semibold mb-2">{p.name}</h3>
                {p.target_benefit && (
                  <p
                    className="text-sm italic mb-3"
                    style={{
                      color: "var(--text-secondary)",
                      fontFamily: "var(--font-quote)",
                    }}
                  >
                    {p.target_benefit}
                  </p>
                )}
                {p.description && (
                  <p
                    className="text-sm leading-relaxed mb-4"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {p.description}
                  </p>
                )}
                <div className="flex justify-between items-baseline mt-auto">
                  <span className="font-heading text-lg font-semibold">
                    {formatINR(p.default_selling_price ?? null)}
                  </span>
                  <span
                    className="text-xs uppercase tracking-widest"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Read more →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
