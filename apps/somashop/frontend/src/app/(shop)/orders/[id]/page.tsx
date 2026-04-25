"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getMyOrder, type OrderDetail } from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; data: OrderDetail }
  | { status: "missing" }
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
  if (s.includes("cancel")) return { label: "Cancelled", bg: "var(--status-error-bg)", text: "var(--status-error-text)" };
  return { label: status, bg: "var(--status-draft-bg)", text: "var(--status-draft-text)" };
}

export default function OrderDetailPage() {
  const params = useParams();
  const id = (params?.id as string) ?? "";
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    if (!id) return;
    getMyOrder(id)
      .then((data) => setState({ status: "ok", data }))
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : "Could not load order";
        if (msg.toLowerCase().includes("not found") || msg.includes("404")) {
          setState({ status: "missing" });
        } else {
          setState({ status: "error", message: msg });
        }
      });
  }, [id]);

  if (state.status === "loading") {
    return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;
  }
  if (state.status === "missing") {
    return (
      <div className="max-w-reading">
        <h1 className="font-heading text-3xl font-bold mb-4">Order not found</h1>
        <p style={{ color: "var(--text-secondary)" }} className="mb-6">
          We don't see an order under that ID for your account.
        </p>
        <Link href="/orders" className="btn btn-primary">
          Back to your orders
        </Link>
      </div>
    );
  }
  if (state.status === "error") {
    return (
      <div
        className="border-l-2 pl-4 py-2"
        style={{
          borderColor: "var(--status-error)",
          color: "var(--status-error)",
        }}
      >
        {state.message}
      </div>
    );
  }

  const o = state.data;
  const tone = statusTone(o.status);
  return (
    <div className="max-w-reading">
      <Link
        href="/orders"
        className="text-xs tracking-[0.15em] uppercase mb-8 inline-block"
        style={{ color: "var(--text-muted)" }}
      >
        ← Back to orders
      </Link>

      <p
        className="text-xs tracking-[0.2em] uppercase mb-3"
        style={{ color: "var(--text-muted)" }}
      >
        Subscription
      </p>
      <div className="flex flex-wrap items-baseline justify-between gap-4 mb-8">
        <h1 className="font-heading text-4xl font-bold">
          {o.plan_name ?? "Order"}
        </h1>
        <span
          className="text-[11px] uppercase tracking-widest font-semibold px-2 py-1 rounded"
          style={{ background: tone.bg, color: tone.text }}
        >
          {tone.label}
        </span>
      </div>

      <dl
        className="border-t border-b py-6 grid grid-cols-1 sm:grid-cols-2 gap-y-5 gap-x-8 mb-8"
        style={{ borderColor: "var(--border)" }}
      >
        <div>
          <dt
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Cadence
          </dt>
          <dd>{o.frequency_name ?? "—"}</dd>
        </div>
        <div>
          <dt
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Per delivery
          </dt>
          <dd className="font-heading text-lg font-semibold">
            {formatINR(o.price_per_delivery ?? null)}
          </dd>
        </div>
        <div>
          <dt
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Started
          </dt>
          <dd>{o.start_date ?? "—"}</dd>
        </div>
        <div>
          <dt
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Service zone
          </dt>
          <dd>{o.service_zone_name ?? "Hyderabad — auto-assigned"}</dd>
        </div>
        {o.paused_from && (
          <div className="sm:col-span-2">
            <dt
              className="text-xs tracking-[0.15em] uppercase mb-1"
              style={{ color: "var(--text-muted)" }}
            >
              Paused
            </dt>
            <dd>
              {o.paused_from} → {o.paused_to ?? "indefinite"}
            </dd>
          </div>
        )}
      </dl>

      <section className="card p-6 mb-8">
        <h3 className="font-heading text-lg font-semibold mb-3">
          Delivery cadence
        </h3>
        <p
          className="text-sm leading-relaxed mb-3"
          style={{ color: "var(--text-secondary)" }}
        >
          We press and bottle each delivery the same morning it arrives. Your
          first delivery starts on{" "}
          <span className="font-mono" style={{ color: "var(--text-primary)" }}>
            {o.start_date ?? "—"}
          </span>
          .
        </p>
        <p
          className="text-sm leading-relaxed"
          style={{ color: "var(--text-muted)" }}
        >
          Need to skip a day, change the address, or pause the subscription?
          Reply to your last delivery confirmation message — we'll handle it.
          Self-serve subscription editing is coming.
        </p>
      </section>

      <p
        className="text-xs"
        style={{ color: "var(--text-muted)" }}
      >
        Order ID:{" "}
        <span className="font-mono" style={{ color: "var(--text-secondary)" }}>
          {o.id}
        </span>
      </p>
    </div>
  );
}
