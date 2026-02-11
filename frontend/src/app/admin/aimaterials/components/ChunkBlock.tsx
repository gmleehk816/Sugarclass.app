'use client';

import React, { useState } from 'react';
import { ArrowUp, ArrowDown, Trash, RefreshCw, Eye, Edit2, Loader2 } from 'lucide-react';
import type { ContentChunk } from '../lib/chunkParser';

// ===========================================================================
// ChunkBlock — Controlled editing for a single content chunk
// Replaces contentEditable with textarea + live preview toggle
// ===========================================================================

interface ChunkBlockProps {
    chunk: ContentChunk;
    index: number;
    totalChunks: number;
    onUpdate: (id: string, content: string) => void;
    onDelete: (id: string) => void;
    onMove: (id: string, direction: 'up' | 'down') => void;
    onRegenerate: (id: string) => void;
    isRegenerating?: boolean;
}

// Chunk type labels and accent colors
const CHUNK_META: Record<string, { label: string; color: string }> = {
    text: { label: 'Text', color: '#3b82f6' },
    heading: { label: 'Heading', color: '#f59e0b' },
    image: { label: 'Image', color: '#10b981' },
    video: { label: 'Video', color: '#8b5cf6' },
    list: { label: 'List', color: '#06b6d4' },
    quote: { label: 'Quote', color: '#ec4899' },
    callout: { label: 'Callout', color: '#f97316' },
    table: { label: 'Table', color: '#6366f1' },
};

const ChunkBlock: React.FC<ChunkBlockProps> = ({
    chunk, index, totalChunks, onUpdate, onDelete, onMove, onRegenerate, isRegenerating
}) => {
    const [editing, setEditing] = useState(false);
    const [localContent, setLocalContent] = useState(chunk.content);
    const meta = CHUNK_META[chunk.type] || CHUNK_META.text;

    // Is this a media chunk that shouldn't have a textarea editor?
    const isMedia = chunk.type === 'image' || chunk.type === 'video';

    // Commit edits back to parent
    const commitEdit = () => {
        onUpdate(chunk.id, localContent);
        setEditing(false);
    };

    // Cancel edits
    const cancelEdit = () => {
        setLocalContent(chunk.content);
        setEditing(false);
    };

    // Sync localContent when chunk.content changes externally (e.g., after regeneration)
    React.useEffect(() => {
        setLocalContent(chunk.content);
    }, [chunk.content]);

    return (
        <div style={{
            background: 'white',
            borderRadius: '12px',
            border: `1px solid ${editing ? meta.color : '#e2e8f0'}`,
            marginBottom: '10px',
            overflow: 'hidden',
            boxShadow: editing ? `0 0 0 2px ${meta.color}22` : '0 1px 3px rgba(0,0,0,0.05)',
            position: 'relative',
            transition: 'border-color 0.2s, box-shadow 0.2s',
        }}>
            {/* Regenerating overlay */}
            {isRegenerating && (
                <div style={{
                    position: 'absolute', inset: 0, background: 'rgba(255,255,255,0.85)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 10, borderRadius: '12px',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#7c3aed', fontWeight: 600 }}>
                        <Loader2 size={18} className="animate-spin" />
                        Regenerating…
                    </div>
                </div>
            )}

            {/* Action Bar */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 12px', background: '#f8fafc', borderBottom: '1px solid #f1f5f9',
            }}>
                {/* Left: type badge */}
                <div style={{
                    fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                    letterSpacing: '0.05em', color: meta.color,
                    display: 'flex', alignItems: 'center', gap: '6px',
                }}>
                    <span style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: meta.color, display: 'inline-block',
                    }} />
                    {meta.label}
                </div>

                {/* Right: action buttons */}
                <div style={{ display: 'flex', gap: '2px' }}>
                    {!isMedia && (
                        <button
                            type="button"
                            onClick={() => editing ? commitEdit() : setEditing(true)}
                            title={editing ? 'Preview' : 'Edit HTML'}
                            style={actionBtnStyle}
                        >
                            {editing ? <Eye size={14} /> : <Edit2 size={14} />}
                        </button>
                    )}
                    {(chunk.type === 'text' || chunk.type === 'heading' || chunk.type === 'list' || chunk.type === 'quote') && (
                        <button type="button" onClick={() => onRegenerate(chunk.id)} title="Regenerate chunk" style={{ ...actionBtnStyle, color: '#7c3aed' }}>
                            <RefreshCw size={14} />
                        </button>
                    )}
                    <button type="button" onClick={() => onMove(chunk.id, 'up')} disabled={index === 0} title="Move up" style={actionBtnStyle}>
                        <ArrowUp size={14} />
                    </button>
                    <button type="button" onClick={() => onMove(chunk.id, 'down')} disabled={index === totalChunks - 1} title="Move down" style={actionBtnStyle}>
                        <ArrowDown size={14} />
                    </button>
                    <button type="button" onClick={() => onDelete(chunk.id)} title="Delete chunk" style={{ ...actionBtnStyle, color: '#ef4444' }}>
                        <Trash size={14} />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            {editing ? (
                <div style={{ borderTop: '1px solid #e2e8f0' }}>
                    <textarea
                        value={localContent}
                        onChange={(e) => setLocalContent(e.target.value)}
                        style={{
                            width: '100%', minHeight: '120px', padding: '16px',
                            border: 'none', outline: 'none', resize: 'vertical',
                            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                            fontSize: '0.85rem', lineHeight: 1.6, color: '#334155',
                            background: '#fefce8',
                        }}
                    />
                    <div style={{
                        display: 'flex', gap: '8px', justifyContent: 'flex-end',
                        padding: '8px 12px', background: '#f8fafc', borderTop: '1px solid #e2e8f0',
                    }}>
                        <button type="button" onClick={cancelEdit} style={secondaryBtnStyle}>Cancel</button>
                        <button type="button" onClick={commitEdit} style={primaryBtnStyle}>Apply</button>
                    </div>
                </div>
            ) : (
                <div
                    dangerouslySetInnerHTML={{ __html: chunk.content }}
                    style={{
                        padding: '20px 24px', minHeight: '40px',
                        fontSize: chunk.type === 'heading' ? '1.3rem' : '1rem',
                        fontWeight: chunk.type === 'heading' ? 700 : 400,
                        lineHeight: 1.7, color: '#1e293b',
                    }}
                />
            )}
        </div>
    );
};

// Shared button styles
const actionBtnStyle: React.CSSProperties = {
    background: 'none', border: 'none', color: '#64748b',
    cursor: 'pointer', padding: '4px', borderRadius: '4px',
    display: 'flex', alignItems: 'center',
};

const primaryBtnStyle: React.CSSProperties = {
    padding: '6px 16px', borderRadius: '6px', border: 'none',
    background: '#2563eb', color: 'white', fontWeight: 600,
    fontSize: '0.8rem', cursor: 'pointer',
};

const secondaryBtnStyle: React.CSSProperties = {
    padding: '6px 16px', borderRadius: '6px', border: '1px solid #e2e8f0',
    background: 'white', color: '#64748b', fontWeight: 600,
    fontSize: '0.8rem', cursor: 'pointer',
};

export default ChunkBlock;
