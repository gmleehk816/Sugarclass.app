"use client";

import React, { useState, useEffect } from 'react';
import { serviceFetch } from '@/lib/microservices';
import {
    Zap,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Clock,
    ChevronRight,
    ChevronDown,
    Folder,
    FolderOpen,
    FileText,
    Database,
    BookOpen,
    Layers,
    HelpCircle,
    Image as ImageIcon,
    Edit,
    Sparkles,
    Loader2,
    AlertCircle,
    Play,
    BarChart3,
    Eye,
    Terminal,
    Info
} from "lucide-react";

// ===========================================================================
// V8 INTERFACES
// ===========================================================================

interface V8SubtopicStatus {
    subtopic_id: string;
    has_concepts: boolean;
    concept_count: number;
    svg_count: number;
    quiz_count: number;
    flashcard_count: number;
    reallife_image_count: number;
    processed_at: string | null;
}

interface V8Topic {
    id: string;
    topic_id: string;
    name: string;
    order_num: number;
    subtopic_count: number;
    processed_count: number;
}

interface V8Subtopic {
    id: string;
    subtopic_id: string;
    name: string;
    order_num: number;
    processed_at: string | null;
    v8_concepts_count: number;
}

interface V8Concept {
    id: number;
    concept_key: string;
    title: string;
    description: string;
    icon: string;
    order_num: number;
    generated?: {
        svg?: string;
        bullets?: string;
    };
}

interface V8FullSubtopic {
    id: string;
    subtopic_id: string;
    name: string;
    concepts: V8Concept[];
    quiz: any[];
    flashcards: any[];
    reallife_images: any[];
    learning_objectives: any[];
    key_terms: any[];
    formulas: any[];
}

interface V8Task {
    task_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    message: string;
    error?: string;
    started_at?: string;
    completed_at?: string;
    logs?: { log_level: string; message: string; created_at: string }[];
}

// ===========================================================================
// STYLES & DESIGN TOKENS
// ================================================= design tokens match globals.css
const designTokens = {
    primary: '#1e293b', // Slate 800
    primaryLight: '#334155', // Slate 700
    primaryMuted: 'rgba(30, 41, 59, 0.05)',
    accent: '#927559', // Bronze
    accentLight: '#a48c73',
    accentMuted: 'rgba(146, 117, 89, 0.1)',
    background: '#fcfaf7', // Ivory
    cardBg: 'rgba(255, 255, 255, 0.85)',
    cardBorder: 'rgba(0, 0, 0, 0.04)',
    success: '#3d5a45', // Forest Sage
    shadowSm: '0 2px 4px rgba(0, 0, 0, 0.02)',
    shadowMd: '0 10px 25px -5px rgba(0, 0, 0, 0.04)',
    shadowLg: '0 20px 50px -12px rgba(0, 0, 0, 0.08)',
    shadowGlass: '0 8px 32px 0 rgba(31, 38, 135, 0.05)',
    radiusXl: '32px',
    radiusLg: '24px',
    radiusMd: '16px',
    radiusSm: '8px',
    fontFamily: "'Outfit', sans-serif",
    transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)'
};

const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    border: `1px solid ${designTokens.cardBorder}`,
    borderRadius: designTokens.radiusMd,
    fontSize: '0.95rem',
    fontFamily: designTokens.fontFamily,
    background: 'white',
    boxShadow: designTokens.shadowSm,
    transition: designTokens.transition,
};

const cardStyle = (isMobile?: boolean) => ({
    background: designTokens.cardBg,
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    padding: isMobile ? '20px' : '32px',
    borderRadius: designTokens.radiusLg,
    border: `1px solid ${designTokens.cardBorder}`,
    boxShadow: designTokens.shadowMd,
    transition: designTokens.transition,
});

const buttonPrimary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 24px',
    borderRadius: designTokens.radiusMd,
    background: designTokens.primary,
    color: 'white',
    border: 'none',
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(30, 41, 59, 0.15)',
    transition: designTokens.transition,
    fontFamily: designTokens.fontFamily,
    letterSpacing: '-0.01em',
};

const buttonSecondary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 24px',
    borderRadius: designTokens.radiusMd,
    background: 'white',
    color: designTokens.primary,
    border: `1px solid ${designTokens.cardBorder}`,
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
    boxShadow: designTokens.shadowSm,
    transition: designTokens.transition,
    fontFamily: designTokens.fontFamily,
};

// ===========================================================================
// V8 GENERATE OPTIONS INTERFACE
// ===========================================================================

interface V8GenerateOptions {
    generate_concepts: boolean;
    generate_svgs: boolean;
    generate_quiz: boolean;
    generate_flashcards: boolean;
    generate_images: boolean;
    force_regenerate: boolean;
    apply_to_full_topic: boolean;
    custom_prompt: string;
}

// ===========================================================================
// V8 GENERATE MODAL COMPONENT
// ===========================================================================

