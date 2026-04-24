"use client";

import Link from "next/link";

type Card = {
  href: string;
  title: string;
  blurb: string;
};

const cards: Card[] = [
  { href: "/reports/today", title: "Today's Dashboard", blurb: "KPI snapshot — active batches, deliveries in transit, completed runs, active subscriptions." },
  { href: "/reports/yield", title: "Yield & COGS Trends", blurb: "Daily/weekly/monthly yield percentage and COGS per unit with filters by kitchen and product." },
  { href: "/reports/inventory-alerts", title: "Inventory Alerts", blurb: "Critical and low-stock raw materials per kitchen. Jump-start a procurement run from any row." },
  { href: "/reports/procurement", title: "Procurement Spend", blurb: "Monthly procurement spend rolled up by kitchen and supplier with totals." },
  { href: "/reports/revenue", title: "Revenue Projection", blurb: "Projected monthly MRR per active subscription — price × deliveries_per_week × 4.333." },
  { href: "/reports/compliance", title: "FSSAI Compliance", blurb: "Per-batch lot numbers + QC results. Download a CSV filtered by date range." },
];

export default function ReportsLandingPage() {
  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Reports</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Cross-layer rollups over operations. Read-only views — no new data generated here.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((c) => (
          <li key={c.href}>
            <Link
              href={c.href}
              className="block rounded border p-5 transition-colors"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", borderLeft: "3px solid transparent" }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLElement;
                el.style.borderLeftColor = "var(--accent)";
                el.style.backgroundColor = "var(--bg-table-hover)";
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLElement;
                el.style.borderLeftColor = "transparent";
                el.style.backgroundColor = "var(--bg-card)";
              }}
            >
              <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{c.title}</div>
              <div className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>{c.blurb}</div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
