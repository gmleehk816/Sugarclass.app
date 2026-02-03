'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Save, Loader2, CheckCircle2, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getMyWritings, UserWriting, saveWriting } from '@/lib/api'
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

export default function EditWritingPage() {
    const params = useParams()
    const router = useRouter()
    const writingId = parseInt(params.id as string)

    const [writing, setWriting] = useState<UserWriting | null>(null)
    const [loading, setLoading] = useState(true)
    const [userText, setUserText] = useState('')
    const [contentHtml, setContentHtml] = useState('')
    const [contentJson, setContentJson] = useState('')
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

    // Load the saved writing
    useEffect(() => {
        async function fetchWriting() {
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

        fetchWriting()
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
                year_level: writing.year_level || 'Year 7',
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
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
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

            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Article Reference */}
                <div className="bg-surface rounded-xl shadow-sm border border-border p-4 mb-4">
                    <h2 className="text-lg font-heading font-bold text-text-primary mb-2">
                        {writing.title}
                    </h2>
                    <div className="text-xs text-text-muted">
                        {writing.word_count} words • {writing.year_level || 'N/A'} • Saved on {new Date(writing.created_at).toLocaleDateString()}
                    </div>
                    <Link href={`/news/${writing.article_id}`} className="text-primary hover:underline text-sm inline-block mt-2">
                        View original article →
                    </Link>
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
        </div>
    )
}
