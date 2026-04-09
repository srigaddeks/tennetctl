import type { Metadata } from 'next'
import './globals.css'
import { SdkProvider } from '@/components/sdk-provider'
import { Nav } from '@/components/nav'

export const metadata: Metadata = {
  title: 'kbio Demo - Behavioral Biometrics',
  description: 'Live demonstration of K-Protect behavioral biometrics SDK',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SdkProvider>
          <Nav />
          <main style={{ maxWidth: 1120, margin: '0 auto', padding: '28px 24px 64px' }}>
            {children}
          </main>
          <footer style={{
            borderTop: '1px solid var(--border)',
            padding: '20px 32px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: 11,
          }}>
            kbio Behavioral Biometrics SDK Demo &mdash; K-Protect by Kreesalis
          </footer>
        </SdkProvider>
      </body>
    </html>
  )
}
