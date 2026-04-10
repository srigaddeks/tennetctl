'use client'

import { useState } from 'react'
import { Sidebar, MobileTopbar, MobileSidebar } from './nav'

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--background)', color: 'var(--foreground)' }}>
      {/* Desktop sidebar — hidden on mobile via media query workaround */}
      <div className="desktop-sidebar">
        <Sidebar />
      </div>

      {/* Mobile drawer */}
      <div className="mobile-only">
        <MobileTopbar open={mobileOpen} onToggle={() => setMobileOpen(!mobileOpen)} />
      </div>
      <MobileSidebar open={mobileOpen} onClose={() => setMobileOpen(false)} />

      {/* Main content */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <main style={{ flex: 1, maxWidth: 1100, width: '100%', margin: '0 auto', padding: '32px 32px 64px' }}>
          {children}
        </main>
        <footer style={{
          borderTop: '1px solid var(--border)',
          padding: '16px 32px',
          textAlign: 'center',
          color: 'var(--foreground-subtle)',
          fontSize: 11,
        }}>
          kbio Behavioral Biometrics SDK Demo &mdash; K-Protect by Kreesalis
        </footer>
      </div>

      {/* Responsive CSS — inline since we don't have Tailwind in demo */}
      <style>{`
        .desktop-sidebar { display: flex; }
        .mobile-only { display: none; }
        @media (max-width: 768px) {
          .desktop-sidebar { display: none !important; }
          .mobile-only { display: block; }
        }
      `}</style>
    </div>
  )
}
