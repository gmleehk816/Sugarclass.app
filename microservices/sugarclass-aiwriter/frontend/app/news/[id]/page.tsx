'use client'

import { motion } from 'framer-motion'
import { ArrowLeft, BookOpen, Clock, Printer, Sparkles } from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getArticle, Article } from '@/lib/api'

export default function ArticlePage() {
    const params = useParams()
    const articleId = parseInt(params.id as string)
    const [article, setArticle] = useState<Article | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        async function fetchArticle() {
            try {
                const data = await getArticle(articleId)
                setArticle(data)
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load article')
            } finally {
                setLoading(false)
            }
        }

        fetchArticle()
    }, [articleId])

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-sky-blue border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-text-secondary">Loading article...</p>
                </div>
            </div>
        )
    }

    if (error || !article) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-500 mb-4">{error || 'Article not found'}</p>
                    <Link href="/news">
                        <button className="px-6 py-2 bg-sky-blue text-white rounded-lg font-semibold">
                            Back to News Feed
                        </button>
                    </Link>
                </div>
            </div>
        )
    }

    const readingTime = article.word_count ? Math.ceil(article.word_count / 200) : 5
    const categoryColors: Record<string, string> = {
        Science: 'bg-science',
        Technology: 'bg-tech',
        Environment: 'bg-environment',
        Sports: 'bg-sports',
        Arts: 'bg-arts',
        Health: 'bg-health',
    }

    const handlePrint = () => {
        window.print()
    }

    return (
        <>
            <style jsx global>{`
                @media print {
                    .no-print {
                        display: none !important;
                    }
                    body {
                        background: white !important;
                    }
                    article {
                        max-width: 100% !important;
                        padding: 0 !important;
                    }
                }
            `}</style>
            <div className="min-h-screen bg-background pt-4">
                {/* Article Content */}
                <article className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Article Meta Bar */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between mb-6 no-print"
                >
                    <Link href="/news">
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="flex items-center gap-2 px-4 py-2 bg-surface rounded-lg border border-border hover:border-primary hover:text-primary transition-colors text-text-secondary"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-sm font-semibold">Back to Feed</span>
                        </motion.button>
                    </Link>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 px-4 py-2 bg-surface rounded-lg border border-border">
                            <Clock className="w-4 h-4 text-primary" />
                            <span className="text-sm font-semibold text-text-primary">
                                {readingTime} min read
                            </span>
                        </div>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handlePrint}
                            className="flex items-center gap-2 px-4 py-2 bg-surface rounded-lg border border-border hover:border-primary hover:text-primary transition-colors text-text-secondary"
                            aria-label="Print article"
                        >
                            <Printer className="w-4 h-4" />
                            <span className="text-sm font-semibold">Print</span>
                        </motion.button>
                    </div>
                </motion.div>
                {/* Hero Image */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full h-64 md:h-96 rounded-2xl mb-8 overflow-hidden"
                >
                    {article.image_url ? (
                        <img
                            src={article.image_url}
                            alt={article.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-sky-blue/30 to-ai-purple/30" />
                    )}
                </motion.div>

                {/* Title & Meta */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <h1 className="text-4xl md:text-5xl font-heading font-bold text-text-primary mb-4 leading-tight">
                        {article.title}
                    </h1>

                    <div className="flex flex-wrap items-center gap-4 mb-6 text-sm">
                        {article.category && (
                            <span className={`px-3 py-1 ${categoryColors[article.category] || 'bg-sky-blue'} text-white rounded-full font-semibold`}>
                                {article.category}
                            </span>
                        )}
                        {article.source && (
                            <span className="text-text-secondary">
                                📡 {article.source}
                            </span>
                        )}
                        {article.age_group && (
                            <span className="px-3 py-1 bg-mint/10 text-mint rounded-full font-semibold">
                                Ages {article.age_group}
                            </span>
                        )}
                        {article.word_count && (
                            <span className="flex items-center gap-1 text-text-muted">
                                <BookOpen className="w-4 h-4" />
                                {article.word_count} words
                            </span>
                        )}
                        <span className="flex items-center gap-1 text-text-muted">
                            <Clock className="w-4 h-4" />
                            {readingTime} min read
                        </span>
                    </div>

                    <hr className="border-border mb-8" />
                </motion.div>

                {/* Article Body */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="prose prose-lg max-w-none"
                >
                    {article.full_text ? (
                        <div className="text-text-primary leading-relaxed whitespace-pre-wrap">
                            {article.full_text}
                        </div>
                    ) : (
                        <p className="text-text-secondary italic">
                            Full article text not available. Visit the source for more information.
                        </p>
                    )}
                </motion.div>

                {/* CTA to Write */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="mt-12 bg-gradient-to-br from-ai-purple/10 to-sky-blue/10 rounded-2xl p-8 text-center border-2 border-ai-purple/20 no-print"
                >
                    <div className="flex justify-center mb-4">
                        <div className="w-16 h-16 bg-ai-purple rounded-full flex items-center justify-center">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h3 className="text-2xl font-heading font-bold text-text-primary mb-3">
                        💡 Ready to Write Your Own Version?
                    </h3>
                    <p className="text-text-secondary mb-6 max-w-xl mx-auto">
                        Use our AI writing coach to help you write an amazing article about this topic!
                    </p>
                    <Link href={`/news/${articleId}/write`}>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="px-8 py-4 bg-gradient-to-r from-sky-blue to-ai-purple text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-shadow"
                        >
                            Start Writing This News →
                        </motion.button>
                    </Link>
                </motion.div>

                {/* Source Link */}
                {article.url && (
                    <div className="mt-8 text-center no-print">
                        <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-blue hover:underline text-sm"
                        >
                            View Original Article →
                        </a>
                    </div>
                )}
            </article>
        </div>
        </>
    )
}
