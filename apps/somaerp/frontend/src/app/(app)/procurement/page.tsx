"use client";

import Link from "next/link";

export default function ProcurementLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Procurement</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Record shopping trips and compute BOM-explosion plans for upcoming
          demand.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <li>
          <Link
            href="/procurement/runs"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Procurement Runs</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Record shopping trips — header plus line items with lot numbers
              and quality grades. Emits received inventory movements.
            </div>
          </Link>
        </li>
        <li>
          <Link
            href="/procurement/planner"
            className="block rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
          >
            <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>MRP Planner</div>
            <div className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Plan raw materials needed for any upcoming day. Explodes active
              recipes, subtracts stock, and estimates cost from primary
              suppliers.
            </div>
          </Link>
        </li>
      </ul>
    </div>
  );
}
