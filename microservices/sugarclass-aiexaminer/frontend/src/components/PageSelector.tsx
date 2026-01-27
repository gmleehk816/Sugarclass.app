'use client';

import { useState } from 'react';
import { FileText, Check, X, AlertCircle, Sparkles, CheckSquare, MessageSquare, ArrowRight, Search, BookOpen } from 'lucide-react';

interface PagePreview {
    page: number;
    title: string;
    preview: string;
    char_count: number;
    is_title_page: boolean;
}

interface PageSelectorProps {
    totalPages: number;
    maxPages: number;
    pagePreviews?: PagePreview[];
    contentPreview?: string;
    onConfirm: (selectedPages: number[], questionType: 'mcq' | 'short', numQuestions: number) => void;
    onCancel: () => void;
    requiresSelection?: boolean;
}

export default function PageSelector({
    totalPages,
    maxPages = 20,
    pagePreviews = [],
    contentPreview,
    onConfirm,
    onCancel,
    requiresSelection = true
}: PageSelectorProps) {
    const [selectedPages, setSelectedPages] = useState<Set<number>>(() => {
        if (!requiresSelection) {
            return new Set(Array.from({ length: totalPages }, (_, i) => i + 1));
        }
        // For documents requiring selection, start with an empty set
        return new Set();
    });

    const [questionType, setQuestionType] = useState<'mcq' | 'short'>('mcq');
    const [numQuestions, setNumQuestions] = useState(15);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSelected, setShowSelected] = useState(false);

    const togglePage = (pageNum: number) => {
        const newSelected = new Set(selectedPages);
        if (newSelected.has(pageNum)) {
            newSelected.delete(pageNum);
        } else if (newSelected.size < maxPages) {
            newSelected.add(pageNum);
        }
        setSelectedPages(newSelected);
    };

    const selectRange = (start: number, end: number) => {
        const newSelected = new Set<number>();
        for (let i = start; i <= end && newSelected.size < maxPages; i++) {
            newSelected.add(i);
        }
        setSelectedPages(newSelected);
    };

    const selectAll = () => {
        const newSelected = new Set<number>();
        for (let i = 1; i <= Math.min(totalPages, maxPages); i++) {
            newSelected.add(i);
        }
        setSelectedPages(newSelected);
    };

    const clearAll = () => {
        setSelectedPages(new Set());
    };

    // Filter pages based on search query
    const filteredPreviews = pagePreviews.filter(p => {
        if (showSelected && !selectedPages.has(p.page)) return false;
        if (!searchQuery) return true;
        const query = searchQuery.toLowerCase();
        return (
            p.title.toLowerCase().includes(query) ||
            p.preview.toLowerCase().includes(query) ||
            p.page.toString() === query
        );
    });

    // Generate page items (either from previews or simple numbers)
    const pageItems = pagePreviews.length > 0
        ? filteredPreviews
        : Array.from({ length: totalPages }, (_, i) => ({
            page: i + 1,
            title: `Page ${i + 1}`,
            preview: i === 0 ? (contentPreview || '') : '',
            char_count: i === 0 ? (contentPreview?.length || 0) : 0,
            is_title_page: i === 0
        }));

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
            <div className={`bg-white rounded-[32px] shadow-2xl max-w-5xl w-full max-h-[95vh] overflow-hidden flex flex-col`}>
                {/* Header */}
                <div className="p-6 md:p-8 border-b border-card-border">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4">
                            <div className="p-4 rounded-2xl bg-accent-muted text-accent">
                                <Sparkles size={28} />
                            </div>
                            <div>
                                <h2 className="text-2xl font-extrabold text-primary">Configure Your Quiz</h2>
                                <p className="text-slate-500 font-medium text-sm">
                                    {requiresSelection
                                        ? `Select up to ${maxPages} focus pages from your ${totalPages}-page document.`
                                        : `Review your ${totalPages > 1 ? `${totalPages}-page` : 'one-page'} document and configure the assessment.`}
                                </p>
                            </div>
                        </div>
                        <button onClick={onCancel} className="p-3 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-all">
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
                    {/* Left: Page Context / Selection */}
                    <div className="flex-1 flex flex-col overflow-hidden border-r border-card-border bg-white">
                        {/* Search and Stats */}
                        <div className="p-4 border-b border-card-border bg-slate-50">
                            {requiresSelection ? (
                                <>
                                    <div className="flex items-center gap-3 mb-3">
                                        <div className="flex-1 relative">
                                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                            <input
                                                type="text"
                                                placeholder="Search pages by topic..."
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:border-primary focus:outline-none text-sm font-medium"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4 flex-wrap">
                                        <div className={`px-3 py-1.5 rounded-full font-bold text-xs ${selectedPages.size === maxPages ? 'bg-accent-muted text-accent' : 'bg-primary-muted text-primary'}`}>
                                            {selectedPages.size} / {maxPages} selected
                                        </div>
                                        <button onClick={selectAll} className="text-xs font-bold text-accent hover:underline">
                                            Select First {maxPages}
                                        </button>
                                        <button onClick={clearAll} className="text-xs font-bold text-slate-400 hover:text-slate-600">
                                            Clear All
                                        </button>
                                        <button
                                            onClick={() => setShowSelected(!showSelected)}
                                            className={`text-xs font-bold ${showSelected ? 'text-primary' : 'text-slate-400 hover:text-slate-600'}`}
                                        >
                                            {showSelected ? 'Show All' : 'Show Selected'}
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <div className="text-sm font-bold text-primary flex items-center gap-2">
                                    <FileText size={16} /> document Content Preview
                                </div>
                            )}
                        </div>

                        {/* Page List - Compact List View */}
                        <div className="flex-1 overflow-y-auto">
                            <div className="divide-y divide-slate-100">
                                {pageItems.map((page) => {
                                    const isSelected = selectedPages.has(page.page);
                                    const isDisabled = requiresSelection && !isSelected && selectedPages.size >= maxPages;

                                    return (
                                        <div
                                            key={page.page}
                                            onClick={() => requiresSelection && !isDisabled && togglePage(page.page)}
                                            className={`
                                                group flex items-center gap-4 px-6 py-3 transition-all
                                                ${requiresSelection && !isDisabled ? 'cursor-pointer hover:bg-slate-50' : 'cursor-default'}
                                                ${isSelected ? 'bg-primary/5' : ''}
                                                ${isDisabled ? 'opacity-40 grayscale cursor-not-allowed' : ''}
                                            `}
                                        >
                                            {/* Page Number Badge */}
                                            <div className={`
                                                w-8 h-8 rounded-lg flex items-center justify-center text-xs font-black shrink-0 transition-colors
                                                ${isSelected ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200'}
                                            `}>
                                                {page.page}
                                            </div>

                                            {/* Text Content */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <h4 className={`font-bold text-sm truncate ${isSelected ? 'text-primary' : 'text-slate-700'}`}>
                                                        {page.title}
                                                    </h4>
                                                    {page.is_title_page && (
                                                        <span className="px-1.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-amber-100 text-amber-700">
                                                            Topic
                                                        </span>
                                                    )}
                                                </div>
                                                {page.preview && (
                                                    <p className="text-xs text-slate-400 truncate mt-0.5">
                                                        {page.preview}
                                                    </p>
                                                )}
                                            </div>

                                            {/* Status Indicators */}
                                            <div className="flex items-center gap-3 shrink-0">
                                                {page.char_count > 0 && (
                                                    <span className="hidden sm:block text-[10px] font-bold text-slate-300 uppercase tracking-widest">
                                                        {page.char_count > 1000 ? `${(page.char_count / 1000).toFixed(1)}k` : page.char_count} chars
                                                    </span>
                                                )}

                                                {requiresSelection && (
                                                    <div className={`
                                                        w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all
                                                        ${isSelected ? 'bg-accent border-accent scale-110' : 'border-slate-200 group-hover:border-slate-300'}
                                                    `}>
                                                        {isSelected && <Check size={12} className="text-white" strokeWidth={4} />}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {pageItems.length === 0 && (
                                <div className="text-center py-12 text-slate-400">
                                    <BookOpen size={40} className="mx-auto mb-3 opacity-50" />
                                    <p className="font-medium">No pages match your search</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Quiz Settings */}
                    <div className="w-full md:w-[400px] flex flex-col bg-slate-50">
                        <div className="p-6 md:p-10 space-y-8 animate-fade-in">
                            {/* Question Count */}
                            <div>
                                <h3 className="font-extrabold text-primary mb-5 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-full bg-primary text-white text-sm flex items-center justify-center shadow-lg">1</span>
                                    Question Density
                                </h3>
                                <div className="grid grid-cols-3 gap-2">
                                    {[10, 15, 20].map((count) => (
                                        <button
                                            key={count}
                                            onClick={() => setNumQuestions(count)}
                                            className={`py-3 rounded-xl font-bold text-sm transition-all ${numQuestions === count
                                                ? 'bg-primary text-white shadow-lg'
                                                : 'bg-white text-slate-600 border border-slate-200 hover:border-primary'
                                                }`}
                                        >
                                            {count}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Question Type */}
                            <div>
                                <h3 className="font-extrabold text-primary mb-5 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-full bg-primary text-white text-sm flex items-center justify-center shadow-lg">2</span>
                                    Assessment Format
                                </h3>
                                <div className="space-y-2">
                                    <button
                                        onClick={() => setQuestionType('mcq')}
                                        className={`w-full p-4 rounded-xl border-2 text-left transition-all ${questionType === 'mcq'
                                            ? 'bg-blue-50 border-blue-500'
                                            : 'bg-white border-slate-200 hover:border-blue-300'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${questionType === 'mcq' ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                                                <CheckSquare size={20} />
                                            </div>
                                            <div>
                                                <h4 className={`font-bold text-sm ${questionType === 'mcq' ? 'text-blue-700' : 'text-slate-700'}`}>
                                                    Multiple Choice
                                                </h4>
                                                <p className="text-xs text-slate-500">4 options per question</p>
                                            </div>
                                            {questionType === 'mcq' && (
                                                <Check size={20} className="ml-auto text-blue-500" />
                                            )}
                                        </div>
                                    </button>

                                    <button
                                        onClick={() => setQuestionType('short')}
                                        className={`w-full p-4 rounded-xl border-2 text-left transition-all ${questionType === 'short'
                                            ? 'bg-amber-50 border-amber-500'
                                            : 'bg-white border-slate-200 hover:border-amber-300'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${questionType === 'short' ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                                                <MessageSquare size={20} />
                                            </div>
                                            <div>
                                                <h4 className={`font-bold text-sm ${questionType === 'short' ? 'text-amber-700' : 'text-slate-700'}`}>
                                                    Short Answer
                                                </h4>
                                                <p className="text-xs text-slate-500">AI validates your answers</p>
                                            </div>
                                            {questionType === 'short' && (
                                                <Check size={20} className="ml-auto text-amber-500" />
                                            )}
                                        </div>
                                    </button>
                                </div>
                            </div>

                            {/* Quick Select Ranges (Only for selection mode) */}
                            {requiresSelection && (
                                <div>
                                    <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
                                        <span className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center">3</span>
                                        Quick Select
                                    </h3>
                                    <div className="grid grid-cols-2 gap-2">
                                        {[
                                            { label: 'First 10', start: 1, end: 10 },
                                            { label: 'First 20', start: 1, end: 20 },
                                            { label: 'Last 10', start: Math.max(1, totalPages - 9), end: totalPages },
                                            { label: 'Last 20', start: Math.max(1, totalPages - 19), end: totalPages },
                                        ].map((range, i) => (
                                            <button
                                                key={i}
                                                onClick={() => selectRange(range.start, Math.min(range.end, totalPages))}
                                                className="px-3 py-2 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-600 hover:border-primary hover:text-primary transition-all"
                                            >
                                                {range.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Warning */}
                            {requiresSelection && selectedPages.size === maxPages && (
                                <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
                                    <AlertCircle size={14} />
                                    <span>Max {maxPages} pages reached</span>
                                </div>
                            )}
                        </div>

                        {/* Generate Button */}
                        <div className="p-6 border-t border-slate-200 bg-white">
                            <button
                                onClick={() => onConfirm(Array.from(selectedPages).sort((a, b) => a - b), questionType, numQuestions)}
                                disabled={selectedPages.size === 0}
                                className="w-full py-4 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold disabled:opacity-30 disabled:grayscale hover:shadow-xl transition-all flex items-center justify-center gap-2"
                            >
                                Generate {numQuestions} Questions
                                <ArrowRight size={18} />
                            </button>
                            <p className="text-center text-xs text-slate-400 mt-3">
                                From {selectedPages.size} selected pages • {questionType === 'mcq' ? 'Multiple Choice' : 'Short Answer'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
