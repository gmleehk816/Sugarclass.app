'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Menu, X, Home, Newspaper, Sparkles, ChevronDown, FileText } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const [scrolled, setScrolled] = useState(false)
    const pathname = usePathname()

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    const navItems = [
        { href: '/', label: 'Home', icon: Home },
        { href: '/news', label: 'News Stories', icon: Newspaper },
        { href: '/my-writings', label: 'My Writings', icon: FileText },
    ]

    const mobileMenuVariants = {
        closed: {
            opacity: 0,
            x: '100%'
        },
        open: {
            opacity: 1,
            x: 0
        }
    }

    const itemVariants = {
        closed: { opacity: 0, x: 50 },
        open: { opacity: 1, x: 0 }
    }

    return (
        <>
            {/* Desktop & Tablet Navbar */}
            <nav className={`sticky top-0 z-50 transition-all duration-300 ${
                scrolled 
                    ? 'bg-surface/95 backdrop-blur-md shadow-lg border-b border-border-light' 
                    : 'bg-surface/95 backdrop-blur-sm border-b border-border/50'
            }`}>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16 md:h-20">
                        {/* Logo */}
                        <div className="flex items-center gap-2 md:gap-3">
                            <div className="w-9 h-9 md:w-10 md:h-10 bg-gradient-to-br from-accent to-accent-light rounded-xl flex items-center justify-center shadow-md hover:shadow-lg transition-all hover:scale-105 cursor-pointer">
                                <BookOpen className="w-5 h-5 md:w-6 md:h-6 text-white" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-lg md:text-xl font-heading font-bold text-text-primary leading-tight">
                                    NewsCollect
                                </span>
                                <span className="text-xs md:text-sm font-semibold text-accent">
                                    Kids
                                </span>
                            </div>
                        </div>

                        {/* Desktop Navigation */}
                        <div className="hidden md:flex items-center gap-1">
                            {navItems.map((item) => {
                                const Icon = item.icon
                                const isActive = pathname === item.href
                                return (
                                    <Link key={item.href} href={item.href}>
                                        <button
                                            className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all ${
                                                isActive
                                                    ? 'bg-accent/10 text-accent'
                                                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-dark'
                                            }`}
                                        >
                                            <Icon className="w-4 h-4" />
                                            {item.label}
                                        </button>
                                    </Link>
                                )
                            })}
                        </div>


                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="md:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-surface-dark hover:bg-surface-darker transition-colors"
                        >
                            {isMenuOpen ? (
                                <X className="w-6 h-6 text-text-primary" />
                            ) : (
                                <Menu className="w-6 h-6 text-text-primary" />
                            )}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            {isMenuOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        onClick={() => setIsMenuOpen(false)}
                        className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
                    />

                    {/* Mobile Menu Panel */}
                    <div className="fixed right-0 top-0 h-full w-80 max-w-[85vw] bg-surface z-50 md:hidden shadow-2xl">
                        <div className="flex flex-col h-full">
                            {/* Menu Header */}
                            <div className="flex items-center justify-between p-6 border-b border-border">
                                <div className="flex items-center gap-2">
                                    <div className="w-10 h-10 bg-gradient-to-br from-accent to-accent-light rounded-xl flex items-center justify-center">
                                        <BookOpen className="w-6 h-6 text-white" />
                                    </div>
                                    <span className="text-xl font-heading font-bold text-text-primary">
                                        Menu
                                    </span>
                                </div>
                                <button
                                    onClick={() => setIsMenuOpen(false)}
                                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-dark transition-colors"
                                >
                                    <X className="w-5 h-5 text-text-secondary" />
                                </button>
                            </div>

                            {/* Menu Items */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-2">
                                {navItems.map((item) => {
                                    const Icon = item.icon
                                    const isActive = pathname === item.href
                                    return (
                                        <Link key={item.href} href={item.href} onClick={() => setIsMenuOpen(false)}>
                                            <button
                                                className={`w-full px-4 py-3 rounded-xl font-medium text-left flex items-center gap-3 transition-all hover:x-5 ${
                                                    isActive
                                                        ? 'bg-gradient-to-r from-accent/10 to-accent/20 text-accent'
                                                        : 'text-text-secondary hover:bg-surface-dark hover:text-text-primary'
                                                }`}
                                            >
                                                <Icon className={`w-5 h-5 ${isActive ? 'text-accent' : 'text-text-muted'}`} />
                                                {item.label}
                                                {isActive && (
                                                    <div className="ml-auto w-1.5 h-1.5 bg-accent rounded-full" />
                                                )}
                                            </button>
                                        </Link>
                                    )
                                })}
                            </div>

                        </div>
                    </div>
                </>
            )}
        </>
    )
}