const V8GenerateModal = ({
    options,
    setOptions,
    onConfirm,
    onClose,
    generating,
    subtopicName,
    isMobile
}: {
    options: V8GenerateOptions;
    setOptions: (options: V8GenerateOptions) => void;
    onConfirm: () => void;
    onClose: () => void;
    generating: boolean;
    subtopicName?: string;
    isMobile: boolean;
}) => {
    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
            fontFamily: designTokens.fontFamily
        }}>
            <div style={{
                background: 'white',
                padding: isMobile ? '24px' : '48px',
                borderRadius: designTokens.radiusXl,
                width: '100%',
                maxWidth: '640px',
                boxShadow: designTokens.shadowLg,
                position: 'relative',
                border: `1px solid ${designTokens.cardBorder}`,
                animation: 'fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
            }}>
                {/* Close Button */}
                <button
                    onClick={onClose}
                    disabled={generating}
                    style={{
                        position: 'absolute',
                        top: '24px',
                        right: '24px',
                        background: designTokens.primaryMuted,
                        border: 'none',
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: generating ? 'not-allowed' : 'pointer',
                        color: designTokens.primary,
                        transition: designTokens.transition
                    }}
                >
                    <XCircle size={20} />
                </button>

                <div style={{ marginBottom: '32px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                        <div style={{ background: designTokens.accentMuted, padding: '12px', borderRadius: '16px' }}>
                            <Sparkles size={28} color={designTokens.accent} />
                        </div>
                        <h2 style={{ fontSize: '2rem', fontWeight: 800, margin: 0, color: designTokens.primary, letterSpacing: '-0.03em' }}>
                            Task Configuration
                        </h2>
                    </div>
                    <p style={{ color: designTokens.primaryLight, opacity: 0.7, fontSize: '0.95rem', lineHeight: 1.6, margin: 0 }}>
                        {subtopicName ? (
                            <>Synthesizing V8 content for <strong style={{ color: designTokens.primary }}>{subtopicName}</strong> using advanced LLM pipelines.</>
                        ) : 'Initialize the V8 generation pipeline for this educational module.'}
                    </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '32px' }}>
                    {[
                        { key: 'generate_concepts', label: 'Interactive Concepts', icon: <Layers size={18} /> },
                        { key: 'generate_svgs', label: 'SVG Architecture', icon: <ImageIcon size={18} /> },
                        { key: 'generate_quiz', label: 'Assessment Engine', icon: <HelpCircle size={18} /> },
                        { key: 'generate_flashcards', label: 'Active Recall Sets', icon: <FileText size={18} /> },
                        { key: 'generate_images', label: 'Visual Context', icon: <ImageIcon size={18} /> },
                        { key: 'force_regenerate', label: 'Deep Regeneration', icon: <RefreshCw size={18} />, color: designTokens.accent }
                    ].map((opt) => (
                        <label
                            key={opt.key}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                padding: '16px',
                                borderRadius: designTokens.radiusMd,
                                background: (options as any)[opt.key] ? designTokens.primaryMuted : '#fcfaf7',
                                border: `2px solid ${(options as any)[opt.key] ? designTokens.accent : 'rgba(0,0,0,0.03)'}`,
                                cursor: 'pointer',
                                transition: designTokens.transition,
                                opacity: generating ? 0.6 : 1
                            }}
                        >
                            <input
                                type="checkbox"
                                checked={(options as any)[opt.key]}
                                disabled={generating}
                                onChange={(e) => setOptions({ ...options, [opt.key]: e.target.checked })}
                                style={{
                                    width: '20px',
                                    height: '20px',
                                    accentColor: designTokens.primary,
                                    cursor: 'pointer'
                                }}
                            />
                            <div style={{ color: (options as any)[opt.key] ? designTokens.primary : designTokens.primaryLight, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ opacity: 0.7 }}>{opt.icon}</div>
                                <span style={{ fontSize: '0.85rem', fontWeight: (options as any)[opt.key] ? 800 : 600 }}>{opt.label}</span>
                            </div>
                        </label>
                    ))}
                </div>

                <div style={{ marginBottom: '32px' }}>
                    <label style={{ display: 'block', marginBottom: '12px', fontSize: '0.85rem', fontWeight: 800, color: designTokens.primary, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Synthesis Directives
                    </label>
                    <textarea
                        value={options.custom_prompt}
                        onChange={(e) => setOptions({ ...options, custom_prompt: e.target.value })}
                        placeholder="Define custom constraints or focus areas for the AI..."
                        disabled={generating}
                        style={{
                            ...inputStyle,
                            height: '120px',
                            resize: 'none',
                            fontSize: '0.9rem',
                            lineHeight: 1.6
                        }}
                    />
                </div>

                <div style={{ display: 'flex', gap: '16px' }}>
                    <button
                        onClick={onClose}
                        disabled={generating}
                        style={{ ...buttonSecondary, flex: 1, justifyContent: 'center', padding: '16px' }}
                    >
                        Decline
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={generating}
                        style={{
                            ...buttonPrimary,
                            flex: 1,
                            justifyContent: 'center',
                            padding: '16px',
                            background: designTokens.accent,
                            boxShadow: `0 12px 24px -6px ${designTokens.accentMuted}`
                        }}
                    >
                        {generating ? <Loader2 size={20} className="animate-spin" /> : 'Execute Pipeline'}
                    </button>
                </div>
            </div>
        </div>
    );
};

// ===========================================================================
// V8 CONTENT BROWSER COMPONENT
// ===========================================================================

