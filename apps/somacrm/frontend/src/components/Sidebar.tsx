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
  dashboard: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/>
      <rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/>
      <rect x="3" y="14" width="7" height="7"/>
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
  building: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/>
      <path d="M9 22V12h6v10"/>
      <path d="M3 9h18"/>
      <path d="M3 15h18"/>
    </svg>
  ),
  target: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
    </svg>
  ),
  barChart: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  dollar: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23"/>
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
    </svg>
  ),
  calendar: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
  ),
  pieChart: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>
      <path d="M22 12A10 10 0 0 0 12 2v10z"/>
    </svg>
  ),
};

const NAV_SECTIONS: NavSection[] = [
  {
    title: "OVERVIEW",
    items: [
      { href: "/", label: "Dashboard", icon: icons.dashboard },
    ],
  },
  {
    title: "PEOPLE",
    items: [
      { href: "/contacts", label: "Contacts", icon: icons.users },
      { href: "/organizations", label: "Organizations", icon: icons.building },
    ],
  },
  {
    title: "SALES",
    items: [
      { href: "/leads", label: "Leads", icon: icons.target },
      { href: "/pipeline", label: "Pipeline", icon: icons.barChart },
      { href: "/deals", label: "Deals", icon: icons.dollar },
    ],
  },
  {
    title: "ACTIVITY",
    items: [
      { href: "/activities", label: "Activities", icon: icons.calendar },
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      { href: "/reports", label: "Reports", icon: icons.pieChart },
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
            somacrm
          </div>
          <div className="text-xs mt-0.5" style={{ color: "var(--text-sidebar-muted)", fontFamily: "var(--font-ui)" }}>
            CRM Platform
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
