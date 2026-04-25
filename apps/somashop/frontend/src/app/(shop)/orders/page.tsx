"use client";

import { useEffect, useState } from "react";

import { listMyOrders, type Order } from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; data: Order[] }
  | { status: "error"; message: string };

export default function OrdersPage() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    listMyOrders()
      .then((data) => setState({ status: "ok", data }))
      .catch((e: unknown) =>
        setState({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load orders",
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
          Your subscriptions
        </p>
        <h1 className="font-heading text-4xl font-bold mb-4">Orders</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          Active and past deliveries from your Soma Delights subscription.
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
        </div>
      )}

      {state.status === "ok" && state.data.length === 0 && (
        <p style={{ color: "var(--text-muted)" }}>
          No orders yet. Browse the menu to start.
        </p>
      )}

      {state.status === "ok" && state.data.length > 0 && (
        <div className="space-y-3">
          {state.data.map((o) => (
            <div key={o.id} className="card p-5 flex justify-between items-center">
              <div>
                <p className="font-medium mb-1">Order {o.id.slice(0, 8)}</p>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  {new Date(o.created_at).toLocaleDateString(undefined, {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </p>
              </div>
              <span
                className="text-xs uppercase tracking-widest font-semibold"
                style={{ color: "var(--text-secondary)" }}
              >
                {o.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
