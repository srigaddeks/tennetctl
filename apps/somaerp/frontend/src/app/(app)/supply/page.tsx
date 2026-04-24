"use client";

import Link from "next/link";

const CARDS = [
  { href: "/supply/raw-materials", title: "Raw Materials", description: "Ingredients and packaging SKUs — categories, default unit, shelf life, lot tracking, target cost." },
  { href: "/supply/suppliers", title: "Suppliers", description: "Vendors and sources — wholesale markets, rythu bazaars, marketplaces. Location + payment terms + quality." },
];

export default function SupplyLandingPage() {
  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>Supply</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Raw materials and suppliers — the dependency for recipes, procurement runs, inventory movements, and QC checkpoints.
        </p>
      </div>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {CARDS.map((card) => (
          <li key={card.href}>
            <Link href={card.href} className="block h-full rounded border p-5 transition-colors" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", borderLeft: "3px solid transparent" }}
              onMouseEnter={(e) => { const el = e.currentTarget as HTMLElement; el.style.borderLeftColor = "var(--accent)"; el.style.backgroundColor = "var(--bg-table-hover)"; }}
              onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; el.style.borderLeftColor = "transparent"; el.style.backgroundColor = "var(--bg-card)"; }}>
              <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{card.title}</div>
              <div className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>{card.description}</div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
