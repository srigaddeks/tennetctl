import { Nav } from './nav'

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--background)' }}>
      <Nav />
      <main style={{ flex: 1, minWidth: 0, padding: '28px 32px', overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  )
}
