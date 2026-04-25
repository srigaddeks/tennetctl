"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { listMyOrders, type Order } from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; data: Order[] }
  | { status: "error"; message: string };

function formatINR(amount: number | string | null | undefined): string {
  if (amount == null) return "—";
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  if (!Number.isFinite(n)) return "—";
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

function statusTone(status: string): { label: string; bg: string; text: string } {
  const s = status.toLowerCase();
  if (s.includes("active")) return { label: "Active", bg: "var(--status-active-bg)", text: "var(--status-active-text)" };
  if (s.includes("paus")) return { label: "Paused", bg: "var(--status-paused-bg)", text: "var(--status-paused-text)" };
  if (s.includes("cancel") || s.includes("error")) return { label: status, bg: "var(--status-error-bg)", text: "var(--status-error-text)" };
  return { label: status, bg: "var(--status-draft-bg)", text: "var(--status-draft-text)" };
}

export default function OrdersPage() {
  const sp = useSearchParams();
  const justPlaced = sp?.get("placed") === "1";
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

      {justPlaced && (
        <div
          className="mb-8 p-4 border-l-2"
          style={{
            borderColor: "var(--status-active)",
            background: "var(--status-active-bg)",
            color: "var(--status-active-text)",
          }}
        >
          Order placed. We'll start your deliveries on the next press cycle.
        </div>
      )}

      {state.status === "loading" && (
        <div style={{ color: "var(--text-muted)" }}>Loading…</div>
      )}

      {state.status === "error" && (
        <div
          className="border-l-2 pl-4 py-2"
          style={{
            borderColor: "var(--status-error)",
            color: "var(--status-error)",
          }}
        >
          {state.message}
        </div>
      )}

      {state.status === "ok" && state.data.length === 0 && (
        <div className="card p-8 max-w-reading">
          <p style={{ color: "var(--text-secondary)" }} className="mb-4">
            No orders yet.
          </p>
          <Link href="/products" className="btn btn-primary">
            Browse the menu
          </Link>
        </div>
      )}

      {state.status === "ok" && state.data.length > 0 && (
        <div className="space-y-3">
          {state.data.map((o) => {
            const tone = statusTone(o.status);
            return (
              <article key={o.id} className="card p-6">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-heading text-xl font-semibold mb-1">
                      {o.plan_name ?? "Subscription"}
                    </h3>
                    <p
                      className="text-xs font-mono tracking-widest uppercase"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {o.frequency_name ?? "—"} · {o.start_date ?? "—"}
                    </p>
                  </div>
                  <span
                    className="text-[10px] uppercase tracking-widest font-semibold px-2 py-1 rounded"
                    style={{ background: tone.bg, color: tone.text }}
                  >
                    {tone.label}
                  </span>
                </div>
                <div className="flex justify-between items-baseline">
                  <span
                    className="text-sm"
                    style={{ color: "var(--text-muted)" }}
                  >
                    Order {o.id.slice(0, 8)}
                  </span>
                  <span className="font-heading text-lg font-semibold">
                    {formatINR(o.price_per_delivery ?? null)}
                    <span
                      className="text-xs ml-1 font-normal"
                      style={{ color: "var(--text-muted)" }}
                    >
                      / delivery
                    </span>
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
