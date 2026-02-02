import React from 'react'
import { Clock, BookOpen } from 'lucide-react'
import Link from 'next/link'
import { Article } from '@/lib/api'

interface ArticleCardProps {
    article: Article
    index: number
    key?: any
}

const categoryColors: Record<string, string> = {
    Science: 'bg-science text-white',
    Technology: 'bg-tech text-white',
    Environment: 'bg-environment text-white',
    Sports: 'bg-sports text-white',
    Arts: 'bg-arts text-white',
    Health: 'bg-health text-white',
}

export default function ArticleCard({ article }: ArticleCardProps) {
    const readingTime = Math.ceil((article.word_count || 300) / 200) // Assuming 200 words per minute

    return (
        <div>
            <Link href={`/news/${article.id}`}>
                <div className="group bg-white rounded-2xl shadow-md overflow-hidden cursor-pointer h-full flex flex-col hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                    {/* Image with gradient overlay */}
                    <div className="relative h-48 overflow-hidden bg-gradient-to-br from-accent/20 to-primary/20">
                        {article.image_url ? (
                            <img
                                src={article.image_url}
                                alt={article.title}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                            />
                        ) : (
                            <div className="w-full h-full bg-gradient-to-br from-accent/30 to-primary/30 group-hover:scale-110 transition-transform duration-500" />
                        )}

                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />

                        {/* Category Badge */}
                        {article.category && (
                            <span className={`absolute top-3 left-3 px-3 py-1 ${categoryColors[article.category] || 'bg-accent text-white'} backdrop-blur-sm rounded-full text-xs font-semibold shadow-lg`}>
                                {article.category}
                            </span>
                        )}
                    </div>

                    {/* Content */}
                    <div className="p-5 flex-1 flex flex-col">
                        <h3 className="text-xl font-heading font-bold text-text-primary mb-2 line-clamp-2 group-hover:text-accent transition-colors">
                            {article.title}
                        </h3>
                        <p className="text-sm text-text-secondary mb-4 line-clamp-3 leading-relaxed flex-1">
                            {article.description || 'No description available.'}
                        </p>

                        {/* Meta Information */}
                        <div className="flex items-center justify-between text-xs text-text-muted pt-4 border-t border-border">
                            <div className="flex items-center gap-4">
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {readingTime} min
                                </span>
                                {article.word_count && (
                                    <span className="flex items-center gap-1">
                                        <BookOpen className="w-3 h-3" />
                                        {article.word_count} words
                                    </span>
                                )}
                            </div>
                            {article.age_group && (
                                <span className="px-2 py-1 bg-success/10 text-success rounded-full font-semibold">
                                    Ages {article.age_group}
                                </span>
                            )}
                        </div>

                        {/* Source */}
                        {article.source && (
                            <div className="mt-2 text-xs text-text-muted">
                                📡 {article.source}
                            </div>
                        )}
                    </div>
                </div>
            </Link>
        </div>
    )
}
