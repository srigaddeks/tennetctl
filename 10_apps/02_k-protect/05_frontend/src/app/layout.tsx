import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/components/auth-provider'
import { RouteGuard } from '@/components/route-guard'

export const metadata: Metadata = {
  title: 'KProtect — Policy Intelligence Dashboard',
  description: 'Behavioral biometrics policy management and threat intelligence',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <RouteGuard>{children}</RouteGuard>
        </AuthProvider>
      </body>
    </html>
  )
}
