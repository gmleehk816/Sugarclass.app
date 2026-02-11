'use client';

import React, { useState, useEffect } from 'react';
import {
    Save, RefreshCw, Maximize2, Minimize2, X as XIcon,
    Plus, Image as ImageIcon, Video, Type, Heading, Loader2,
} from 'lucide-react';
import { serviceFetch } from '@/lib/microservices';
import ChunkBlock from './ChunkBlock';
import { parseHtmlToChunks, chunksToHtml, type ContentChunk, type ChunkType } from '../lib/chunkParser';

// ===========================================================================
// Interfaces
// ===========================================================================

interface ResourceContent {
    id: number;
    subtopic_id: number;
    subtopic_name?: string;
    html_content: string;
    summary?: string;
    key_terms?: string;
}

interface RegenerateOptions {
    focus: string;
    temperature: number;
}

// ===========================================================================
// ChunkEditor — Full chunk-based content editor
// ===========================================================================

interface ChunkEditorProps {
    content: ResourceContent | null;
    onClose: () => void;
    onSave: (data: Partial<ResourceContent>) => Promise<void>;
}

const ChunkEditor: React.FC<ChunkEditorProps> = ({ content, onClose, onSave }) => {
    // ---- State ----
    const [formData, setFormData] = useState({
        summary: content?.summary || '',
        key_terms: content?.key_terms || ''
    });
    const [chunks, setChunks] = useState<ContentChunk[]>([]);
    const [isInitialized, setIsInitialized] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [fullScreen, setFullScreen] = useState(false);

    // Modal states
    const [showImageModal, setShowImageModal] = useState(false);
    const [showVideoModal, setShowVideoModal] = useState(false);
    const [showRegenerateModal, setShowRegenerateModal] = useState(false);
    const [insertAfterChunkId, setInsertAfterChunkId] = useState<string | null>(null);

    // Image modal
    const [imagePrompt, setImagePrompt] = useState('');
    const [generatingImage, setGeneratingImage] = useState(false);

    // Video modal
    const [videoUrl, setVideoUrl] = useState('');

    // Regeneration
    const [regeneratingChunkId, setRegeneratingChunkId] = useState<string | null>(null);
    const [chunkRegenerating, setChunkRegenerating] = useState(false);
    const [regenOptions, setRegenOptions] = useState<RegenerateOptions>({ focus: '', temperature: 0.7 });

    // ---- Initialize chunks ----
    useEffect(() => {
        if (content?.html_content && !isInitialized) {
            setChunks(parseHtmlToChunks(content.html_content));
            setIsInitialized(true);
        }
    }, [content, isInitialized]);

    // ---- Chunk operations ----
    const updateChunk = (id: string, newContent: string) => {
        setChunks(prev => prev.map(c => c.id === id ? { ...c, content: newContent } : c));
    };

    const deleteChunk = (id: string) => {
        if (confirm('Delete this chunk?')) {
            setChunks(prev => prev.filter(c => c.id !== id));
        }
    };

    const moveChunk = (id: string, direction: 'up' | 'down') => {
        setChunks(prev => {
            const index = prev.findIndex(c => c.id === id);
            if (index < 0) return prev;
            const newIndex = direction === 'up' ? index - 1 : index + 1;
            if (newIndex < 0 || newIndex >= prev.length) return prev;
            const next = [...prev];
            [next[index], next[newIndex]] = [next[newIndex], next[index]];
            return next;
        });
    };

    const addChunkAt = (type: ChunkType, afterId: string | null, html: string) => {
        const id = `ck_new_${Date.now().toString(36)}`;
        const newChunk: ContentChunk = { id, type, content: html };
        setChunks(prev => {
            if (!afterId) return [newChunk, ...prev];
            const idx = prev.findIndex(c => c.id === afterId);
            const copy = [...prev];
            copy.splice(idx + 1, 0, newChunk);
            return copy;
        });
    };

    // ---- Save ----
    const handleSubmit = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        setSaving(true);
        setError('');
        try {
            await onSave({ ...formData, html_content: chunksToHtml(chunks) });
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to save content');
        } finally {
            setSaving(false);
        }
    };

    // ---- Regeneration ----
    const handleRegenerateChunk = (chunkId: string) => {
        setRegeneratingChunkId(chunkId);
        setShowRegenerateModal(true);
    };

    const confirmRegenerate = async () => {
        if (!regeneratingChunkId) return;
        const chunk = chunks.find(c => c.id === regeneratingChunkId);
        if (!chunk) return;

        // Build surrounding context (prev/next chunk text for coherence)
        const chunkIndex = chunks.findIndex(c => c.id === regeneratingChunkId);
        const prevChunk = chunkIndex > 0 ? chunks[chunkIndex - 1] : null;
        const nextChunk = chunkIndex < chunks.length - 1 ? chunks[chunkIndex + 1] : null;

        setChunkRegenerating(true);
        setShowRegenerateModal(false);
        setError('');

        try {
            const result = await serviceFetch('aimaterials', '/api/admin/contents/regenerate-chunk', {
                method: 'POST',
                body: JSON.stringify({
                    content: chunk.content,
                    type: chunk.type,
                    focus: regenOptions.focus || undefined,
                    temperature: regenOptions.temperature,
                    subtopic_name: content?.subtopic_name || '',
                    surrounding_context: {
                        before: prevChunk?.content || '',
                        after: nextChunk?.content || '',
                    },
                }),
            });

            if (result.success && result.content) {
                updateChunk(regeneratingChunkId, result.content);
            } else {
                setError('Regeneration returned no content');
            }
        } catch (err: any) {
            setError('Regeneration failed: ' + err.message);
        } finally {
            setChunkRegenerating(false);
            setRegeneratingChunkId(null);
        }
    };

    // ---- Image insertion ----
    const handleInsertImage = async () => {
        if (!imagePrompt.trim()) return;
        setGeneratingImage(true);
        try {
            const result = await serviceFetch('aimaterials', '/api/admin/generate-content-image', {
                method: 'POST',
                body: JSON.stringify({ prompt: imagePrompt }),
            });
            if (result.success && result.image_url) {
                let finalUrl = result.image_url;
                if (!finalUrl.startsWith('http')) {
                    const baseUrl = typeof window !== 'undefined' && !window.location.hostname.includes('localhost')
                        ? '/services/aimaterials' : 'http://localhost:8004';
                    finalUrl = `${baseUrl}${result.image_url}`;
                }
                const imgHtml = `<figure style="text-align:center;margin:20px 0;"><img src="${finalUrl}" alt="${imagePrompt}" style="max-width:100%;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);"/><figcaption style="margin-top:8px;font-size:0.85rem;color:#64748b;font-style:italic;">${imagePrompt}</figcaption></figure>`;
                addChunkAt('image', insertAfterChunkId, imgHtml);
                setShowImageModal(false);
                setImagePrompt('');
            }
        } catch (err: any) {
            setError('Image generation failed: ' + err.message);
        } finally {
            setGeneratingImage(false);
        }
    };

    // ---- Video insertion ----
    const handleInsertVideo = () => {
        if (!videoUrl.trim()) return;
        const ytMatch = videoUrl.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
        let videoHtml: string;
        if (ytMatch) {
            const ytId = ytMatch[1];
            videoHtml = `<div style="margin:20px 0;border-radius:16px;overflow:hidden;position:relative;padding-bottom:56.25%;height:0;"><iframe src="https://www.youtube.com/embed/${ytId}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;" allowfullscreen></iframe></div>`;
        } else {
            videoHtml = `<div style="margin:20px 0;padding:24px;background:#f1f5f9;border-radius:12px;text-align:center;"><p>Video: ${videoUrl}</p></div>`;
        }
        addChunkAt('video', insertAfterChunkId, videoHtml);
        setShowVideoModal(false);
        setVideoUrl('');
    };

    // ---- Add Between UI ----
    const AddBetween = ({ afterId }: { afterId: string | null }) => (
        <div style={{
            height: '10px', position: 'relative', display: 'flex', justifyContent: 'center',
            alignItems: 'center', margin: '6px 0', opacity: 0.08, transition: 'opacity 0.2s',
        }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.08')}
        >
            <div style={{ height: '2px', background: '#cbd5e1', width: '100%', position: 'absolute' }} />
            <div style={{ display: 'flex', gap: '6px', zIndex: 10, background: '#f1f5f9', padding: '0 8px' }}>
                <AddBtn label="Text" color="#3b82f6" onClick={() => addChunkAt('text', afterId, '<p>New paragraph…</p>')} />
                <AddBtn label="Heading" color="#f59e0b" onClick={() => addChunkAt('heading', afterId, '<h2>New Heading</h2>')} />
                <AddBtn label="Photo" color="#10b981" onClick={() => { setInsertAfterChunkId(afterId); setShowImageModal(true); }} />
                <AddBtn label="Video" color="#8b5cf6" onClick={() => { setInsertAfterChunkId(afterId); setShowVideoModal(true); }} />
            </div>
        </div>
    );

    // ---- Focus options for regeneration ----
    const focusOptions = [
        { value: '', label: 'Standard (balanced)' },
        { value: 'more creative', label: 'More Creative & Engaging' },
        { value: 'simpler', label: 'Simpler & More Concise' },
        { value: 'focus on examples', label: 'Focus on Real-World Examples' },
        { value: 'focus on visual learning', label: 'Focus on Visual Learning' },
        { value: 'more detailed', label: 'More Detailed & Comprehensive' },
    ];

    // ==== RENDER ====
    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000, padding: fullScreen ? '0' : '20px',
        }}>
            <div style={{
                background: '#f8fafc', borderRadius: fullScreen ? '0' : '16px',
                width: '100%', maxWidth: fullScreen ? '100%' : '1100px',
                height: fullScreen ? '100%' : '90vh', display: 'flex', flexDirection: 'column',
                overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
            }}>
                {/* ---- Header ---- */}
                <div style={{ padding: '14px 24px', background: 'white', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
                            Chunk Editor: {content?.subtopic_name}
                        </h2>
                        <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                            {chunks.length} chunk{chunks.length !== 1 ? 's' : ''} — edit individually or regenerate with AI
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button type="button" onClick={() => setFullScreen(!fullScreen)} style={iconBtnStyle}>
                            {fullScreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                        </button>
                        <button type="button" onClick={onClose} style={iconBtnStyle}>
                            <XIcon size={20} />
                        </button>
                    </div>
                </div>

                {/* ---- Body ---- */}
                <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                    {/* Main chunk list */}
                    <div style={{ flex: 1, overflowY: 'auto', padding: '20px', background: '#f1f5f9' }}>
                        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                            <AddBetween afterId={null} />

                            {chunks.map((chunk, index) => (
                                <div key={chunk.id}>
                                    <ChunkBlock
                                        chunk={chunk}
                                        index={index}
                                        totalChunks={chunks.length}
                                        onUpdate={updateChunk}
                                        onDelete={deleteChunk}
                                        onMove={moveChunk}
                                        onRegenerate={handleRegenerateChunk}
                                        isRegenerating={chunkRegenerating && regeneratingChunkId === chunk.id}
                                    />
                                    <AddBetween afterId={chunk.id} />
                                </div>
                            ))}

                            {chunks.length === 0 && (
                                <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
                                    <Type size={32} style={{ marginBottom: '12px' }} />
                                    <p style={{ fontWeight: 600 }}>No content chunks yet</p>
                                    <p style={{ fontSize: '0.85rem' }}>Use the + buttons above to add content</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div style={{ width: '280px', background: 'white', borderLeft: '1px solid #e2e8f0', padding: '20px', overflowY: 'auto' }}>
                        <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Subtopic Options
                        </h3>

                        <div style={{ marginBottom: '18px' }}>
                            <label style={labelStyle}>Summary</label>
                            <textarea
                                value={formData.summary}
                                onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                                style={{ ...inputStyle, minHeight: '90px' }}
                            />
                        </div>

                        <div style={{ marginBottom: '18px' }}>
                            <label style={labelStyle}>Key Terms</label>
                            <textarea
                                value={formData.key_terms}
                                onChange={(e) => setFormData({ ...formData, key_terms: e.target.value })}
                                style={{ ...inputStyle, minHeight: '90px' }}
                            />
                        </div>

                        {error && (
                            <div style={{ padding: '10px', background: '#fee2e2', color: '#ef4444', borderRadius: '8px', fontSize: '0.8rem', marginBottom: '12px' }}>
                                {error}
                            </div>
                        )}
                    </div>
                </div>

                {/* ---- Footer ---- */}
                <div style={{ padding: '14px 24px', background: 'white', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                    <button type="button" onClick={onClose} style={{ padding: '8px 20px', borderRadius: '8px', border: '1px solid #e2e8f0', background: 'white', fontWeight: 600, cursor: 'pointer' }}>
                        Discard
                    </button>
                    <button
                        type="button" onClick={() => handleSubmit()} disabled={saving}
                        style={{ padding: '8px 24px', borderRadius: '8px', background: '#2563eb', color: 'white', border: 'none', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                        {saving ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
                        {saving ? 'Saving…' : 'Save All Changes'}
                    </button>
                </div>
            </div>

            {/* ---- Image Modal ---- */}
            {showImageModal && (
                <ModalOverlay>
                    <div style={modalBoxStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '1.1rem' }}>Generate Image Chunk</h3>
                        <textarea
                            placeholder="Describe the image…"
                            value={imagePrompt}
                            onChange={(e) => setImagePrompt(e.target.value)}
                            style={{ ...inputStyle, minHeight: '80px', marginBottom: '16px' }}
                        />
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                            <button type="button" onClick={() => setShowImageModal(false)} style={secondaryBtnStyle}>Cancel</button>
                            <button type="button" onClick={handleInsertImage} disabled={generatingImage || !imagePrompt} style={{ ...primaryBtnStyle, background: '#10b981' }}>
                                {generatingImage ? 'Generating…' : 'Generate & Insert'}
                            </button>
                        </div>
                    </div>
                </ModalOverlay>
            )}

            {/* ---- Video Modal ---- */}
            {showVideoModal && (
                <ModalOverlay>
                    <div style={modalBoxStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '1.1rem' }}>Insert Video Chunk</h3>
                        <input
                            type="text" placeholder="YouTube or Video URL…"
                            value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)}
                            style={{ ...inputStyle, marginBottom: '16px' }}
                        />
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                            <button type="button" onClick={() => setShowVideoModal(false)} style={secondaryBtnStyle}>Cancel</button>
                            <button type="button" onClick={handleInsertVideo} disabled={!videoUrl} style={{ ...primaryBtnStyle, background: '#8b5cf6' }}>Insert</button>
                        </div>
                    </div>
                </ModalOverlay>
            )}

            {/* ---- Regeneration Options Modal ---- */}
            {showRegenerateModal && (
                <ModalOverlay>
                    <div style={{ ...modalBoxStyle, maxWidth: '480px' }}>
                        <h3 style={{ margin: '0 0 20px', fontSize: '1.2rem', fontWeight: 700 }}>Regenerate Chunk</h3>

                        <div style={{ marginBottom: '16px' }}>
                            <label style={labelStyle}>Enhancement Focus</label>
                            <select
                                value={regenOptions.focus}
                                onChange={(e) => setRegenOptions({ ...regenOptions, focus: e.target.value })}
                                style={{ ...inputStyle, cursor: 'pointer' }}
                            >
                                {focusOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={labelStyle}>Creativity: {regenOptions.temperature.toFixed(1)}</label>
                            <input
                                type="range" min="0" max="1" step="0.1"
                                value={regenOptions.temperature}
                                onChange={(e) => setRegenOptions({ ...regenOptions, temperature: parseFloat(e.target.value) })}
                                style={{ width: '100%' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', marginTop: '2px' }}>
                                <span>Conservative</span><span>Balanced</span><span>Creative</span>
                            </div>
                        </div>

                        <div style={{ padding: '10px 12px', background: '#eff6ff', borderRadius: '8px', fontSize: '0.82rem', color: '#1e40af', borderLeft: '3px solid #3b82f6', marginBottom: '16px' }}>
                            AI will enhance this chunk while preserving its context in the surrounding content.
                        </div>

                        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                            <button type="button" onClick={() => setShowRegenerateModal(false)} style={secondaryBtnStyle}>Cancel</button>
                            <button type="button" onClick={confirmRegenerate} style={{ ...primaryBtnStyle, background: '#7c3aed' }}>
                                <RefreshCw size={14} /> Regenerate
                            </button>
                        </div>
                    </div>
                </ModalOverlay>
            )}
        </div>
    );
};

// ===========================================================================
// Shared UI helpers
// ===========================================================================

const ModalOverlay: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1100,
    }}>
        {children}
    </div>
);

const AddBtn = ({ label, color, onClick }: { label: string; color: string; onClick: () => void }) => (
    <button type="button" onClick={onClick} style={{
        padding: '2px 8px', borderRadius: '4px', background: color, color: 'white',
        border: 'none', fontSize: '0.68rem', cursor: 'pointer', fontWeight: 600,
    }}>
        + {label}
    </button>
);

const iconBtnStyle: React.CSSProperties = {
    background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px',
};

const inputStyle: React.CSSProperties = {
    width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0',
    borderRadius: '8px', fontSize: '0.88rem', fontFamily: 'inherit',
};

const labelStyle: React.CSSProperties = {
    display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#64748b', marginBottom: '6px',
};

const modalBoxStyle: React.CSSProperties = {
    background: 'white', padding: '24px', borderRadius: '16px', width: '100%', maxWidth: '420px',
};

const primaryBtnStyle: React.CSSProperties = {
    padding: '8px 20px', borderRadius: '8px', border: 'none', background: '#2563eb',
    color: 'white', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
};

const secondaryBtnStyle: React.CSSProperties = {
    padding: '8px 16px', borderRadius: '8px', border: '1px solid #e2e8f0',
    background: 'white', color: '#64748b', fontWeight: 600, cursor: 'pointer',
};

export default ChunkEditor;
