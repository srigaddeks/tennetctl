"use client";

import Link from "next/link";

const CARDS = [
  { href: "/catalog/product-lines", title: "Product Lines", description: "Top-level product families grouped by category (beverage, shot, pulp). Every product rolls up to a line." },
  { href: "/catalog/products", title: "Products", description: "SKUs within a product line. Carry default serving, shelf life, COGS, price, currency, and wellness tags." },
];

export default function CatalogLandingPage() {
  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>Catalog</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Product lines and SKUs — the dependency for recipes, production batches, subscriptions, and kitchen capacity planning.
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
