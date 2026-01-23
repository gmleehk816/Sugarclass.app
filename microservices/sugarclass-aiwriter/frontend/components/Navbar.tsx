'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Menu, X, Home, Newspaper, Sparkles, ChevronDown, Zap } from 'lucide-react'
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
                        <motion.div
                            className="flex items-center gap-2 md:gap-3"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                        >
                            <motion.div
                                className="w-9 h-9 md:w-10 md:h-10 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center shadow-md hover:shadow-lg transition-shadow"
                                whileHover={{ scale: 1.05, rotate: 5 }}
                            >
                                <BookOpen className="w-5 h-5 md:w-6 md:h-6 text-white" />
                            </motion.div>
                            <div className="flex flex-col">
                                <span className="text-lg md:text-xl font-heading font-bold text-text-primary leading-tight">
                                    NewsCollect
                                </span>
                                <span className="text-xs md:text-sm font-semibold text-primary">
                                    Kids
                                </span>
                            </div>
                        </motion.div>

                        {/* Desktop Navigation */}
                        <div className="hidden md:flex items-center gap-1">
                            {navItems.map((item, index) => {
                                const Icon = item.icon
                                const isActive = pathname === item.href
                                return (
                                    <Link key={item.href} href={item.href}>
                                        <motion.button
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            whileHover={{ y: -2 }}
                                            whileTap={{ y: 0 }}
                                            className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all ${
                                                isActive
                                                    ? 'bg-primary/10 text-primary'
                                                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-dark'
                                            }`}
                                        >
                                            <Icon className="w-4 h-4" />
                                            {item.label}
                                        </motion.button>
                                    </Link>
                                )
                            })}
                        </div>

                        {/* Desktop CTA */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="hidden md:block"
                        >
                            <Link href="/news">
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    className="px-6 py-2.5 bg-gradient-to-r from-primary to-primary-dark text-white rounded-xl font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center gap-2"
                                >
                                    <Zap className="w-4 h-4" />
                                    Start Writing
                                </motion.button>
                            </Link>
                        </motion.div>

                        {/* Mobile Menu Button */}
                        <motion.button
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="md:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-surface-dark hover:bg-surface-darker transition-colors"
                        >
                            <AnimatePresence mode="wait">
                                {isMenuOpen ? (
                                    <motion.div
                                        key="close"
                                        initial={{ rotate: -90, opacity: 0 }}
                                        animate={{ rotate: 0, opacity: 1 }}
                                        exit={{ rotate: 90, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                    >
                                        <X className="w-6 h-6 text-text-primary" />
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="menu"
                                        initial={{ rotate: 90, opacity: 0 }}
                                        animate={{ rotate: 0, opacity: 1 }}
                                        exit={{ rotate: -90, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                    >
                                        <Menu className="w-6 h-6 text-text-primary" />
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.button>
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMenuOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsMenuOpen(false)}
                            className="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"
                        />
                        
                        {/* Mobile Menu Panel */}
                        <motion.div
                            variants={mobileMenuVariants}
                            initial="closed"
                            animate="open"
                            exit="closed"
                            className="fixed right-0 top-0 h-full w-80 max-w-[85vw] bg-surface z-50 md:hidden shadow-2xl"
                        >
                            <div className="flex flex-col h-full">
                                {/* Menu Header */}
                                <div className="flex items-center justify-between p-6 border-b border-border">
                                    <div className="flex items-center gap-2">
                                        <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center">
                                            <BookOpen className="w-6 h-6 text-white" />
                                        </div>
                                        <span className="text-xl font-heading font-bold text-text-primary">
                                            Menu
                                        </span>
                                    </div>
                                    <motion.button
                                        whileTap={{ scale: 0.9 }}
                                        onClick={() => setIsMenuOpen(false)}
                                        className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-dark transition-colors"
                                    >
                                        <X className="w-5 h-5 text-text-secondary" />
                                    </motion.button>
                                </div>

                                {/* Menu Items */}
                                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                                    {navItems.map((item) => {
                                        const Icon = item.icon
                                        const isActive = pathname === item.href
                                        return (
                                            <Link key={item.href} href={item.href} onClick={() => setIsMenuOpen(false)}>
                                                <motion.button
                                                    variants={itemVariants}
                                                    whileHover={{ x: 5 }}
                                                    whileTap={{ scale: 0.98 }}
                                                    className={`w-full px-4 py-3 rounded-xl font-medium text-left flex items-center gap-3 transition-all ${
                                                        isActive
                                                            ? 'bg-gradient-to-r from-primary/10 to-accent/10 text-primary'
                                                            : 'text-text-secondary hover:bg-surface-dark hover:text-text-primary'
                                                    }`}
                                                >
                                                    <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : 'text-text-muted'}`} />
                                                    {item.label}
                                                    {isActive && (
                                                        <motion.div
                                                            layoutId="activeIndicator"
                                                            className="ml-auto w-1.5 h-1.5 bg-primary rounded-full"
                                                        />
                                                    )}
                                                </motion.button>
                                            </Link>
                                        )
                                    })}
                                </div>

                                {/* Menu Footer */}
                                <div className="p-4 border-t border-border">
                                    <Link href="/news" onClick={() => setIsMenuOpen(false)}>
                                        <motion.button
                                            variants={itemVariants}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            className="w-full px-6 py-4 bg-gradient-to-r from-primary to-primary-dark text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
                                        >
                                            <Zap className="w-5 h-5" />
                                            Start Writing Now
                                        </motion.button>
                                    </Link>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    )
}
