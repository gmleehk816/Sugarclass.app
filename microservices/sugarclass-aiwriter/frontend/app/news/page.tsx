'use client'

import { motion } from 'framer-motion'
import { ArrowLeft, Settings2, Search, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { useState, useEffect } from 'react'
import ArticleCard from '@/components/ArticleCard'
import { getArticles, Article, triggerCollection } from '@/lib/api'

export default function NewsPage() {
    const [selectedCategory, setSelectedCategory] = useState('All')
    const [selectedAge, setSelectedAge] = useState('All Ages')
    const [articles, setArticles] = useState<Article[]>([])
    const [loading, setLoading] = useState(true)
    const [loadingMore, setLoadingMore] = useState(false)
    const [syncing, setSyncing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [offset, setOffset] = useState(0)
    const pageSize = 12

    const categories = [
        { name: 'All', icon: '📰', color: 'primary' },
        { name: 'science', icon: '🔬', color: 'science' },
        { name: 'technology', icon: '💻', color: 'tech' },
        { name: 'environment', icon: '🌍', color: 'environment' },
        { name: 'sports', icon: '⚽', color: 'sports' },
        { name: 'arts', icon: '🎨', color: 'arts' },
        { name: 'health', icon: '❤️', color: 'health' },
    ]

    const ageGroups = ['All Ages', '7-10', '11-14', '15-18']

    async function fetchArticles(isLoadMore = false) {
        try {
            if (isLoadMore) setLoadingMore(true)
            else {
                setLoading(true)
                setOffset(0)
            }

            const currentOffset = isLoadMore ? offset + pageSize : 0
            const filters: any = {
                limit: pageSize,
                offset: currentOffset
            }
            if (selectedCategory !== 'All') filters.category = selectedCategory.toLowerCase()
            if (selectedAge !== 'All Ages') filters.age_group = selectedAge

            const data = await getArticles(filters)

            if (isLoadMore) {
                setArticles((prev: Article[]) => [...prev, ...data])
                setOffset(currentOffset)
            } else {
                setArticles(data)
                setOffset(0)
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load articles')
        } finally {
            setLoading(false)
            setLoadingMore(false)
        }
    }

    async function handleSyncNews() {
        try {
            setSyncing(true)
            await triggerCollection()
            await fetchArticles() // Refresh the list
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to sync news')
        } finally {
            setSyncing(false)
        }
    }

    // Fetch articles from API
    useEffect(() => {
        fetchArticles()
    }, [selectedCategory, selectedAge])

    return (
        <div className="min-h-screen bg-background pt-4">
            {/* Page Title Section */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-between mb-8"
                >
                    <div>
                        <h1 className="text-3xl md:text-4xl font-heading font-bold text-text-primary mb-2">
                            📰 News Feed
                        </h1>
                        <p className="text-text-secondary">
                            Discover fascinating stories from around the world
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleSyncNews}
                            disabled={syncing}
                            className={`flex items-center gap-2 px-4 py-2 bg-surface rounded-xl hover:bg-surface-dark transition-colors shadow-sm text-sm font-semibold text-text-secondary ${syncing ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <div className={`${syncing ? 'animate-spin' : ''}`}>
                                <RefreshCw className="w-4 h-4" />
                            </div>
                            {syncing ? 'Syncing...' : 'Sync Latest News'}
                        </motion.button>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="p-3 bg-surface rounded-xl hover:bg-surface-dark transition-colors shadow-sm"
                        >
                            <Settings2 className="w-5 h-5 text-text-secondary" />
                        </motion.button>
                    </div>
                </motion.div>
                {/* Search Bar */}
                <div className="mb-8">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
                        <input
                            type="text"
                            placeholder="Search for news stories..."
                            className="w-full pl-12 pr-4 py-3 bg-white border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-blue focus:border-transparent transition-all"
                        />
                    </div>
                </div>

                {/* Category Filters */}
                <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-secondary mb-3">Categories</h3>
                    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                        {categories.map((cat) => (
                            <motion.button
                                key={cat.name}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setSelectedCategory(cat.name)}
                                className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap transition-all duration-200 ${selectedCategory === cat.name
                                    ? 'bg-sky-blue text-white shadow-md'
                                    : 'bg-white text-text-secondary hover:bg-surface-muted border border-border'
                                    }`}
                            >
                                {cat.icon} {cat.name}
                            </motion.button>
                        ))}
                    </div>
                </div>

                {/* Age Group Filters */}
                <div className="mb-8">
                    <h3 className="text-sm font-semibold text-text-secondary mb-3">Age Group</h3>
                    <div className="flex gap-2">
                        {ageGroups.map((age) => (
                            <motion.button
                                key={age}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setSelectedAge(age)}
                                className={`px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${selectedAge === age
                                    ? 'bg-mint text-white shadow-md'
                                    : 'bg-white text-text-secondary hover:bg-surface-muted border border-border'
                                    }`}
                            >
                                {age}
                            </motion.button>
                        ))}
                    </div>
                </div>

                {/* Articles Grid */}
                {loading ? (
                    <div className="flex justify-center items-center py-20">
                        <div className="text-center">
                            <div className="animate-spin w-12 h-12 border-4 border-sky-blue border-t-transparent rounded-full mx-auto mb-4" />
                            <p className="text-text-secondary">Loading articles...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="flex justify-center items-center py-20">
                        <div className="text-center">
                            <p className="text-red-500 mb-4">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-2 bg-sky-blue text-white rounded-lg font-semibold"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                ) : articles.length === 0 ? (
                    <div className="flex justify-center items-center py-20">
                        <p className="text-text-secondary text-lg">No articles found with these filters.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {articles.map((article: Article, index: number) => (
                            <ArticleCard key={article.id} article={article} index={index} />
                        ))}
                    </div>
                )}
                {/* Load More */}
                <div className="mt-12 text-center pb-12">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => fetchArticles(true)}
                        disabled={loadingMore || loading}
                        className={`px-8 py-3 bg-white border-2 border-border text-text-primary rounded-xl font-semibold hover:border-sky-blue hover:text-sky-blue transition-all duration-200 ${(loadingMore || loading) ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                    >
                        {loadingMore ? (
                            <div className="flex items-center gap-2">
                                <div className="animate-spin w-4 h-4 border-2 border-sky-blue border-t-transparent rounded-full" />
                                <span>Loading...</span>
                            </div>
                        ) : (
                            'Load More Articles'
                        )}
                    </motion.button>
                </div>
            </div>
        </div >
    )
}
