"use client";

import { useEffect, useState } from "react";

import { listProducts, type Product } from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; data: Product[] }
  | { status: "error"; message: string };

export default function ProductsPage() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    listProducts()
      .then((data) => setState({ status: "ok", data }))
      .catch((e: unknown) =>
        setState({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load products",
        }),
      );
  }, []);

  return (
    <div>
      <header className="mb-12 max-w-reading">
        <p
          className="text-sm tracking-[0.2em] uppercase mb-3"
          style={{ color: "var(--text-muted)" }}
        >
          The menu
        </p>
        <h1 className="font-heading text-4xl font-bold mb-4">Today's pressing</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Bottles + shots, cold-pressed in our Hyderabad kitchen.
        </p>
      </header>

      {state.status === "loading" && (
        <div style={{ color: "var(--text-muted)" }}>Loading...</div>
      )}

      {state.status === "error" && (
        <div
          className="border-l-2 pl-4 py-2"
          style={{ borderColor: "var(--status-error)", color: "var(--status-error)" }}
        >
          {state.message}
          {state.message.includes("sign in") && (
            <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>
              You'll need to sign in to see the menu.
            </p>
          )}
        </div>
      )}

      {state.status === "ok" && state.data.length === 0 && (
        <p style={{ color: "var(--text-muted)" }}>No products yet.</p>
      )}

      {state.status === "ok" && state.data.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {state.data.map((p) => (
            <article key={p.id} className="card p-6">
              <h3 className="font-heading text-xl font-semibold mb-2">
                {p.name}
              </h3>
              <p
                className="text-sm mb-4"
                style={{ color: "var(--text-muted)" }}
              >
                {p.slug}
              </p>
              {p.description && (
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {p.description}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
