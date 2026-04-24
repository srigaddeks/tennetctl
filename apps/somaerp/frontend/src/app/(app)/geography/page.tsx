"use client";

import Link from "next/link";

type NavCard = {
  href: string;
  title: string;
  description: string;
};

const CARDS: NavCard[] = [
  {
    href: "/geography/locations",
    title: "Locations",
    description:
      "City-level sites. Every kitchen rolls up to a location; regions drive timezone and currency defaults.",
  },
  {
    href: "/geography/kitchens",
    title: "Kitchens",
    description:
      "Production facilities (home, commissary, satellite). State machine: active ↔ paused, * → decommissioned.",
  },
  {
    href: "/geography/service-zones",
    title: "Service Zones",
    description:
      "Delivery areas tied to a kitchen. Polygon or pincode-set; only active kitchens accept new zones.",
  },
];

export default function GeographyLandingPage() {
  return (
    <div className="max-w-4xl">
      <div className="mb-6">
        <h1
          className="text-2xl font-semibold tracking-tight"
          style={{ color: "var(--text-primary)" }}
        >
          Geography
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          The foundation layer every other module hangs off of — locations own
          kitchens, kitchens own service zones, production batches, procurement,
          and delivery routes.
        </p>
      </div>

      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((card) => (
          <li key={card.href}>
            <Link
              href={card.href}
              className="block h-full rounded border p-5 transition-colors"
              style={{
                backgroundColor: "var(--bg-card)",
                borderColor: "var(--border)",
                borderLeft: "3px solid transparent",
              }}
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
              <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {card.title}
              </div>
              <div className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                {card.description}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
