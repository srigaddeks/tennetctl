"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { clearCart, setCartPlan } from "@/lib/cart";
import {
  getMe,
  getPlanBySlug,
  placeOrder,
  type SubscriptionPlan,
} from "@/lib/api";

type State =
  | { status: "loading" }
  | { status: "ok"; plan: SubscriptionPlan }
  | { status: "missing" }
  | { status: "error"; message: string };

function formatINR(amount: number | string | null | undefined): string {
  if (amount == null) return "—";
  const n = typeof amount === "string" ? parseFloat(amount) : amount;
  if (!Number.isFinite(n)) return "—";
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

export default function CheckoutPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const planSlug = sp?.get("plan") ?? "";

  const [state, setState] = useState<State>({ status: "loading" });
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+91");
  const [line1, setLine1] = useState("");
  const [city, setCity] = useState("Hyderabad");
  const [pincode, setPincode] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (planSlug) setCartPlan(planSlug);
  }, [planSlug]);

  useEffect(() => {
    void getMe().then((me) => {
      setSignedIn(me !== null);
      if (me?.user.display_name) setName(me.user.display_name);
    });
  }, []);

  useEffect(() => {
    if (!planSlug) {
      setState({ status: "missing" });
      return;
    }
    getPlanBySlug(planSlug)
      .then((plan) => {
        if (!plan) setState({ status: "missing" });
        else setState({ status: "ok", plan });
      })
      .catch((e: unknown) =>
        setState({
          status: "error",
          message: e instanceof Error ? e.message : "Could not load plan",
        }),
      );
  }, [planSlug]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (state.status !== "ok") return;
    setError(null);
    setSubmitting(true);
    try {
      await placeOrder({
        subscription_plan_id: state.plan.id,
        name: name.trim(),
        phone: phone.trim(),
        address_line1: line1.trim(),
        address_pincode: pincode.trim(),
        city: city.trim(),
        notes: notes.trim() || null,
      });
      clearCart();
      router.push("/orders?placed=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (state.status === "loading") {
    return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;
  }
  if (state.status === "missing") {
    return (
      <div className="max-w-reading">
        <h1 className="font-heading text-3xl font-bold mb-4">Pick a plan first</h1>
        <p style={{ color: "var(--text-secondary)" }} className="mb-6">
          Browse the subscription options to start a delivery.
        </p>
        <Link href="/products" className="btn btn-primary">
          See plans
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

  if (signedIn === false) {
    return (
      <div className="max-w-reading">
        <h1 className="font-heading text-3xl font-bold mb-4">Sign in to subscribe</h1>
        <p style={{ color: "var(--text-secondary)" }} className="mb-6">
          We'll send a quick code to your mobile to verify it's you.
        </p>
        <Link
          href={`/signin?next=${encodeURIComponent(
            `/checkout?plan=${planSlug}`,
          )}`}
          className="btn btn-primary"
        >
          Sign in →
        </Link>
      </div>
    );
  }

  const plan = state.plan;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-12">
      {/* Form */}
      <div>
        <p
          className="text-xs tracking-[0.2em] uppercase mb-3"
          style={{ color: "var(--text-muted)" }}
        >
          Checkout
        </p>
        <h1 className="font-heading text-4xl font-bold mb-8">
          Where should we deliver?
        </h1>
        <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
          <div>
            <label
              className="block text-xs tracking-[0.15em] uppercase mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Your name
            </label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label
              className="block text-xs tracking-[0.15em] uppercase mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Phone (E.164)
            </label>
            <input
              className="input"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>
          <div>
            <label
              className="block text-xs tracking-[0.15em] uppercase mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Delivery address
            </label>
            <input
              className="input mb-3"
              placeholder="Street + landmark"
              value={line1}
              onChange={(e) => setLine1(e.target.value)}
              required
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                className="input"
                placeholder="City"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />
              <input
                className="input"
                placeholder="Pincode"
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                required
              />
            </div>
          </div>
          <div>
            <label
              className="block text-xs tracking-[0.15em] uppercase mb-2"
              style={{ color: "var(--text-muted)" }}
            >
              Delivery notes (optional)
            </label>
            <textarea
              className="input"
              rows={3}
              placeholder="Buzzer? Gate code? Building name?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
          {error && (
            <p className="text-sm" style={{ color: "var(--status-error)" }}>
              {error}
            </p>
          )}
          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={submitting}
          >
            {submitting ? "Placing order…" : "Place order →"}
          </button>
        </form>
      </div>

      {/* Order summary */}
      <aside>
        <div className="card p-6 sticky top-6">
          <p
            className="text-xs tracking-[0.15em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Your subscription
          </p>
          <h3 className="font-heading text-2xl font-bold mb-2">{plan.name}</h3>
          <p
            className="font-mono text-xs uppercase tracking-widest mb-4"
            style={{ color: "var(--text-muted)" }}
          >
            {plan.frequency_name ?? plan.frequency_code ?? "—"}
          </p>
          {plan.description && (
            <p
              className="text-sm leading-relaxed mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              {plan.description}
            </p>
          )}
          <div
            className="border-t pt-4 flex justify-between items-baseline"
            style={{ borderColor: "var(--border)" }}
          >
            <span className="text-sm" style={{ color: "var(--text-muted)" }}>
              Per delivery
            </span>
            <span className="font-heading text-2xl font-bold">
              {formatINR(plan.price_per_delivery ?? null)}
            </span>
          </div>
        </div>
      </aside>
    </div>
  );
}
