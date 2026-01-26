import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'
import Breadcrumbs from '@/components/Breadcrumbs'

export const metadata: Metadata = {
    title: 'Sugarclass AI Writer - Learn & Write News Stories',
    description: 'A fun and supportive platform for kids ages 8-15 to read and write news articles with AI assistance',
}

import SessionHandler from '@/components/SessionHandler'

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" data-scroll-behavior="smooth">
            <body>
                <SessionHandler />
                <Navbar />
                <Breadcrumbs />
                {children}
            </body>
        </html>
    )
}
