'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Calendar, Trash2, Edit3, FileText, Loader2, ChevronDown, ChevronUp, Search, Grid3x3, List, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getMyWritings, UserWriting } from '@/lib/api'

type ViewMode = 'grid' | 'list'

export default function MyWritingsPage() {
    const [writings, setWritings] = useState<UserWriting[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())
    const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set())
    const [viewMode, setViewMode] = useState<ViewMode>('grid')
    const [searchQuery, setSearchQuery] = useState('')

    // Filter writings based on search query
    const filteredWritings = writings.filter(writing =>
        writing.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        writing.content.toLowerCase().includes(searchQuery.toLowerCase())
    )

    useEffect(() => {
        async function fetchWritings() {
            try {
                const response = await getMyWritings()
                if (response.success) {
                    setWritings(response.writings)
                } else {
                    setError(response.error || 'Failed to load writings')
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to connect to server')
            } finally {
                setLoading(false)
            }
        }

        fetchWritings()
    }, [])

    function toggleExpand(id: number) {
        setExpandedIds(prev => {
            const newSet = new Set(prev)
            if (newSet.has(id)) {
                newSet.delete(id)
            } else {
                newSet.add(id)
            }
            return newSet
        })
    }

    function formatDate(dateString: string) {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    async function handleDelete(id: number, event: React.MouseEvent) {
        event.stopPropagation()
        event.preventDefault()

        if (!confirm('Are you sure you want to delete this writing?')) {
            return
        }

        setDeletingIds(prev => new Set(prev).add(id))

        try {
            const token = localStorage.getItem('sugarclass_token')
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/ai/writings/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                },
            })

            if (response.ok) {
                setWritings(prev => prev.filter(w => w.id !== id))
            } else {
                alert('Failed to delete writing')
            }
        } catch (err) {
            alert('Failed to connect to server')
        } finally {
            setDeletingIds(prev => {
                const newSet = new Set(prev)
                newSet.delete(id)
                return newSet
            })
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-text-secondary">Loading your writings...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pb-12">
            {/* Header */}
            <div className="bg-surface border-b border-border">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                        <div>
                            <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">My Writings</h1>
                            <p className="text-text-secondary">
                                {writings.length} {writings.length === 1 ? 'writing' : 'writings'} saved
                            </p>
                        </div>

                        {/* View Toggle */}
                        <div className="flex items-center gap-2 bg-surface-dark rounded-lg p-1 border border-border">
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`p-2 rounded-md transition-colors ${
                                    viewMode === 'grid'
                                        ? 'bg-primary text-white'
                                        : 'text-text-muted hover:text-text-primary hover:bg-surface'
                                }`}
                                title="Grid view"
                            >
                                <Grid3x3 className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setViewMode('list')}
                                className={`p-2 rounded-md transition-colors ${
                                    viewMode === 'list'
                                        ? 'bg-primary text-white'
                                        : 'text-text-muted hover:text-text-primary hover:bg-surface'
                                }`}
                                title="List view"
                            >
                                <List className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Search Bar */}
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                        <input
                            type="text"
                            placeholder="Search writings by title or content..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 bg-surface-dark border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-text-primary placeholder:text-text-muted"
                        />
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="bg-warning/10 border border-warning/30 rounded-lg p-4 mb-6">
                        <p className="text-warning">{error}</p>
                    </div>
                )}

                {filteredWritings.length === 0 && writings.length > 0 ? (
                    <div className="text-center py-16">
                        <Search className="w-16 h-16 text-text-muted mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-text-primary mb-2">No writings found</h2>
                        <p className="text-text-secondary">Try adjusting your search query</p>
                    </div>
                ) : writings.length === 0 ? (
                    <div className="text-center py-16">
                        <FileText className="w-16 h-16 text-text-muted mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-text-primary mb-2">No writings yet</h2>
                        <p className="text-text-secondary mb-6">Start writing and save your first article!</p>
                        <Link href="/news">
                            <button className="px-6 py-2 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-colors">
                                Browse News Articles
                            </button>
                        </Link>
                    </div>
                ) : viewMode === 'grid' ? (
                    // Grid View
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredWritings.map(writing => (
                            <motion.div
                                key={writing.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden hover:shadow-md transition-shadow"
                            >
                                <Link href={`/my-writings/${writing.id}`} className="block h-full">
                                    <div className="p-5">
                                        {/* Title */}
                                        <h3 className="font-semibold text-text-primary mb-3 line-clamp-2 text-lg">
                                            {writing.title}
                                        </h3>

                                        {/* Year Level Badge */}
                                        {writing.year_level && (
                                            <div className="mb-3">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                                                    {writing.year_level}
                                                </span>
                                            </div>
                                        )}

                                        {/* Content Preview */}
                                        <div className="text-sm text-text-secondary mb-4 line-clamp-3">
                                            {writing.content}
                                        </div>

                                        {/* Footer */}
                                        <div className="flex items-center justify-between pt-3 border-t border-border">
                                            <div className="flex items-center gap-3 text-xs text-text-muted">
                                                <span className="flex items-center gap-1">
                                                    <BookOpen className="w-3.5 h-3.5" />
                                                    {writing.word_count} words
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3.5 h-3.5" />
                                                    {formatDate(writing.created_at)}
                                                </span>
                                            </div>
                                            <ChevronRight className="w-5 h-5 text-text-muted" />
                                        </div>

                                        {/* Milestone */}
                                        {writing.milestone_message && (
                                            <div className="mt-3 pt-3 border-t border-border">
                                                <span className="text-xs text-primary font-medium">
                                                    {writing.milestone_message}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </Link>

                                {/* Actions */}
                                <div className="flex border-t border-border divide-x divide-border">
                                    <Link
                                        href={`/my-writings/${writing.id}`}
                                        className="flex-1 py-2.5 text-center text-sm font-medium text-text-primary hover:bg-surface-dark transition-colors flex items-center justify-center gap-1.5"
                                    >
                                        <Edit3 className="w-4 h-4" />
                                        Edit
                                    </Link>
                                    <button
                                        onClick={(e) => handleDelete(writing.id, e)}
                                        disabled={deletingIds.has(writing.id)}
                                        className="flex-1 py-2.5 text-center text-sm font-medium text-danger hover:bg-surface-dark transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                                    >
                                        {deletingIds.has(writing.id) ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <Trash2 className="w-4 h-4" />
                                        )}
                                        Delete
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                ) : (
                    // List View
                    <div className="space-y-4 max-w-4xl mx-auto">
                        {filteredWritings.map(writing => (
                            <motion.div
                                key={writing.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden"
                            >
                                {/* Header */}
                                <button
                                    onClick={() => toggleExpand(writing.id)}
                                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-dark/50 transition-colors"
                                >
                                    <div className="flex-1 text-left">
                                        <h3 className="font-semibold text-text-primary mb-1 line-clamp-1">
                                            {writing.title}
                                        </h3>
                                        <div className="flex items-center gap-4 text-xs text-text-muted">
                                            <span className="flex items-center gap-1">
                                                <BookOpen className="w-3 h-3" />
                                                {writing.word_count} words
                                            </span>
                                            {writing.year_level && (
                                                <span>{writing.year_level}</span>
                                            )}
                                            <span className="flex items-center gap-1">
                                                <Calendar className="w-3 h-3" />
                                                {formatDate(writing.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Link
                                            href={`/my-writings/${writing.id}`}
                                            onClick={(e) => e.stopPropagation()}
                                            className="p-2 rounded-lg hover:bg-surface-dark text-text-muted hover:text-primary transition-colors"
                                            title="Edit writing"
                                        >
                                            <Edit3 className="w-4 h-4" />
                                        </Link>
                                        <button
                                            onClick={(e) => handleDelete(writing.id, e)}
                                            disabled={deletingIds.has(writing.id)}
                                            className="p-2 rounded-lg hover:bg-surface-dark text-text-muted hover:text-danger transition-colors disabled:opacity-50"
                                            title="Delete"
                                        >
                                            {deletingIds.has(writing.id) ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Trash2 className="w-4 h-4" />
                                            )}
                                        </button>
                                        {expandedIds.has(writing.id) ? (
                                            <ChevronUp className="w-5 h-5 text-text-muted" />
                                        ) : (
                                            <ChevronDown className="w-5 h-5 text-text-muted" />
                                        )}
                                    </div>
                                </button>

                                {/* Expanded Content */}
                                <AnimatePresence>
                                    {expandedIds.has(writing.id) && (
                                        <motion.div
                                            initial={{ height: 0 }}
                                            animate={{ height: 'auto' }}
                                            exit={{ height: 0 }}
                                            className="border-t border-border"
                                        >
                                            <div className="p-6">
                                                {writing.milestone_message && (
                                                    <div className="mb-4 inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                                                        <span>{writing.milestone_message}</span>
                                                    </div>
                                                )}

                                                {/* Render formatted HTML if available, otherwise plain text */}
                                                <div className="prose prose-sm max-w-none">
                                                    {writing.content_html ? (
                                                        <div
                                                            dangerouslySetInnerHTML={{ __html: writing.content_html }}
                                                            className="text-text-primary leading-relaxed"
                                                        />
                                                    ) : (
                                                        <div className="text-text-primary whitespace-pre-wrap leading-relaxed">
                                                            {writing.content}
                                                        </div>
                                                    )}
                                                </div>

                                                {writing.updated_at !== writing.created_at && (
                                                    <div className="mt-4 text-xs text-text-muted">
                                                        Last updated: {formatDate(writing.updated_at)}
                                                    </div>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
