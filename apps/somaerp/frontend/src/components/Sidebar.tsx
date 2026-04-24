"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  href: string;
  label: string;
  icon: React.ReactNode;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

// Inline SVG icons — no icon library dependency
const icons = {
  mapPin: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
      <circle cx="12" cy="10" r="3"/>
    </svg>
  ),
  tag: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
      <line x1="7" y1="7" x2="7.01" y2="7"/>
    </svg>
  ),
  truck: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="3" width="15" height="13"/>
      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
      <circle cx="5.5" cy="18.5" r="2.5"/>
      <circle cx="18.5" cy="18.5" r="2.5"/>
    </svg>
  ),
  flask: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 3h6M9 3v8l-4.5 7.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-3L15 11V3"/>
    </svg>
  ),
  wrench: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>
  ),
  checkCircle: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  ),
  cart: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="21" r="1"/>
      <circle cx="20" cy="21" r="1"/>
      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
    </svg>
  ),
  box: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
      <line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>
  ),
  cog: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/>
    </svg>
  ),
  users: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  repeat: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="17 1 21 5 17 9"/>
      <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
      <polyline points="7 23 3 19 7 15"/>
      <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
    </svg>
  ),
  package: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/>
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
      <line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>
  ),
  barChart: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
};

const NAV_SECTIONS: NavSection[] = [
  {
    title: "OPERATIONS",
    items: [
      { href: "/geography", label: "Geography", icon: icons.mapPin },
      { href: "/catalog", label: "Catalog", icon: icons.tag },
      { href: "/supply", label: "Supply", icon: icons.truck },
    ],
  },
  {
    title: "PRODUCTION",
    items: [
      { href: "/recipes", label: "Recipes", icon: icons.flask },
      { href: "/equipment", label: "Equipment", icon: icons.wrench },
      { href: "/quality", label: "Quality", icon: icons.checkCircle },
      { href: "/procurement", label: "Procurement", icon: icons.cart },
      { href: "/inventory", label: "Inventory", icon: icons.box },
      { href: "/production", label: "Production", icon: icons.cog },
    ],
  },
  {
    title: "COMMERCE",
    items: [
      { href: "/customers", label: "Customers", icon: icons.users },
      { href: "/subscriptions", label: "Subscriptions", icon: icons.repeat },
      { href: "/delivery", label: "Delivery", icon: icons.package },
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      { href: "/reports", label: "Reports", icon: icons.barChart },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  function isActive(href: string): boolean {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <aside
      className="fixed left-0 top-0 flex h-screen flex-col overflow-y-auto"
      style={{
        width: "var(--sidebar-width)",
        backgroundColor: "var(--bg-sidebar)",
        borderRight: "1px solid #1F2937",
        fontFamily: "var(--font-ui)",
      }}
    >
      {/* Logo */}
      <div className="flex-shrink-0 px-4 py-4" style={{ borderBottom: "1px solid #1F2937" }}>
        <Link href="/" className="block">
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 500, color: "var(--text-sidebar)", letterSpacing: "-0.01em" }}>
            somaerp
          </div>
          <div className="text-xs mt-0.5" style={{ color: "var(--text-sidebar-muted)", fontFamily: "var(--font-ui)" }}>
            ERP Platform
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-4">
            <div
              className="px-4 py-1"
              style={{
                color: "var(--text-sidebar-muted)",
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.1em",
                textTransform: "uppercase" as const,
                fontFamily: "var(--font-ui)",
              }}
            >
              {section.title}
            </div>
            <ul>
              {section.items.map((item) => {
                const active = isActive(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="flex items-center gap-2.5 px-4 py-2 text-sm font-medium transition-colors"
                      style={{
                        fontFamily: "var(--font-ui)",
                        color: active ? "#FFFFFF" : "var(--text-sidebar-muted)",
                        backgroundColor: active
                          ? "var(--bg-sidebar-active)"
                          : "transparent",
                      }}
                      onMouseEnter={(e) => {
                        if (!active) {
                          (e.currentTarget as HTMLElement).style.backgroundColor =
                            "var(--bg-sidebar-hover)";
                          (e.currentTarget as HTMLElement).style.color =
                            "var(--text-sidebar)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!active) {
                          (e.currentTarget as HTMLElement).style.backgroundColor =
                            "transparent";
                          (e.currentTarget as HTMLElement).style.color =
                            "var(--text-sidebar-muted)";
                        }
                      }}
                    >
                      <span className="flex-shrink-0 opacity-80">{item.icon}</span>
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer version badge */}
      <div
        className="flex-shrink-0 px-4 py-3"
        style={{ borderTop: "1px solid #1F2937" }}
      >
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            borderRadius: 4,
            padding: "2px 8px",
            fontFamily: "var(--font-mono)",
            fontSize: 10,
            backgroundColor: "#1F2937",
            color: "var(--text-sidebar-muted)",
            letterSpacing: "0.04em",
          }}
        >
          tennetctl v0.9.0
        </span>
      </div>
    </aside>
  );
}
