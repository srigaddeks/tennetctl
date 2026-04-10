import type { Metadata } from 'next'
import './globals.css'
import { SdkProvider } from '@/components/sdk-provider'
import { AuthProvider } from '@/components/auth-provider'
import { RouteGuard } from '@/components/route-guard'

export const metadata: Metadata = {
  title: 'kbio Demo — Behavioral Biometrics SDK',
  description: 'Live demonstration of kbio behavioral biometrics scoring engine',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SdkProvider>
          <AuthProvider>
            <RouteGuard>{children}</RouteGuard>
          </AuthProvider>
        </SdkProvider>
      </body>
    </html>
  )
}
