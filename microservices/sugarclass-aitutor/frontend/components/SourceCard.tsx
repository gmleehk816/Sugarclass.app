import React, { useState } from 'react';
import { Source } from '../types';

interface SourceCardProps {
    source: Source;
}

const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
    const [expanded, setExpanded] = useState(false);

    // Helper to strip HTML tags for clean display
    const stripHtml = (html: string) => {
        const doc = new DOMParser().parseFromString(html, 'text/html');
        return doc.body.textContent || "";
    };

    const rawText = source.content_preview || source.text_preview || '';
    const text = stripHtml(rawText);
    const scorePercent = typeof source.score === 'number' ? Math.round(source.score * 100) : 0;

    return (
        <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-100 rounded-xl p-4 hover:shadow-md transition-all duration-200">
            <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#F43E01]/10 to-[#F43E01]/5 flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-[#F43E01]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <span className="text-xs font-semibold text-gray-700 truncate">{source.filename || 'Source'}</span>
                </div>
                <div className={`px-2 py-1 rounded-full text-[10px] font-bold ${scorePercent >= 80 ? 'bg-green-100 text-green-700' :
                    scorePercent >= 60 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-600'
                    }`}>
                    {scorePercent}%
                </div>
            </div>

            <p className={`text-xs text-gray-500 leading-relaxed ${expanded ? '' : 'line-clamp-3'}`}>
                {text}
            </p>

            {text.length > 150 && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-[10px] text-[#F43E01] font-semibold mt-2 hover:underline"
                >
                    {expanded ? 'Show less' : 'Show more'}
                </button>
            )}
        </div>
    );
};

export default SourceCard;
