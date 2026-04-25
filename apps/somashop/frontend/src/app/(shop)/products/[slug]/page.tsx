"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getProductBySlug, type Product } from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; data: Product }
  | { status: "missing" }
  | { status: "error"; message: string };

function formatINR(amount: number | string | null | undefined): string {
  if (amount == null) return "—";
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  if (!Number.isFinite(n)) return "—";
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

export default function ProductDetailPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? "";
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    if (!slug) return;
    getProductBySlug(slug)
      .then((p) => {
        if (!p) setState({ status: "missing" });
        else setState({ status: "ok", data: p });
      })
      .catch((e: unknown) =>
        setState({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load",
        }),
      );
  }, [slug]);

  if (state.status === "loading") {
    return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;
  }
  if (state.status === "missing") {
    return (
      <div className="max-w-reading">
        <h1 className="font-heading text-3xl font-bold mb-4">Not found</h1>
        <p style={{ color: "var(--text-secondary)" }}>
          We don't have that product on the menu.{" "}
          <Link
            href="/products"
            className="underline"
            style={{ color: "var(--text-primary)" }}
          >
            See the full menu →
          </Link>
        </p>
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

  const p = state.data;

  return (
    <article className="max-w-reading">
      <Link
        href="/products"
        className="text-xs tracking-[0.15em] uppercase mb-8 inline-block"
        style={{ color: "var(--text-muted)" }}
      >
        ← Back to menu
      </Link>

      <p
        className="text-xs tracking-[0.2em] uppercase mb-3"
        style={{ color: "var(--text-muted)" }}
      >
        {p.product_line_name ?? "—"}
        {p.default_serving_size_ml
          ? ` · ${Math.round(Number(p.default_serving_size_ml))} ml`
          : ""}
      </p>

      <h1 className="font-heading text-5xl font-extrabold tracking-tight mb-6">
        {p.name}
      </h1>

      {p.target_benefit && (
        <blockquote className="pull-quote text-2xl mb-8 leading-relaxed">
          {p.target_benefit}
        </blockquote>
      )}

      {p.description && (
        <p
          className="text-lg leading-relaxed mb-12"
          style={{ color: "var(--text-secondary)" }}
        >
          {p.description}
        </p>
      )}

      <div
        className="border-t border-b py-6 my-8 flex justify-between items-center"
        style={{ borderColor: "var(--border)" }}
      >
        <div>
          <p
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Single bottle
          </p>
          <span className="font-heading text-3xl font-bold">
            {formatINR(p.default_selling_price ?? null)}
          </span>
        </div>
        <Link href="/products" className="btn btn-primary">
          See subscriptions
        </Link>
      </div>

      <div
        className="text-sm leading-relaxed"
        style={{ color: "var(--text-muted)" }}
      >
        Bottled the morning of delivery. 72-hour shelf life from press, kept
        cold throughout. No HPP, no preservatives, no concentrates — just
        whole produce.
      </div>
    </article>
  );
}