const V8ContentBrowser = ({
    subjects: propSubjects,
    loadingSubjects: propLoadingSubjects,
    onRefresh,
    isMobile,
    isTablet
}: {
    subjects: any[];
    loadingSubjects: boolean;
    onRefresh: () => void;
    isMobile: boolean;
    isTablet: boolean;
}) => {
    const [expandedSubjects, setExpandedSubjects] = useState<Record<string, boolean>>({});
    const [expandedTopics, setExpandedTopics] = useState<Record<string, boolean>>({});

    // Use internal state for V8 subjects (fetched from V8 API)
    const [subjects, setSubjects] = useState<any[]>(propSubjects || []);
    const [loadingSubjects, setLoadingSubjects] = useState(propLoadingSubjects);
    const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
    const [topics, setTopics] = useState<V8Topic[]>([]);
    const [loadingTopics, setLoadingTopics] = useState(false);
    const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
    const [subtopics, setSubtopics] = useState<V8Subtopic[]>([]);
    const [loadingSubtopics, setLoadingSubtopics] = useState(false);
    const [selectedSubtopicId, setSelectedSubtopicId] = useState<string | null>(null);
    const [subtopicStatus, setSubtopicStatus] = useState<V8SubtopicStatus | null>(null);
    const [fullSubtopic, setFullSubtopic] = useState<V8FullSubtopic | null>(null);
    const [loadingContent, setLoadingContent] = useState(false);

    // Generation state
    const [generating, setGenerating] = useState(false);
    const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<V8Task | null>(null);
    const [showLogs, setShowLogs] = useState(true);
    const [showGenerateModal, setShowGenerateModal] = useState(false);
    const [generateOptions, setGenerateOptions] = useState({
        generate_concepts: true,
        generate_svgs: true,
        generate_quiz: true,
        generate_flashcards: true,
        generate_images: false,
        force_regenerate: false,
        apply_to_full_topic: false,
        custom_prompt: '',
    });

    const [viewMode, setViewMode] = useState<'topic-overview' | 'subtopic-detail'>('topic-overview');

    // Fetch V8 subjects on mount
    useEffect(() => {
        loadSubjects();
    }, []);

    const toggleSubject = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setExpandedSubjects(prev => ({ ...prev, [id]: !prev[id] }));
        if (selectedSubjectId !== id) {
            setSelectedSubjectId(id);
        }
    };

    const toggleTopic = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setExpandedTopics(prev => ({ ...prev, [id]: !prev[id] }));
        if (selectedTopicId !== id) {
            setSelectedTopicId(id);
        }
    };

    // Auto-expand and load when subject/topic is selected via polling or initial load
    useEffect(() => {
        if (selectedSubjectId) {
            setExpandedSubjects(prev => ({ ...prev, [selectedSubjectId]: true }));
            loadTopics(selectedSubjectId);
        }
    }, [selectedSubjectId]);

    useEffect(() => {
        if (selectedTopicId) {
            setExpandedTopics(prev => ({ ...prev, [selectedTopicId]: true }));
            loadSubtopics(selectedTopicId);
            setViewMode('topic-overview');
            setSelectedSubtopicId(null); // Reset when changing topic
        }
    }, [selectedTopicId]);

    // Load content when subtopic is selected
    useEffect(() => {
        if (selectedSubtopicId) {
            loadSubtopicContent(selectedSubtopicId);
            setViewMode('subtopic-detail');
        } else {
            setSubtopicStatus(null);
            setFullSubtopic(null);
        }
    }, [selectedSubtopicId]);

    // Poll task status when generating
    useEffect(() => {
        if (!currentTaskId) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await serviceFetch('aimaterials', `/api/admin/v8/tasks/${currentTaskId}`);
                setTaskStatus(data);

                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(pollInterval);
                    setGenerating(false);

                    if (data.status === 'completed') {
                        // Refresh subtopic content
                        loadSubtopicContent(selectedSubtopicId!);
                        loadSubtopics(selectedTopicId!);
                    }
                }
            } catch (err) {
                console.error('Error polling task status', err);
            }
        }, 2000);

        return () => clearInterval(pollInterval);
    }, [currentTaskId, selectedSubtopicId, selectedTopicId]);

    const loadSubjects = async () => {
        setLoadingSubjects(true);
        try {
            const data = await serviceFetch('aimaterials', '/api/admin/v8/subjects');
            setSubjects(data.subjects || []);
            // Auto-select and expand first subject if available
            if (data.subjects && data.subjects.length > 0) {
                const firstId = data.subjects[0].id;
                setSelectedSubjectId(firstId);
                setExpandedSubjects({ [firstId]: true });
            }
        } catch (err) {
            console.error('Error loading subjects', err);
            if (propSubjects && propSubjects.length > 0) setSubjects(propSubjects);
        } finally {
            setLoadingSubjects(false);
        }
    };

    const loadTopics = async (subjectId: string) => {
        setLoadingTopics(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/v8/subjects/${subjectId}/topics`);
            setTopics(data.topics || []);
        } catch (err) {
            console.error('Error loading topics', err);
            setTopics([]);
        } finally {
            setLoadingTopics(false);
        }
    };

    const loadSubtopics = async (topicId: string) => {
        setLoadingSubtopics(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/v8/topics/${topicId}/subtopics?include_status=true`);
            setSubtopics(data.subtopics || []);
        } catch (err) {
            console.error('Error loading subtopics', err);
            setSubtopics([]);
        } finally {
            setLoadingSubtopics(false);
        }
    };

    const loadSubtopicContent = async (subtopicId: string) => {
        setLoadingContent(true);
        try {
            const statusData = await serviceFetch('aimaterials', `/api/admin/v8/subtopics/${subtopicId}/status`);
            setSubtopicStatus(statusData);

            if (statusData.has_concepts) {
                const fullData = await serviceFetch('aimaterials', `/api/admin/v8/subtopics/${subtopicId}`);
                setFullSubtopic(fullData);
            } else {
                setFullSubtopic(null);
            }
        } catch (err) {
            console.error('Error loading subtopic content', err);
            setSubtopicStatus(null);
            setFullSubtopic(null);
        } finally {
            setLoadingContent(false);
        }
    };

    const handleGenerateV8 = async (forceRegenerate = false) => {
        if (!selectedSubtopicId) return;

        setGenerating(true);
        setTaskStatus(null);
        setShowLogs(true);
        setShowGenerateModal(false);

        try {
            const data = await serviceFetch('aimaterials', `/api/admin/v8/subtopics/${selectedSubtopicId}/generate`, {
                method: 'POST',
                body: JSON.stringify({
                    force_regenerate: forceRegenerate || generateOptions.force_regenerate,
                    generate_svgs: generateOptions.generate_svgs,
                    generate_quiz: generateOptions.generate_quiz,
                    generate_flashcards: generateOptions.generate_flashcards,
                    generate_images: generateOptions.generate_images,
                    custom_prompt: generateOptions.custom_prompt || undefined,
                }),
            });

            if (data.task_id) {
                setCurrentTaskId(data.task_id);
            } else if (data.status === 'already_generated') {
                setTaskStatus({
                    task_id: '',
                    status: 'completed',
                    progress: 100,
                    message: data.message || 'V8 content already exists',
                    logs: []
                });
                setGenerating(false);
                loadSubtopicContent(selectedSubtopicId);
            } else {
                setGenerating(false);
            }
        } catch (err) {
            console.error('Error starting V8 generation', err);
            setGenerating(false);
        }
    };

    const openGenerateModal = (forceRegenerate = false) => {
        setGenerateOptions(prev => ({ ...prev, force_regenerate: forceRegenerate }));
        setShowGenerateModal(true);
    };

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: isTablet ? '1fr' : '300px 1fr 350px',
            gap: '32px',
            minHeight: '800px',
            fontFamily: designTokens.fontFamily
        }}>
            {/* Hierarchical Navigation Sidebar (Left) */}
            <div style={{
                ...cardStyle(isMobile),
                display: 'flex',
                gap: '12px',
                flexDirection: 'column',
                maxHeight: '900px',
                overflow: 'hidden',
                padding: '24px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', paddingBottom: '16px', borderBottom: `1px solid ${designTokens.primaryMuted}` }}>
                    <div style={{ background: designTokens.accentMuted, padding: '8px', borderRadius: '10px' }}>
                        <Layers size={20} color={designTokens.accent} />
                    </div>
                    <div>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: designTokens.primary, letterSpacing: '-0.02em' }}>Content Explorer</h3>
                        <div style={{ fontSize: '0.7rem', color: designTokens.accent, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '2px' }}>V8 Architecture</div>
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }} className="custom-scrollbar">
                    {loadingSubjects ? (
                        <div style={{ padding: '40px', textAlign: 'center', color: designTokens.primaryLight }}>
                            <Loader2 size={32} className="animate-spin" />
                        </div>
                    ) : subjects.length === 0 ? (
                        <div style={{ padding: '40px', textAlign: 'center', color: designTokens.primaryLight, opacity: 0.6, fontSize: '0.9rem' }}>
                            No courses found in database.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {subjects.map((subject: any) => (
                                <div key={subject.id} style={{ marginBottom: '6px' }}>
                                    {/* Subject Row */}
                                    <button
                                        onClick={(e) => toggleSubject(subject.id, e)}
                                        style={{
                                            width: '100%',
                                            padding: '12px 16px',
                                            borderRadius: designTokens.radiusMd,
                                            border: 'none',
                                            background: selectedSubjectId === subject.id ? designTokens.accentMuted : 'transparent',
                                            cursor: 'pointer',
                                            textAlign: 'left',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px',
                                            transition: designTokens.transition,
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.background = selectedSubjectId === subject.id ? designTokens.accentMuted : designTokens.primaryMuted }}
                                        onMouseLeave={(e) => { e.currentTarget.style.background = selectedSubjectId === subject.id ? designTokens.accentMuted : 'transparent' }}
                                    >
                                        <div style={{ opacity: 0.5, color: designTokens.primary }}>
                                            {expandedSubjects[subject.id] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                        </div>
                                        <BookOpen size={18} color={selectedSubjectId === subject.id ? designTokens.accent : designTokens.primaryLight} />
                                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: selectedSubjectId === subject.id ? designTokens.primary : designTokens.primaryLight, flex: 1, letterSpacing: '-0.01em' }}>
                                            {subject.name}
                                        </span>
                                        <div style={{
                                            fontSize: '0.7rem',
                                            fontWeight: 800,
                                            color: designTokens.accent,
                                            background: designTokens.accentMuted,
                                            padding: '2px 8px',
                                            borderRadius: '20px'
                                        }}>
                                            {subject.topic_count || 0}
                                        </div>
                                    </button>

                                    {/* Topics List */}
                                    {expandedSubjects[subject.id] && (
                                        <div style={{
                                            paddingLeft: '24px',
                                            marginTop: '6px',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            gap: '4px',
                                            borderLeft: `2px solid ${designTokens.accentMuted}`,
                                            marginLeft: '24px'
                                        }}>
                                            {loadingTopics && selectedSubjectId === subject.id ? (
                                                <div style={{ padding: '12px', textAlign: 'center' }}><Loader2 size={18} className="animate-spin" color={designTokens.accent} /></div>
                                            ) : topics.length === 0 ? (
                                                <div style={{ padding: '12px', color: designTokens.primaryLight, opacity: 0.5, fontSize: '0.8rem' }}>No topics</div>
                                            ) : topics.map((topic) => (
                                                <div key={topic.id}>
                                                    <button
                                                        onClick={(e) => toggleTopic(topic.id, e)}
                                                        style={{
                                                            width: '100%',
                                                            padding: '10px 14px',
                                                            borderRadius: designTokens.radiusSm,
                                                            border: 'none',
                                                            background: selectedTopicId === topic.id ? designTokens.primaryMuted : 'transparent',
                                                            cursor: 'pointer',
                                                            textAlign: 'left',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '10px',
                                                            transition: designTokens.transition,
                                                        }}
                                                    >
                                                        <div style={{ opacity: 0.4 }}>
                                                            {expandedTopics[topic.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                                        </div>
                                                        <FolderOpen size={16} color={selectedTopicId === topic.id ? designTokens.primary : designTokens.primaryLight} style={{ opacity: 0.7 }} />
                                                        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: selectedTopicId === topic.id ? designTokens.primary : designTokens.primaryLight, flex: 1 }}>
                                                            {topic.name}
                                                        </span>
                                                        <div style={{
                                                            fontSize: '0.65rem',
                                                            fontWeight: 700,
                                                            padding: '2px 6px',
                                                            borderRadius: '6px',
                                                            background: topic.processed_count === topic.subtopic_count ? designTokens.success : designTokens.primaryMuted,
                                                            color: topic.processed_count === topic.subtopic_count ? 'white' : designTokens.primaryLight,
                                                            opacity: topic.processed_count === topic.subtopic_count ? 1 : 0.6
                                                        }}>
                                                            {topic.processed_count}/{topic.subtopic_count}
                                                        </div>
                                                    </button>

                                                    {/* Subtopics removed from sidebar tree per user request */}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* V8 Content Details Area (Center) */}
            <div style={{
                ...cardStyle(isMobile),
                display: 'flex',
                flexDirection: 'column',
                minHeight: '800px',
                padding: '32px',
                background: 'rgba(255, 255, 255, 0.98)', // Brighter center for focus
            }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px', paddingBottom: '24px', borderBottom: `1px solid ${designTokens.primaryMuted}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        {viewMode === 'subtopic-detail' && (
                            <button
                                onClick={() => setViewMode('topic-overview')}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    padding: '8px',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    color: designTokens.primaryLight
                                }}
                            >
                                <ChevronRight size={20} style={{ transform: 'rotate(180deg)' }} />
                            </button>
                        )}
                        <div style={{ background: designTokens.primaryMuted, padding: '12px', borderRadius: '16px', border: `1px solid ${designTokens.cardBorder}` }}>
                            {viewMode === 'topic-overview' ? <Folder size={24} color={designTokens.accent} /> : <Sparkles size={24} color={designTokens.accent} />}
                        </div>
                        <div>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: designTokens.primary, letterSpacing: '-0.02em' }}>
                                {viewMode === 'topic-overview' ? (topics.find(t => t.id === selectedTopicId)?.name || 'Select a Topic') : (fullSubtopic?.name || 'V8 Detail')}
                            </h3>
                            <div style={{ fontSize: '0.85rem', color: designTokens.primaryLight, marginTop: '4px', opacity: 0.7 }}>
                                {viewMode === 'topic-overview' ? 'Topic Overview & Subtopics' : 'Knowledge Nodes & AI Assessment Engine'}
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ flex: 1 }}>
                    {!selectedTopicId ? (
                        <div style={{ padding: '80px 20px', textAlign: 'center', color: '#94a3b8' }}>
                            <div style={{ display: 'inline-flex', padding: '24px', background: '#f8fafc', borderRadius: '50%', marginBottom: '24px' }}>
                                <Eye size={48} color="#cbd5e1" />
                            </div>
                            <h4 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 12px 0', color: '#475569' }}>Explorer View</h4>
                            <p style={{ fontSize: '0.95rem', margin: 0, maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                                Select a subject and topic on the left to begin browsing educational subtopics.
                            </p>
                        </div>
                    ) : viewMode === 'topic-overview' ? (
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
                                <Layers size={18} color={designTokens.accent} />
                                <h4 style={{ fontSize: '0.9rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: designTokens.primaryLight }}>Available Subtopics</h4>
                            </div>

                            {loadingSubtopics ? (
                                <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 size={32} className="animate-spin" color={designTokens.accent} /></div>
                            ) : subtopics.length === 0 ? (
                                <div style={{ padding: '40px', textAlign: 'center', color: designTokens.primaryLight }}>No subtopics found.</div>
                            ) : (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                                    {subtopics.map((subtopic) => (
                                        <button
                                            key={subtopic.id}
                                            onClick={() => setSelectedSubtopicId(subtopic.id)}
                                            style={{
                                                padding: '24px',
                                                background: 'white',
                                                borderRadius: designTokens.radiusMd,
                                                border: `1px solid ${selectedSubtopicId === subtopic.id ? designTokens.accent : designTokens.cardBorder}`,
                                                textAlign: 'left',
                                                cursor: 'pointer',
                                                transition: designTokens.transition,
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '12px',
                                                boxShadow: selectedSubtopicId === subtopic.id ? designTokens.shadowLg : designTokens.shadowSm,
                                                position: 'relative',
                                                overflow: 'hidden'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.transform = 'translateY(-4px)';
                                                e.currentTarget.style.boxShadow = designTokens.shadowLg;
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.transform = 'translateY(0)';
                                                e.currentTarget.style.boxShadow = selectedSubtopicId === subtopic.id ? designTokens.shadowLg : designTokens.shadowSm;
                                            }}
                                        >
                                            {subtopic.v8_concepts_count > 0 && (
                                                <div style={{ position: 'absolute', top: 0, right: 0, padding: '8px', background: designTokens.success + '20', borderRadius: '0 0 0 12px' }}>
                                                    <CheckCircle2 size={14} color={designTokens.success} />
                                                </div>
                                            )}
                                            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: designTokens.accent, textTransform: 'uppercase' }}>Subtopic 0{subtopic.order_num}</div>
                                            <div style={{ fontWeight: 700, fontSize: '1rem', color: designTokens.primary }}>{subtopic.name}</div>
                                            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                                                {subtopic.v8_concepts_count > 0 ? (
                                                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: designTokens.success }}>
                                                        {subtopic.v8_concepts_count} Knowledge Nodes
                                                    </div>
                                                ) : (
                                                    <div style={{ fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8' }}>Pending Synthesis</div>
                                                )}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        /* Subtopic Detail Mode */
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            {loadingContent ? (
                                <div style={{ padding: '80px 20px', textAlign: 'center' }}>
                                    <Loader2 size={40} className="animate-spin" color={designTokens.accent} />
                                    <div style={{ marginTop: '16px', fontWeight: 600, color: designTokens.primaryLight }}>Accessing V8 Nodes...</div>
                                </div>
                            ) : subtopicStatus && !subtopicStatus.has_concepts ? (
                                <div style={{ padding: '60px 40px', textAlign: 'center', background: '#f8fafc', borderRadius: '24px', border: '2px dashed #e2e8f0' }}>
                                    <div style={{ display: 'inline-flex', padding: '20px', background: '#fffbeb', borderRadius: '50%', marginBottom: '20px' }}>
                                        <Sparkles size={40} color="#f59e0b" />
                                    </div>
                                    <h4 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 12px 0', color: '#1e293b' }}>
                                        No V8 Content Synthesis Detected
                                    </h4>
                                    <p style={{ fontSize: '0.95rem', color: '#64748b', marginBottom: '32px', maxWidth: '450px', marginLeft: 'auto', marginRight: 'auto' }}>
                                        This subtopic requires initialization through the V8 generation pipeline to create diagrams and concept nodes.
                                    </p>
                                    <button
                                        onClick={() => openGenerateModal(false)}
                                        disabled={generating}
                                        style={{
                                            ...buttonPrimary,
                                            padding: '14px 32px',
                                            borderRadius: '14px',
                                            fontSize: '1rem',
                                            boxShadow: '0 10px 25px -5px rgba(190, 18, 60, 0.4)'
                                        }}
                                    >
                                        <Zap size={20} />
                                        Initialize Synthesis
                                    </button>
                                </div>
                            ) : subtopicStatus && fullSubtopic ? (
                                <V8ContentDetails
                                    status={subtopicStatus}
                                    subtopic={fullSubtopic}
                                    onRegenerate={() => openGenerateModal(true)}
                                    regenerating={generating}
                                />
                            ) : null}
                        </div>
                    )}
                </div>
            </div>

            {/* Telemetry & Tasks Sidebar (Right) */}
            {
                !isTablet && (
                    <div style={{
                        ...cardStyle(isMobile),
                        display: 'flex',
                        flexDirection: 'column',
                        maxHeight: '900px',
                        padding: '24px',
                        background: 'rgba(15, 23, 42, 0.02)', // Slightly distinct slate wash
                        borderLeft: `1px solid ${designTokens.primaryMuted}`
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', paddingBottom: '16px', borderBottom: `1px solid ${designTokens.primaryMuted}` }}>
                            <div style={{ background: designTokens.primary, padding: '8px', borderRadius: '10px' }}>
                                <BarChart3 size={18} color="white" />
                            </div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0, color: designTokens.primary, letterSpacing: '-0.02em' }}>Telemetry Stream</h3>
                        </div>

                        <div style={{ flex: 1, overflowY: 'auto' }} className="custom-scrollbar">
                            {taskStatus ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                    {/* Mini Task Status */}
                                    <div style={{
                                        padding: '20px',
                                        background: taskStatus.status === 'failed' ? '#fff1f2' :
                                            taskStatus.status === 'completed' ? '#f0fdf4' : designTokens.primary,
                                        borderRadius: designTokens.radiusMd,
                                        color: taskStatus.status === 'running' || taskStatus.status === 'pending' ? 'white' : 'inherit',
                                        boxShadow: designTokens.shadowSm,
                                        border: `1px solid ${taskStatus.status === 'failed' ? '#fecaca' : taskStatus.status === 'completed' ? '#bbf7d0' : 'rgba(255,255,255,0.1)'}`,
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                {taskStatus.status === 'running' && <RefreshCw size={16} className="animate-spin" color={designTokens.accentLight} />}
                                                {taskStatus.status === 'completed' && <CheckCircle2 size={16} color={designTokens.success} />}
                                                <span style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{taskStatus.status}</span>
                                            </div>
                                            {taskStatus.status === 'running' && (
                                                <div style={{ fontSize: '1.1rem', fontWeight: 900, color: designTokens.accentLight }}>{taskStatus.progress}%</div>
                                            )}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '12px', lineHeight: 1.4 }}>{taskStatus.message}</div>

                                        {taskStatus.status === 'running' && (
                                            <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                                                <div style={{
                                                    background: `linear-gradient(90deg, ${designTokens.accent} 0%, ${designTokens.accentLight} 100%)`,
                                                    height: '100%',
                                                    width: `${taskStatus.progress}%`,
                                                    transition: 'width 0.4s ease'
                                                }} />
                                            </div>
                                        )}
                                    </div>

                                    {/* Logs */}
                                    {taskStatus.logs && taskStatus.logs.length > 0 && (
                                        <div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                                <Terminal size={14} color={designTokens.primaryLight} style={{ opacity: 0.6 }} />
                                                <span style={{ fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: designTokens.primaryLight, opacity: 0.6 }}>Log History</span>
                                            </div>
                                            <div style={{
                                                background: '#0f172a',
                                                borderRadius: '12px',
                                                padding: '16px',
                                                maxHeight: '500px',
                                                overflowY: 'auto',
                                                fontFamily: "'Fira Code', monospace",
                                                fontSize: '0.75rem',
                                                color: '#94a3b8',
                                                boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.3)',
                                                lineHeight: 1.5
                                            }} className="custom-scrollbar">
                                                {taskStatus.logs.slice().reverse().map((log, idx) => (
                                                    <div key={idx} style={{
                                                        padding: '6px 0',
                                                        borderBottom: '1px solid rgba(255,255,255,0.03)',
                                                        color: log.log_level === 'error' ? '#f87171' : log.log_level === 'warning' ? '#fbbf24' : '#94a3b8'
                                                    }}>
                                                        <span style={{ opacity: 0.4, fontSize: '0.65rem' }}>{log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'SYS'}</span>
                                                        <div style={{ marginTop: '2px' }}>{log.message}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div style={{ padding: '40px 20px', textAlign: 'center', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
                                    <Info size={32} style={{ opacity: 0.2 }} />
                                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>No Active Tasks</div>
                                    <p style={{ fontSize: '0.75rem', opacity: 0.6, margin: 0 }}>Start a V8 synthesis task to see live telemetry and architectural logs here.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

            {showGenerateModal && (
                <V8GenerateModal
                    options={generateOptions}
                    setOptions={setGenerateOptions}
                    onConfirm={() => handleGenerateV8(generateOptions.force_regenerate)}
                    onClose={() => setShowGenerateModal(false)}
                    generating={generating}
                    subtopicName={subtopics.find(s => s.id === selectedSubtopicId)?.name}
                    isMobile={isMobile}
                />
            )}
        </div>
    );
};

// ===========================================================================
// V8 CONTENT DETAILS COMPONENT
// ===========================================================================

const V8ContentDetails = ({
    status,
    subtopic,
    onRegenerate,
    regenerating
}: {
    status: V8SubtopicStatus;
    subtopic: V8FullSubtopic;
    onRegenerate: () => void;
    regenerating: boolean;
}) => {
    return (
        <div style={{ fontFamily: designTokens.fontFamily }}>
            {/* Unified Content Stream */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
                {/* Concepts Section */}
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                        <div style={{ background: designTokens.success + '20', padding: '10px', borderRadius: '12px' }}>
                            <Layers size={20} color={designTokens.success} />
                        </div>
                        <h4 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: designTokens.primary }}>Knowledge Modules</h4>
                        <div style={{ marginLeft: 'auto', fontSize: '0.8rem', fontWeight: 700, color: designTokens.primaryLight, opacity: 0.4 }}>
                            {subtopic.concepts?.length || 0} Modules
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {subtopic.concepts?.map((concept, index) => (
                            <div key={concept.id || index} style={{
                                padding: '24px',
                                background: 'white',
                                borderRadius: designTokens.radiusMd,
                                border: `1px solid ${designTokens.cardBorder}`,
                                boxShadow: designTokens.shadowSm,
                                transition: designTokens.transition,
                                position: 'relative',
                                overflow: 'hidden'
                            }}>
                                <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: designTokens.accent }} />
                                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '12px' }}>
                                    <span style={{ fontSize: '1.75rem' }}>{concept.icon || '📚'}</span>
                                    <span style={{ fontWeight: 800, color: designTokens.primary, fontSize: '1.05rem', letterSpacing: '-0.01em' }}>{concept.title}</span>
                                    {concept.generated?.svg && (
                                        <div style={{
                                            marginLeft: 'auto',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                            padding: '4px 12px',
                                            background: designTokens.success + '20',
                                            color: designTokens.success,
                                            borderRadius: '20px',
                                            fontSize: '0.7rem',
                                            fontWeight: 800
                                        }}>
                                            <ImageIcon size={12} />
                                            SVG READY
                                        </div>
                                    )}
                                </div>
                                <div style={{
                                    fontSize: '0.95rem',
                                    color: designTokens.primaryLight,
                                    lineHeight: 1.6,
                                    opacity: 0.8
                                }}>
                                    {concept.description || (concept.generated?.bullets ?
                                        <div dangerouslySetInnerHTML={{ __html: concept.generated.bullets }} /> :
                                        'No description available.')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Quiz Section */}
                {subtopic.quiz && subtopic.quiz.length > 0 && (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                            <div style={{ background: designTokens.primaryMuted, padding: '10px', borderRadius: '12px' }}>
                                <HelpCircle size={20} color={designTokens.primary} />
                            </div>
                            <h4 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: designTokens.primary }}>Assessment Engine</h4>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {subtopic.quiz.map((question, index) => (
                                <div key={question.id || index} style={{
                                    padding: '24px',
                                    background: 'white',
                                    borderRadius: designTokens.radiusMd,
                                    border: `1px solid ${designTokens.cardBorder}`,
                                    boxShadow: designTokens.shadowSm,
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                                        <div style={{
                                            padding: '4px 12px',
                                            background: designTokens.primary,
                                            color: 'white',
                                            borderRadius: '20px',
                                            fontSize: '0.7rem',
                                            fontWeight: 800,
                                            letterSpacing: '0.05em'
                                        }}>
                                            QUESTION {question.question_num || index + 1}
                                        </div>
                                    </div>
                                    <div style={{
                                        fontWeight: 700,
                                        color: designTokens.primary,
                                        fontSize: '1.05rem',
                                        lineHeight: 1.5,
                                        marginBottom: '16px'
                                    }}>
                                        {question.question_text}
                                    </div>
                                    <div style={{
                                        background: designTokens.success + '10',
                                        padding: '12px 16px',
                                        borderRadius: '10px',
                                        fontSize: '0.85rem',
                                        color: designTokens.success,
                                        fontWeight: 700,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }}>
                                        <CheckCircle2 size={16} />
                                        Correct Solution: {question.correct_answer}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Flashcards Section */}
                {subtopic.flashcards && subtopic.flashcards.length > 0 && (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                            <div style={{ background: designTokens.accentMuted, padding: '10px', borderRadius: '12px' }}>
                                <FileText size={20} color={designTokens.accent} />
                            </div>
                            <h4 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: designTokens.primary }}>Active Recall Base</h4>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
                            {subtopic.flashcards.map((card, index) => (
                                <div key={card.id || index} style={{
                                    padding: '24px',
                                    background: `linear-gradient(135deg, ${designTokens.primary} 0%, ${designTokens.primaryLight} 100%)`,
                                    borderRadius: designTokens.radiusMd,
                                    color: 'white',
                                    minHeight: '160px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'space-between',
                                    boxShadow: '0 10px 20px -5px rgba(30, 41, 59, 0.4)',
                                }}>
                                    <div style={{ fontSize: '1rem', fontWeight: 800, lineHeight: 1.4 }}>
                                        {card.front}
                                    </div>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        background: 'rgba(255,255,255,0.1)',
                                        padding: '10px',
                                        borderRadius: '8px',
                                        marginTop: '16px',
                                        opacity: 0.9
                                    }}>
                                        {card.back}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Regenerate Button */}
            <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: `1px solid ${designTokens.primaryMuted}` }}>
                <button
                    onClick={onRegenerate}
                    disabled={regenerating}
                    style={{
                        ...buttonSecondary,
                        width: '100%',
                        justifyContent: 'center',
                        padding: '16px',
                        background: '#f8fafc'
                    }}
                >
                    {regenerating ? (
                        <>
                            <RefreshCw size={18} className="animate-spin" />
                            Force Refreshing V8 Pipeline...
                        </>
                    ) : (
                        <>
                            <RefreshCw size={18} />
                            Regenerate Concept Synthesis
                        </>
                    )}
                </button>
            </div>
        </div >
    );
};

export default V8ContentBrowser;
