'use client'

import { motion } from 'framer-motion'
import { BookOpen, Sparkles, Newspaper, TrendingUp, Brain, Rocket, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'
import { useState, useEffect } from 'react'
import { getArticles, Article } from '@/lib/api'

export default function Home() {
    const [recentArticles, setRecentArticles] = useState<Article[]>([])

    useEffect(() => {
        async function fetchRecentArticles() {
            try {
                const articles = await getArticles({ limit: 6 })
                setRecentArticles(articles)
            } catch (err) {
                console.error('Failed to load articles:', err)
            }
        }
        fetchRecentArticles()
    }, [])

    const features = [
        {
            icon: Newspaper,
            title: 'Read Real News',
            description: 'Discover fascinating stories from around the world, curated for young readers',
            color: 'text-primary',
            bgColor: 'bg-primary/5'
        },
        {
            icon: Brain,
            title: 'AI Writing Coach',
            description: 'Get personalized guidance and suggestions to improve your writing',
            color: 'text-accent',
            bgColor: 'bg-accent/5'
        },
        {
            icon: Sparkles,
            title: 'Improve Your Skills',
            description: 'Build vocabulary, grammar, and confidence with every article',
            color: 'text-success',
            bgColor: 'bg-success/5'
        },
        {
            icon: TrendingUp,
            title: 'Track Progress',
            description: 'Watch your word count grow and celebrate every milestone',
            color: 'text-warning',
            bgColor: 'bg-warning/5'
        }
    ]

    const benefits = [
        'Age-appropriate content (7-18 years)',
        'Guided writing practice',
        'Real-time AI feedback',
        'Safe & parent-approved',
        'Build critical thinking',
        'Boost confidence'
    ]

    return (
        <main className="min-h-screen bg-background pt-4">
            {/* Hero Section */}
            <section className="relative overflow-hidden bg-gradient-to-b from-surface to-surface-dark py-24">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                        {/* Left Column - Text Content */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6 }}
                        >
                            <div className="inline-block px-4 py-1.5 bg-primary/10 rounded-full mb-6">
                                <span className="text-primary text-sm font-semibold">✨ AI-Powered Learning Platform</span>
                            </div>
                            <h1 className="text-5xl md:text-6xl font-heading font-bold text-text-primary mb-6 leading-tight">
                                Read. Write.{' '}
                                <span className="text-primary">Grow.</span>
                            </h1>
                            <p className="text-xl text-text-secondary mb-8 leading-relaxed">
                                NewsCollect helps young writers ages 8-15 build confidence through real news and AI-powered guidance.
                            </p>

                            <div className="flex flex-col sm:flex-row gap-4 mb-8">
                                <Link href="/news">
                                    <button className="px-8 py-4 bg-primary text-surface rounded-lg font-bold text-lg hover:bg-primary-dark transition-colors shadow-md hover:shadow-lg flex items-center gap-2 justify-center">
                                        <Rocket className="w-5 h-5" />
                                        Start Writing Now
                                    </button>
                                </Link>
                                <a href="#how-it-works">
                                    <button className="px-8 py-4 bg-surface border-2 border-border text-text-primary rounded-lg font-semibold text-lg hover:border-primary hover:text-primary transition-colors">
                                        See How It Works
                                    </button>
                                </a>
                            </div>

                            {/* Quick Benefits */}
                            <div className="grid grid-cols-2 gap-4">
                                {benefits.slice(0, 4).map((benefit, idx) => (
                                    <motion.div
                                        key={benefit}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.3 + idx * 0.1 }}
                                        className="flex items-start gap-2"
                                    >
                                        <CheckCircle2 className="w-5 h-5 text-success mt-0.5 flex-shrink-0" />
                                        <span className="text-sm text-text-secondary">{benefit}</span>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>

                        {/* Right Column - Sample News Articles Grid */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                            className="relative"
                        >
                            <div className="grid grid-cols-2 gap-4">
                                {recentArticles.slice(0, 5).map((article, idx) => (
                                    <motion.div
                                        key={article.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.4 + idx * 0.1 }}
                                        className={`bg-surface rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-shadow ${idx === 0 ? 'col-span-2' : ''}`}
                                    >
                                        <div className={`relative ${idx === 0 ? 'h-48' : 'h-32'} overflow-hidden`}>
                                            {article.image_url ? (
                                                <img
                                                    src={article.image_url}
                                                    alt={article.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full bg-gradient-to-br from-primary/10 to-accent/10" />
                                            )}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                            <div className="absolute bottom-2 left-2 right-2">
                                                <p className="text-surface text-sm font-semibold line-clamp-2">
                                                    {article.title}
                                                </p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                            {recentArticles.length === 0 && (
                                <div className="grid grid-cols-2 gap-4">
                                    {[1, 2, 3, 4].map((i) => (
                                        <div
                                            key={i}
                                            className={`bg-surface-dark rounded-xl overflow-hidden animate-pulse ${i === 1 ? 'col-span-2 h-48' : 'h-32'}`}
                                        />
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="py-20 bg-surface-dark/50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-heading font-bold text-text-primary mb-4">
                            How NewsCollect Works
                        </h2>
                        <p className="text-lg text-text-secondary max-w-2xl mx-auto">
                            Three simple steps to become a confident writer
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Step 1 */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="text-center"
                        >
                            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                                <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
                                    <span className="text-2xl font-bold text-surface">1</span>
                                </div>
                            </div>
                            <div className="bg-surface rounded-xl p-6 shadow-sm border border-border-light">
                                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                                    <Newspaper className="w-6 h-6 text-primary" />
                                </div>
                                <h3 className="text-xl font-heading font-bold text-text-primary mb-3">
                                    Pick a News Story
                                </h3>
                                <p className="text-text-secondary text-sm leading-relaxed">
                                    Browse real news articles from trusted sources, filtered by age group (7-10, 11-14, 15-18) and topic
                                </p>
                            </div>
                        </motion.div>

                        {/* Step 2 */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="text-center"
                        >
                            <div className="w-20 h-20 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                                <div className="w-16 h-16 bg-accent rounded-full flex items-center justify-center">
                                    <span className="text-2xl font-bold text-surface">2</span>
                                </div>
                            </div>
                            <div className="bg-surface rounded-xl p-6 shadow-sm border border-border-light">
                                <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                                    <Brain className="w-6 h-6 text-accent" />
                                </div>
                                <h3 className="text-xl font-heading font-bold text-text-primary mb-3">
                                    Write with AI Help
                                </h3>
                                <p className="text-text-secondary text-sm leading-relaxed">
                                    Our AI coach gives you writing plans, suggests next paragraphs, and helps improve your grammar and style
                                </p>
                            </div>
                        </motion.div>

                        {/* Step 3 */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.3 }}
                            className="text-center"
                        >
                            <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                                <div className="w-16 h-16 bg-success rounded-full flex items-center justify-center">
                                    <span className="text-2xl font-bold text-surface">3</span>
                                </div>
                            </div>
                            <div className="bg-surface rounded-xl p-6 shadow-sm border border-border-light">
                                <div className="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                                    <TrendingUp className="w-6 h-6 text-success" />
                                </div>
                                <h3 className="text-xl font-heading font-bold text-text-primary mb-3">
                                    Track Your Progress
                                </h3>
                                <p className="text-text-secondary text-sm leading-relaxed">
                                    Watch your word count grow, hit milestones, and see your writing skills improve with every article
                                </p>
                            </div>
                        </motion.div>
                    </div>

                    {/* CTA */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: 0.4 }}
                        className="text-center mt-12"
                    >
                        <Link href="/news">
                            <button className="px-8 py-4 bg-primary text-surface rounded-lg font-bold text-lg hover:bg-primary-dark transition-colors shadow-md hover:shadow-lg inline-flex items-center gap-2">
                                <Sparkles className="w-5 h-5" />
                                Try It Now - It's Free!
                            </button>
                        </Link>
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-surface">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-heading font-bold text-text-primary mb-4">
                            Everything You Need to Succeed
                        </h2>
                        <p className="text-lg text-text-secondary max-w-2xl mx-auto">
                            Our platform combines real news with AI technology to help you become a confident writer
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {features.map((feature, index) => {
                            const Icon = feature.icon
                            return (
                                <motion.div
                                    key={feature.title}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ duration: 0.5, delay: index * 0.1 }}
                                    whileHover={{ y: -4 }}
                                    className="bg-surface-dark/50 rounded-xl p-6 hover:shadow-md transition-all cursor-pointer border border-border-light"
                                >
                                    <div className={`w-14 h-14 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                                        <Icon className={`w-7 h-7 ${feature.color}`} />
                                    </div>
                                    <h3 className="text-xl font-heading font-bold text-text-primary mb-2">
                                        {feature.title}
                                    </h3>
                                    <p className="text-text-secondary leading-relaxed text-sm">
                                        {feature.description}
                                    </p>
                                </motion.div>
                            )
                        })}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 bg-primary">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                    >
                        <h2 className="text-4xl font-heading font-bold text-surface mb-6">
                            Ready to Start Your Writing Journey?
                        </h2>
                        <p className="text-xl text-surface/90 mb-8">
                            Join young writers discovering the joy of storytelling with real news
                        </p>
                        <Link href="/news">
                            <button className="px-10 py-5 bg-surface text-primary rounded-lg font-bold text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-200 flex items-center gap-3 mx-auto">
                                <BookOpen className="w-6 h-6" />
                                Explore News Stories
                            </button>
                        </Link>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-surface-darker py-12 border-t border-border">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                    <BookOpen className="w-5 h-5 text-white" />
                                </div>
                                <span className="text-lg font-heading font-bold text-text-primary">
                                    NewsCollect Kids
                                </span>
                            </div>
                            <p className="text-text-secondary text-sm">
                                Building confident writers through real news and AI-powered learning.
                            </p>
                        </div>
                        <div>
                            <h4 className="font-semibold text-text-primary mb-3">Quick Links</h4>
                            <ul className="space-y-2 text-sm text-text-secondary">
                                <li><Link href="/news" className="hover:text-primary transition-colors">Browse News</Link></li>
                                <li><a href="#" className="hover:text-primary transition-colors">How It Works</a></li>
                                <li><a href="#" className="hover:text-primary transition-colors">For Parents</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-text-primary mb-3">Connect</h4>
                            <p className="text-text-secondary text-sm">
                                Have questions? We're here to help young writers succeed.
                            </p>
                        </div>
                    </div>
                    <div className="border-t border-border pt-6 text-center">
                        <p className="text-text-muted text-sm">
                            © 2025 NewsCollect Kids. Made with ❤️ for young writers everywhere.
                        </p>
                    </div>
                </div>
            </footer>
        </main>
    )
}
