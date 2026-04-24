"use client";

import Link from "next/link";

export default function InventoryLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Inventory</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Current stock per kitchen and an append-only feed of all inventory
          movements.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <li>
          <Link
            href="/inventory/current"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Current Stock</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Live per-(kitchen, raw material) quantities derived from
              append-only movement events.
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/inventory/movements"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Movements Feed</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Immutable event log: received, consumed, wasted, adjusted,
              expired — colour-coded with filters.
            </div>
          </Link>
        </li>
      </ul>
    </div>
  );
}
