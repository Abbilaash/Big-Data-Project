import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Navbar } from '@/components/navbar'

export const metadata: Metadata = {
  title: 'CampusConnect — Student Events & Networking',
  description:
    'CampusConnect helps students discover campus events, find teammates, and connect with fellow students.',
  generator: 'v0.app',
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
  colorScheme: 'light',
  themeColor: '#ffffff',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
