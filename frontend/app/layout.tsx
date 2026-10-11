import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Navbar } from '@/components/navbar'
import { AuthProvider } from '@/lib/auth'
import { AuthGate } from '@/components/auth-gate'
import { ToastProvider } from '@/components/toast'

export const metadata: Metadata = {
  title: 'CampusConnect — Campus Events & Networking',
  description:
    'CampusConnect helps students discover campus events, see what their connections are attending, and build their network.',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'dark light',
  themeColor: '#12141f',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
        >
          Skip to content
        </a>
        <AuthProvider>
          <ToastProvider>
            <Navbar />
            <main id="main" className="mx-auto max-w-6xl px-4 py-8">
              <AuthGate>{children}</AuthGate>
            </main>
          </ToastProvider>
        </AuthProvider>
        {process.env.VERCEL === '1' && <Analytics />}
      </body>
    </html>
  )
}
