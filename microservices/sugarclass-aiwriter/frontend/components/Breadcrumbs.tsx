'use client'

import { ChevronRight, Home } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface BreadcrumbItem {
    label: string
    href: string
    icon?: React.ComponentType<{ className?: string }>
}

export default function Breadcrumbs() {
    const pathname = usePathname()

    // Generate breadcrumbs based on current path
    const generateBreadcrumbs = (): BreadcrumbItem[] => {
        const items: BreadcrumbItem[] = []
        const segments = pathname.split('/').filter(Boolean)

        // Always add Home
        items.push({
            label: 'Home',
            href: '/',
            icon: Home
        })

        // Add dynamic breadcrumbs
        segments.forEach((segment, index) => {
            const href = `/${segments.slice(0, index + 1).join('/')}`
            let label = segment

            // Format labels
            if (segment === 'news') {
                label = 'News Stories'
            } else if (segment === 'write') {
                label = 'AI Writing'
            } else if (segment.match(/^\d+$/)) {
                // If it's a numeric ID, keep it as is
                label = `Article ${segment}`
            } else {
                // Capitalize first letter and replace hyphens with spaces
                label = segment
                    .split('-')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ')
            }

            items.push({ label, href })
        })

        return items
    }

    const breadcrumbs = generateBreadcrumbs()

    // Don't show breadcrumbs on home page
    if (pathname === '/') {
        return null
    }

    return (
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <nav className="flex items-center space-x-1 sm:space-x-2 overflow-x-auto no-scrollbar" aria-label="Breadcrumb">
                {breadcrumbs.map((item, index) => {
                    const Icon = item.icon
                    const isLast = index === breadcrumbs.length - 1

                    return (
                        <div key={item.href} className="flex items-center">
                            {index > 0 && (
                                <ChevronRight className="w-4 h-4 text-text-muted flex-shrink-0" />
                            )}

                            {isLast ? (
                                <span className="px-3 py-1.5 bg-accent/10 text-accent rounded-lg font-medium text-sm whitespace-nowrap">
                                    {Icon && <Icon className="w-4 h-4 inline mr-1" />}
                                    {item.label}
                                </span>
                            ) : (
                                <Link
                                    href={item.href}
                                    className="px-3 py-1.5 hover:bg-surface-dark text-text-secondary hover:text-accent rounded-lg font-medium text-sm transition-all whitespace-nowrap flex items-center gap-1 group"
                                >
                                    {Icon && (
                                        <Icon className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors" />
                                    )}
                                    {item.label}
                                </Link>
                            )}
                        </div>
                    )
                })}
            </nav>
        </div>
    )
}
