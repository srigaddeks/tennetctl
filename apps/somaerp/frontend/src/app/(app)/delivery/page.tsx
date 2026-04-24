"use client";

import Link from "next/link";

export default function DeliveryLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Delivery</h1>
        <p className="mt-2 ">
          Routes anchor a kitchen. Riders run them. Runs generate per-customer
          stops the rider marks delivered / missed on their phone.
        </p>
      </div>

      <nav className="grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          href="/delivery/routes"
          className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Routes</div>
          <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Named delivery routes + customer sequence
          </div>
        </Link>
        <Link
          href="/delivery/riders"
          className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Riders</div>
          <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Rider profiles + role taxonomy
          </div>
        </Link>
        <Link
          href="/delivery/runs"
          className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Today&apos;s Runs</div>
          <div className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
            Plan a run, generate stops, rider mobile UI
          </div>
        </Link>
        <Link
          href="/delivery/board"
          className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Board</div>
          <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Live: runs today, grouped by kitchen
          </div>
        </Link>
      </nav>
    </div>
  );
}
