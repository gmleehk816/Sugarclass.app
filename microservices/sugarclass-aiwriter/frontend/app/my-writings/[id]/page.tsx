'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Save, Loader2, CheckCircle2, BookOpen, ChevronDown, ChevronUp, Wand2, Sparkles, Bot, Lightbulb, Edit3, X } from 'lucide-react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getMyWritings, UserWriting, saveWriting, generatePrewrite, generateSuggestion, improveText, getArticle, Article } from '@/lib/api'
import dynamic from 'next/dynamic'

const RichTextEditor = dynamic(() => import('@/components/RichTextEditor'), {
    ssr: false,
    loading: () => (
        <div className="w-full h-[500px] p-4 border border-border rounded-lg bg-surface animate-pulse">
            <div className="h-4 bg-surface-dark rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-surface-dark rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-surface-dark rounded w-5/6"></div>
        </div>
    )
})

type TabType = 'plan' | 'suggest' | 'improve'

export default function EditWritingPage() {
    const params = useParams()
    const router = useRouter()
    const writingId = parseInt(params.id as string)

    const [writing, setWriting] = useState<UserWriting | null>(null)
    const [article, setArticle] = useState<Article | null>(null)
    const [loading, setLoading] = useState(true)
    const [userText, setUserText] = useState('')
    const [contentHtml, setContentHtml] = useState('')
    const [contentJson, setContentJson] = useState('')
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

    // AI Assistant states
    const [prewriteSummary, setPrewriteSummary] = useState<string | null>(null)
    const [aiSuggestion, setAiSuggestion] = useState<string | null>(null)
    const [aiLoading, setAiLoading] = useState(false)
    const [aiError, setAiError] = useState<string | null>(null)
    const [yearLevel, setYearLevel] = useState('Year 7')
    const [activeTab, setActiveTab] = useState<TabType>('suggest')
    const [articlePanelExpanded, setArticlePanelExpanded] = useState(false)

    // Load the saved writing and article
    useEffect(() => {
        async function fetchData() {
            try {
                const response = await getMyWritings()
                if (response.success) {
                    const found = response.writings.find(w => w.id === writingId)
                    if (found) {
                        setWriting(found)
                        // Load the saved content
                        if (found.content_json) {
                            setContentJson(found.content_json)
                        }
                        if (found.content_html) {
                            setContentHtml(found.content_html)
                        }
                        setUserText(found.content || '')
                        setYearLevel(found.year_level || 'Year 7')

                        // Fetch the article for AI features
                        try {
                            const articleData = await getArticle(found.article_id)
                            setArticle(articleData)
                        } catch (err) {
                            console.error('Failed to load article:', err)
                        }
                    } else {
                        alert('Writing not found')
                        router.push('/my-writings')
                    }
                } else {
                    alert('Failed to load writing')
                    router.push('/my-writings')
                }
            } catch (err) {
                alert('Failed to connect to server')
                router.push('/my-writings')
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [writingId, router])

    const wordCount = userText.trim().split(/\s+/).filter(w => w.length > 0).length

    async function handleSave() {
        if (!writing) return

        setSaveStatus('saving')
        try {
            const response = await saveWriting({
                article_id: writing.article_id,
                title: writing.title,
                content: userText,
                content_html: contentHtml,
                content_json: contentJson,
                word_count: wordCount,
                year_level: yearLevel,
            })

            if (response.success) {
                setSaveStatus('saved')
                setTimeout(() => setSaveStatus('idle'), 3000)
            } else {
                setSaveStatus('error')
                alert(response.error || 'Failed to save')
            }
        } catch (err) {
            setSaveStatus('error')
            alert('Failed to connect to server')
        }
    }

    function handleEditorChange(text: string, html: string, json: string) {
        setUserText(text)
        setContentHtml(html)
        setContentJson(json)
    }

    // AI Assistant handlers
    async function handleGeneratePrewrite() {
        if (!article || !article.full_text) return

        setAiLoading(true)
        setAiError(null)

        try {
            const response = await generatePrewrite({
                title: article.title,
                text: article.full_text,
                year_level: yearLevel
            })

            if (response.success && response.summary) {
                setPrewriteSummary(response.summary)
            } else {
                setAiError(response.error || 'Failed to generate plan')
            }
        } catch (err) {
            setAiError(err instanceof Error ? err.message : 'Failed to generate plan')
        } finally {
            setAiLoading(false)
        }
    }

    async function handleGenerateSuggestion() {
        if (!article || !article.full_text) return

        setAiLoading(true)
        setAiError(null)
        setAiSuggestion(null)

        try {
            const response = await generateSuggestion({
                user_text: userText,
                title: article.title,
                article_text: article.full_text,
                year_level: yearLevel,
                prewrite_summary: prewriteSummary || undefined
            })

            if (response.success && response.suggestion) {
                setAiSuggestion(response.suggestion)
            } else {
                setAiError(response.error || 'Failed to generate suggestion')
            }
        } catch (err) {
            setAiError(err instanceof Error ? err.message : 'Failed to generate suggestion')
        } finally {
            setAiLoading(false)
        }
    }

    async function handleImproveText() {
        if (!article || !article.full_text || !userText.trim()) {
            setAiError('Please write something first!')
            return
        }

        setAiLoading(true)
        setAiError(null)
        setAiSuggestion(null)

        try {
            const response = await improveText({
                text: userText,
                article_text: article.full_text,
                year_level: yearLevel
            })

            if (response.success && response.improved) {
                setAiSuggestion(response.improved)
            } else {
                setAiError(response.error || 'Failed to improve text')
            }
        } catch (err) {
            setAiError(err instanceof Error ? err.message : 'Failed to improve text')
        } finally {
            setAiLoading(false)
        }
    }

    function handleAddToEditor() {
        if (aiSuggestion) {
            setUserText(prev => prev + '\n\n' + aiSuggestion)
            setAiSuggestion(null)
        }
    }

    function handleReplaceWithImproved() {
        if (aiSuggestion) {
            setUserText(aiSuggestion)
            setAiSuggestion(null)
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-text-secondary">Loading your writing...</p>
                </div>
            </div>
        )
    }

    if (!writing) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <p className="text-warning mb-4">Writing not found</p>
                    <Link href="/my-writings">
                        <button className="px-6 py-2 bg-primary text-white rounded-lg font-semibold">
                            Back to My Writings
                        </button>
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pt-4">
            {/* Writing Tools Bar */}
            <div className="sticky top-20 z-40 bg-surface/95 backdrop-blur-md border-b border-border">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-14">
                        <Link href="/my-writings">
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="flex items-center gap-2 text-text-secondary hover:text-primary transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                <span className="font-semibold">Back</span>
                            </motion.button>
                        </Link>

                        <div className="flex items-center gap-6">
                            {/* Word Counter */}
                            <div className="text-center">
                                <div className="text-2xl font-bold text-primary">
                                    {wordCount}
                                </div>
                                <div className="text-xs text-text-muted">words</div>
                            </div>

                            {/* Year Level Selector */}
                            <select
                                value={yearLevel}
                                onChange={(e) => {
                                    setYearLevel(e.target.value)
                                    setPrewriteSummary(null)
                                    setAiSuggestion(null)
                                }}
                                className="px-3 py-1.5 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-surface text-text-primary"
                            >
                                <option>Year 5</option>
                                <option>Year 6</option>
                                <option>Year 7</option>
                                <option>Year 8</option>
                                <option>Year 9</option>
                            </select>

                            {/* Save Button */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleSave}
                                disabled={saveStatus === 'saving'}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm ${saveStatus === 'saved'
                                        ? 'bg-success text-white'
                                        : saveStatus === 'error'
                                            ? 'bg-warning text-white'
                                            : 'bg-primary text-white hover:bg-primary/90'
                                    } disabled:opacity-50`}
                            >
                                {saveStatus === 'saving' ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : saveStatus === 'saved' ? (
                                    <CheckCircle2 className="w-4 h-4" />
                                ) : (
                                    <Save className="w-4 h-4" />
                                )}
                                {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : saveStatus === 'error' ? 'Failed' : 'Save'}
                            </motion.button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left Column - Article Reference & Editor (7 cols) */}
                    <div className="lg:col-span-7 space-y-4">
                        {/* Article Reference - Collapsible */}
                        {article && (
                            <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
                                <button
                                    onClick={() => setArticlePanelExpanded(!articlePanelExpanded)}
                                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-dark/50 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <BookOpen className="w-4 h-4 text-primary" />
                                        <span className="font-semibold text-sm text-text-primary">Source Article</span>
                                        <span className="text-xs text-text-muted ml-2">{article.source}</span>
                                    </div>
                                    {articlePanelExpanded ? (
                                        <ChevronUp className="w-4 h-4 text-text-muted" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-text-muted" />
                                    )}
                                </button>

                                <AnimatePresence>
                                    {articlePanelExpanded && (
                                        <motion.div
                                            initial={{ height: 0 }}
                                            animate={{ height: 'auto' }}
                                            exit={{ height: 0 }}
                                            className="border-t border-border"
                                        >
                                            <div className="p-4">
                                                <h3 className="font-semibold text-text-primary mb-2">{article.title}</h3>
                                                <div className="text-xs text-text-muted mb-3">
                                                    {article.category} • {article.age_group} • {article.word_count} words
                                                </div>
                                                <div className="max-h-60 overflow-y-auto text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                                                    {article.full_text || article.description || 'No content available'}
                                                </div>
                                                {article.url && (
                                                    <a
                                                        href={article.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="mt-3 inline-block text-xs text-primary hover:underline"
                                                    >
                                                        Open original article →
                                                    </a>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        )}

                        {/* Writing info card */}
                        <div className="bg-surface rounded-xl shadow-sm border border-border p-4">
                            <h2 className="text-lg font-heading font-bold text-text-primary mb-2">
                                {writing.title}
                            </h2>
                            <div className="text-xs text-text-muted">
                                {writing.word_count} words • {writing.year_level || 'N/A'} • Saved on {new Date(writing.created_at).toLocaleDateString()}
                            </div>
                            {!article && (
                                <Link href={`/news/${writing.article_id}`} className="text-primary hover:underline text-sm inline-block mt-2">
                                    View original article →
                                </Link>
                            )}
                        </div>

                        {/* Text Editor */}
                        <div className="bg-surface rounded-xl shadow-sm border border-border p-4">
                            <h2 className="text-lg font-heading font-bold text-text-primary mb-2">Edit Your Writing</h2>
                            <RichTextEditor
                                content={userText}
                                contentJson={contentJson}
                                onChange={handleEditorChange}
                                placeholder="Your writing will appear here..."
                            />
                        </div>
                    </div>

                    {/* Right Column - AI Assistant (5 cols) */}
                    <div className="lg:col-span-5">
                        <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden sticky top-24">
                            {/* AI Assistant Header */}
                            <div className="bg-gradient-to-r from-primary to-accent px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white text-sm">AI Writing Coach</h3>
                                        <p className="text-xs text-white/80">Ready to help!</p>
                                    </div>
                                </div>
                            </div>

                            {/* Tabs */}
                            <div className="flex border-b border-border">
                                <button
                                    onClick={() => setActiveTab('plan')}
                                    className={`flex-1 px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${activeTab === 'plan'
                                        ? 'text-primary border-b-2 border-primary bg-primary/5'
                                        : 'text-text-muted hover:text-text-primary'
                                        }`}
                                >
                                    <BookOpen className="w-4 h-4" />
                                    Plan
                                </button>
                                <button
                                    onClick={() => setActiveTab('suggest')}
                                    className={`flex-1 px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${activeTab === 'suggest'
                                        ? 'text-primary border-b-2 border-primary bg-primary/5'
                                        : 'text-text-muted hover:text-text-primary'
                                        }`}
                                >
                                    <Lightbulb className="w-4 h-4" />
                                    Suggest
                                </button>
                                <button
                                    onClick={() => setActiveTab('improve')}
                                    className={`flex-1 px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${activeTab === 'improve'
                                        ? 'text-primary border-b-2 border-primary bg-primary/5'
                                        : 'text-text-muted hover:text-text-primary'
                                        }`}
                                >
                                    <Edit3 className="w-4 h-4" />
                                    Improve
                                </button>
                            </div>

                            {/* Tab Content */}
                            <div className="p-4">
                                {/* Plan Tab */}
                                {activeTab === 'plan' && (
                                    <div className="space-y-3">
                                        <p className="text-sm text-text-secondary">Get a quick writing plan to guide you.</p>
                                        <motion.button
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={handleGeneratePrewrite}
                                            disabled={aiLoading || !article}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                                        >
                                            {aiLoading ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Sparkles className="w-4 h-4" />
                                            )}
                                            Generate Writing Plan
                                        </motion.button>

                                        {prewriteSummary && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="bg-primary/5 rounded-lg p-3 border border-primary/20"
                                            >
                                                <div className="text-xs text-primary font-semibold mb-2 flex items-center gap-1">
                                                    <BookOpen className="w-3 h-3" />
                                                    Your Writing Plan
                                                </div>
                                                <div className="text-sm text-text-primary whitespace-pre-wrap leading-relaxed">
                                                    {prewriteSummary}
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>
                                )}

                                {/* Suggest Tab */}
                                {activeTab === 'suggest' && (
                                    <div className="space-y-3">
                                        <p className="text-sm text-text-secondary">
                                            {userText.length > 10
                                                ? 'Get suggestions for your next paragraph.'
                                                : 'Write a few words first, then get suggestions!'}
                                        </p>
                                        <motion.button
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={handleGenerateSuggestion}
                                            disabled={aiLoading || userText.length < 10 || !article}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                                        >
                                            {aiLoading ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Wand2 className="w-4 h-4" />
                                            )}
                                            Suggest Next Paragraph
                                        </motion.button>

                                        {aiSuggestion && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="bg-accent/5 rounded-lg p-3 border border-accent/20"
                                            >
                                                <div className="text-xs text-accent font-semibold mb-2 flex items-center gap-1">
                                                    <Lightbulb className="w-3 h-3" />
                                                    Suggested Paragraph
                                                </div>
                                                <div className="text-sm text-text-primary leading-relaxed mb-3">
                                                    {aiSuggestion}
                                                </div>
                                                <button
                                                    onClick={handleAddToEditor}
                                                    className="w-full px-3 py-2 bg-accent text-white rounded-lg text-sm font-semibold hover:bg-accent/90 transition-colors"
                                                >
                                                    Add to My Writing
                                                </button>
                                            </motion.div>
                                        )}
                                    </div>
                                )}

                                {/* Improve Tab */}
                                {activeTab === 'improve' && (
                                    <div className="space-y-3">
                                        <p className="text-sm text-text-secondary">
                                            {userText.length > 20
                                                ? 'Let AI improve your writing.'
                                                : 'Write more text to get improvements.'}
                                        </p>
                                        <motion.button
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={handleImproveText}
                                            disabled={aiLoading || userText.length < 20 || !article}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-success text-white rounded-lg font-semibold hover:bg-success/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                                        >
                                            {aiLoading ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Sparkles className="w-4 h-4" />
                                            )}
                                            Improve My Writing
                                        </motion.button>

                                        {aiSuggestion && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="bg-success/5 rounded-lg p-3 border border-success/20"
                                            >
                                                <div className="text-xs text-success font-semibold mb-2 flex items-center gap-1">
                                                    <Edit3 className="w-3 h-3" />
                                                    Improved Version
                                                </div>
                                                <div className="text-sm text-text-primary leading-relaxed mb-3 max-h-40 overflow-y-auto">
                                                    {aiSuggestion}
                                                </div>
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={handleReplaceWithImproved}
                                                        className="flex-1 px-3 py-2 bg-success text-white rounded-lg text-sm font-semibold hover:bg-success/90 transition-colors"
                                                    >
                                                        Use This
                                                    </button>
                                                    <button
                                                        onClick={() => setAiSuggestion(null)}
                                                        className="px-3 py-2 bg-surface-dark border border-border text-text-primary rounded-lg text-sm font-semibold hover:bg-surface transition-colors"
                                                    >
                                                        <X className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>
                                )}

                                {/* AI Error */}
                                <AnimatePresence>
                                    {aiError && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0 }}
                                            className="bg-warning/10 rounded-lg p-3 border border-warning/30"
                                        >
                                            <p className="text-sm text-warning">{aiError}</p>
                                            <button
                                                onClick={() => setAiError(null)}
                                                className="mt-2 text-xs text-warning hover:underline"
                                            >
                                                Dismiss
                                            </button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
