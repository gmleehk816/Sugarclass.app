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
// STYLES
// ===========================================================================

const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontFamily: 'inherit' as const,
    background: 'white',
};

const cardStyle = (isMobile?: boolean) => ({
    background: 'white',
    padding: isMobile ? '16px' : '24px',
    borderRadius: '16px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
});

const buttonPrimary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    borderRadius: '10px',
    background: '#be123c',
    color: 'white',
    border: 'none',
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
};

const buttonSecondary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 20px',
    borderRadius: '10px',
    background: 'white',
    color: '#374151',
    border: '1px solid #e2e8f0',
    fontWeight: 600,
    fontSize: '0.9rem',
    cursor: 'pointer',
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
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
        }}>
            <div style={{
                background: 'white',
                borderRadius: '24px',
                padding: isMobile ? '24px' : '40px',
                maxWidth: '700px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                    <div>
                        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, color: '#1e293b' }}>
                            Generate V8 Content
                        </h2>
                        <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
                            {subtopicName ? `Configure generation for: ${subtopicName}` : 'Configure V8 content generation'}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        disabled={generating}
                        style={{
                            background: '#f1f5f9',
                            border: 'none',
                            width: '40px',
                            height: '40px',
                            borderRadius: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: generating ? 'not-allowed' : 'pointer',
                            color: '#64748b',
                            fontSize: '1.2rem'
                        }}
                    >
                        ✕
                    </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Content Types */}
                    <div style={{
                        background: '#f8fafc',
                        padding: '20px',
                        borderRadius: '16px',
                        border: '1px solid #e2e8f0'
                    }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                            <Layers size={18} color="#7c3aed" /> Content Types to Generate
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                            {[
                                { key: 'generate_concepts', label: 'Concepts & SVGs', icon: '📚' },
                                { key: 'generate_svgs', label: 'SVG Diagrams', icon: '🎨' },
                                { key: 'generate_quiz', label: 'Quiz Questions', icon: '❓' },
                                { key: 'generate_flashcards', label: 'Flashcards', icon: '🎴' },
                                { key: 'generate_images', label: 'Real-life Images', icon: '🖼️' },
                            ].map(item => (
                                <label key={item.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: generating ? 'not-allowed' : 'pointer', padding: '8px 12px', background: (options as any)[item.key] ? '#eef2ff' : 'white', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                                    <input
                                        type="checkbox"
                                        checked={(options as any)[item.key]}
                                        onChange={(e) => setOptions({ ...options, [item.key]: e.target.checked })}
                                        disabled={generating}
                                        style={{ width: '18px', height: '18px', accentColor: '#7c3aed' }}
                                    />
                                    <span style={{ fontSize: '0.9rem', color: '#475569', fontWeight: 500 }}>{item.icon} {item.label}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Custom Prompt */}
                    <div style={{
                        background: '#f8fafc',
                        padding: '20px',
                        borderRadius: '16px',
                        border: '1px solid #e2e8f0'
                    }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                            <Edit size={18} color="#7c3aed" /> Additional Instructions
                        </label>
                        <textarea
                            value={options.custom_prompt}
                            onChange={(e) => setOptions({ ...options, custom_prompt: e.target.value })}
                            disabled={generating}
                            placeholder="e.g., Focus on visual explanations, add more examples for difficult concepts, use simpler language..."
                            style={{
                                ...inputStyle,
                                minHeight: '100px',
                                resize: 'vertical',
                                background: generating ? '#f1f5f9' : 'white',
                                fontSize: '0.9rem',
                                borderRadius: '10px',
                            }}
                        />
                    </div>

                    {/* Force Regenerate */}
                    {options.force_regenerate && (
                        <div style={{
                            padding: '16px',
                            background: '#fff1f2',
                            borderRadius: '12px',
                            border: '1px solid #fecaca',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px'
                        }}>
                            <AlertCircle size={20} color="#dc2626" />
                            <span style={{ fontSize: '0.9rem', color: '#991b1b' }}>
                                <strong>Force Regenerate:</strong> Existing V8 content for this subtopic will be replaced.
                            </span>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{
                    marginTop: '32px',
                    paddingTop: '24px',
                    borderTop: '1px solid #f1f5f9',
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '16px'
                }}>
                    <div style={{
                        padding: '12px 16px',
                        background: '#eff6ff',
                        borderRadius: '12px',
                        fontSize: '0.85rem',
                        color: '#1e40af',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <Info size={14} />
                        Generation runs in background
                    </div>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <button
                            onClick={onClose}
                            disabled={generating}
                            style={{
                                padding: '12px 24px',
                                borderRadius: '12px',
                                border: '1px solid #e2e8f0',
                                background: 'white',
                                color: '#64748b',
                                cursor: generating ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                fontSize: '0.95rem',
                            }}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={generating}
                            style={{
                                padding: '12px 32px',
                                borderRadius: '12px',
                                border: 'none',
                                background: generating ? '#94a3b8' : 'linear-gradient(135deg, #be123c 0%, #9f1239 100%)',
                                color: 'white',
                                cursor: generating ? 'not-allowed' : 'pointer',
                                fontWeight: 700,
                                fontSize: '0.95rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}
                        >
                            {generating ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Zap size={16} />
                                    Start Generation
                                </>
                            )}
                        </button>
                    </div>
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

    // Fetch V8 subjects on mount
    useEffect(() => {
        loadSubjects();
    }, []);

    // Sync with prop subjects if provided (as fallback)
    useEffect(() => {
        if (propSubjects && propSubjects.length > 0 && subjects.length === 0) {
            setSubjects(propSubjects);
        }
    }, [propSubjects]);

    // Load topics when subject is selected
    useEffect(() => {
        if (selectedSubjectId) {
            loadTopics(selectedSubjectId);
        } else {
            setTopics([]);
            setSelectedTopicId(null);
            setSubtopics([]);
            setSelectedSubtopicId(null);
        }
    }, [selectedSubjectId]);

    // Load subtopics when topic is selected
    useEffect(() => {
        if (selectedTopicId) {
            loadSubtopics(selectedTopicId);
        } else {
            setSubtopics([]);
            setSelectedSubtopicId(null);
        }
    }, [selectedTopicId]);

    // Load content when subtopic is selected
    useEffect(() => {
        if (selectedSubtopicId) {
            loadSubtopicContent(selectedSubtopicId);
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
            // Auto-select first subject if available
            if (data.subjects && data.subjects.length > 0) {
                setSelectedSubjectId(data.subjects[0].id);
            }
        } catch (err) {
            console.error('Error loading subjects', err);
            // Fallback to prop subjects
            if (propSubjects && propSubjects.length > 0) {
                setSubjects(propSubjects);
            }
        } finally {
            setLoadingSubjects(false);
        }
    };

    const loadTopics = async (subjectId: string) => {
        setLoadingTopics(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/v8/subjects/${subjectId}/topics`);
            setTopics(data.topics || []);
            if (data.topics?.length > 0) {
                setSelectedTopicId(data.topics[0].id);
            }
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
            if (data.subtopics?.length > 0) {
                setSelectedSubtopicId(data.subtopics[0].id);
            }
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
            // Load status
            const statusData = await serviceFetch('aimaterials', `/api/admin/v8/subtopics/${subtopicId}/status`);
            setSubtopicStatus(statusData);

            // Load full content if processed
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
                // Content already exists
                setTaskStatus({
                    task_id: '',
                    status: 'completed',
                    progress: 100,
                    message: data.message || 'V8 content already exists',
                    logs: []
                });
                setGenerating(false);
                // Reload content
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

    // Find selected subject
    const selectedSubject = subjects.find(s => s.id === selectedSubjectId);

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: isTablet ? '1fr' : '260px 280px 1fr',
            gap: '20px',
            minHeight: '600px'
        }}>
            {/* Subject List */}
            <div style={cardStyle(isMobile)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                    <Database size={18} color="#6366f1" />
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Subjects</h3>
                </div>

                {loadingSubjects ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
                        <Loader2 size={20} className="animate-spin" />
                    </div>
                ) : subjects.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
                        No subjects found. Upload content first.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {subjects.map((subject: any) => (
                            <button
                                key={subject.id}
                                onClick={() => setSelectedSubjectId(subject.id)}
                                style={{
                                    padding: '12px 14px',
                                    borderRadius: '10px',
                                    border: 'none',
                                    background: selectedSubjectId === subject.id ? '#eef2ff' : 'transparent',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    transition: 'background 0.15s',
                                }}
                            >
                                <BookOpen size={16} color={selectedSubjectId === subject.id ? '#6366f1' : '#94a3b8'} />
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>
                                        {subject.name}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                                        {subject.topic_count || 0} topics
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Topic/Subtopic Tree */}
            <div style={cardStyle(isMobile)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                    <Layers size={18} color="#8b5cf6" />
                    <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Topics & Subtopics</h3>
                </div>

                {!selectedSubjectId ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
                        Select a subject
                    </div>
                ) : loadingTopics ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
                        <Loader2 size={20} className="animate-spin" />
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '500px', overflowY: 'auto' }}>
                        {topics.map((topic) => (
                            <div key={topic.id}>
                                {/* Topic Header */}
                                <button
                                    onClick={() => setSelectedTopicId(selectedTopicId === topic.id ? null : topic.id)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        borderRadius: '8px',
                                        border: 'none',
                                        background: selectedTopicId === topic.id ? '#f5f3ff' : 'transparent',
                                        cursor: 'pointer',
                                        textAlign: 'left',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                    }}
                                >
                                    {selectedTopicId === topic.id ? (
                                        <ChevronDown size={14} color="#8b5cf6" />
                                    ) : (
                                        <ChevronRight size={14} color="#94a3b8" />
                                    )}
                                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#374151' }}>
                                        {topic.topic_id} - {topic.name}
                                    </span>
                                    <span style={{
                                        marginLeft: 'auto',
                                        fontSize: '0.7rem',
                                        padding: '2px 6px',
                                        borderRadius: '10px',
                                        background: topic.processed_count > 0 ? '#dcfce7' : '#f3f4f6',
                                        color: topic.processed_count > 0 ? '#16a34a' : '#9ca3af',
                                    }}>
                                        {topic.processed_count}/{topic.subtopic_count}
                                    </span>
                                </button>

                                {/* Subtopics */}
                                {selectedTopicId === topic.id && (
                                    <div style={{ paddingLeft: '20px', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        {loadingSubtopics ? (
                                            <div style={{ padding: '10px', textAlign: 'center' }}>
                                                <Loader2 size={16} className="animate-spin" />
                                            </div>
                                        ) : subtopics.map((subtopic) => (
                                            <button
                                                key={subtopic.id}
                                                onClick={() => setSelectedSubtopicId(subtopic.id)}
                                                style={{
                                                    padding: '8px 12px',
                                                    borderRadius: '6px',
                                                    border: 'none',
                                                    background: selectedSubtopicId === subtopic.id ? '#e0e7ff' : 'transparent',
                                                    cursor: 'pointer',
                                                    textAlign: 'left',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '8px',
                                                }}
                                            >
                                                <FileText size={14} color={subtopic.processed_at ? '#6366f1' : '#d1d5db'} />
                                                <span style={{ fontSize: '0.8rem', color: '#4b5563' }}>
                                                    {subtopic.subtopic_id} {subtopic.name}
                                                </span>
                                                {subtopic.v8_concepts_count > 0 && (
                                                    <CheckCircle2 size={12} color="#22c55e" style={{ marginLeft: 'auto' }} />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* V8 Content Details */}
            <div style={cardStyle(isMobile)}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Sparkles size={18} color="#be123c" />
                        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>V8 Content</h3>
                    </div>
                    {selectedSubtopicId && (
                        <button
                            onClick={() => openGenerateModal(false)}
                            disabled={generating}
                            style={{
                                ...buttonPrimary,
                                opacity: generating ? 0.6 : 1,
                                cursor: generating ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {generating ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <Zap size={16} />
                                    Generate V8
                                </>
                            )}
                        </button>
                    )}
                </div>

                {/* Task Progress */}
                {taskStatus && (
                    <div style={{
                        padding: '16px',
                        background: taskStatus.status === 'failed' ? '#fef2f2' :
                                   taskStatus.status === 'completed' ? '#f0fdf4' : '#eff6ff',
                        borderRadius: '12px',
                        marginBottom: '20px',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                            {taskStatus.status === 'running' && <Loader2 size={16} className="animate-spin" color="#3b82f6" />}
                            {taskStatus.status === 'completed' && <CheckCircle2 size={16} color="#22c55e" />}
                            {taskStatus.status === 'failed' && <XCircle size={16} color="#ef4444" />}
                            {taskStatus.status === 'pending' && <Clock size={16} color="#f59e0b" />}
                            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                                {taskStatus.status === 'running' ? `Processing... ${taskStatus.progress}%` :
                                 taskStatus.status === 'completed' ? 'Completed!' :
                                 taskStatus.status === 'failed' ? 'Failed' : 'Pending...'}
                            </span>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>{taskStatus.message}</div>

                        {/* Progress Bar */}
                        {taskStatus.status === 'running' && (
                            <div style={{ marginTop: '12px', background: '#e2e8f0', borderRadius: '10px', height: '8px', overflow: 'hidden' }}>
                                <div style={{
                                    background: '#3b82f6',
                                    height: '100%',
                                    width: `${taskStatus.progress}%`,
                                    transition: 'width 0.3s',
                                }} />
                            </div>
                        )}

                        {/* Error message */}
                        {taskStatus.error && (
                            <div style={{ marginTop: '8px', fontSize: '0.8rem', color: '#dc2626' }}>
                                {taskStatus.error}
                            </div>
                        )}

                        {/* Live Logs Panel */}
                        {taskStatus.logs && taskStatus.logs.length > 0 && (
                            <div style={{ marginTop: '12px' }}>
                                <button
                                    onClick={() => setShowLogs(!showLogs)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        background: 'none',
                                        border: 'none',
                                        cursor: 'pointer',
                                        fontSize: '0.8rem',
                                        color: '#64748b',
                                        padding: '4px 0',
                                        fontWeight: 500,
                                    }}
                                >
                                    <Terminal size={14} />
                                    {showLogs ? 'Hide Logs' : 'Show Logs'}
                                    {showLogs ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                </button>

                                {showLogs && (
                                    <div style={{
                                        marginTop: '8px',
                                        background: '#1e293b',
                                        borderRadius: '8px',
                                        padding: '12px',
                                        maxHeight: '200px',
                                        overflowY: 'auto',
                                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                                        fontSize: '0.75rem',
                                    }}>
                                        {taskStatus.logs.map((log, idx) => (
                                            <div
                                                key={idx}
                                                style={{
                                                    color: log.log_level === 'error' ? '#f87171' :
                                                           log.log_level === 'warning' ? '#fbbf24' : '#94a3b8',
                                                    padding: '2px 0',
                                                    borderBottom: idx < taskStatus.logs!.length - 1 ? '1px solid #334155' : 'none',
                                                }}
                                            >
                                                <span style={{ color: '#64748b', marginRight: '8px' }}>
                                                    {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}
                                                </span>
                                                {log.message}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {!selectedSubtopicId ? (
                    <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                        <Eye size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
                        <div style={{ fontSize: '1rem' }}>Select a subtopic to view V8 content</div>
                    </div>
                ) : loadingContent ? (
                    <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                        <Loader2 size={32} className="animate-spin" />
                    </div>
                ) : subtopicStatus && !subtopicStatus.has_concepts ? (
                    <div style={{ padding: '40px 20px', textAlign: 'center' }}>
                        <AlertCircle size={48} color="#f59e0b" style={{ marginBottom: '16px' }} />
                        <div style={{ fontSize: '1rem', color: '#374151', marginBottom: '8px' }}>
                            No V8 content yet
                        </div>
                        <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '20px' }}>
                            Click "Generate V8" to create concepts, quiz questions, and flashcards.
                        </div>
                        <button
                            onClick={() => openGenerateModal(false)}
                            disabled={generating}
                            style={buttonPrimary}
                        >
                            <Zap size={16} />
                            Generate V8 Content
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

            {/* V8 Generation Options Modal */}
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
    const [activeTab, setActiveTab] = useState<'concepts' | 'quiz' | 'flashcards'>('concepts');

    return (
        <div>
            {/* Status Summary */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '12px',
                marginBottom: '20px',
            }}>
                <div style={{ padding: '12px', background: '#f0fdf4', borderRadius: '10px', textAlign: 'center' }}>
                    <Layers size={20} color="#22c55e" style={{ marginBottom: '4px' }} />
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#166534' }}>{status.concept_count}</div>
                    <div style={{ fontSize: '0.75rem', color: '#4ade80' }}>Concepts</div>
                </div>
                <div style={{ padding: '12px', background: '#eff6ff', borderRadius: '10px', textAlign: 'center' }}>
                    <HelpCircle size={20} color="#3b82f6" style={{ marginBottom: '4px' }} />
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e40af' }}>{status.quiz_count}</div>
                    <div style={{ fontSize: '0.75rem', color: '#60a5fa' }}>Quiz</div>
                </div>
                <div style={{ padding: '12px', background: '#fef3c7', borderRadius: '10px', textAlign: 'center' }}>
                    <FileText size={20} color="#f59e0b" style={{ marginBottom: '4px' }} />
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#92400e' }}>{status.flashcard_count}</div>
                    <div style={{ fontSize: '0.75rem', color: '#fbbf24' }}>Flashcards</div>
                </div>
                <div style={{ padding: '12px', background: '#fae8ff', borderRadius: '10px', textAlign: 'center' }}>
                    <ImageIcon size={20} color="#c026d3" style={{ marginBottom: '4px' }} />
                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#86198f' }}>{status.svg_count}</div>
                    <div style={{ fontSize: '0.75rem', color: '#d946ef' }}>SVGs</div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #e5e7eb', paddingBottom: '12px' }}>
                <button
                    onClick={() => setActiveTab('concepts')}
                    style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        background: activeTab === 'concepts' ? '#eef2ff' : 'transparent',
                        color: activeTab === 'concepts' ? '#4f46e5' : '#6b7280',
                        fontWeight: 600,
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                    }}
                >
                    <Layers size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                    Concepts ({subtopic.concepts?.length || 0})
                </button>
                <button
                    onClick={() => setActiveTab('quiz')}
                    style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        background: activeTab === 'quiz' ? '#eef2ff' : 'transparent',
                        color: activeTab === 'quiz' ? '#4f46e5' : '#6b7280',
                        fontWeight: 600,
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                    }}
                >
                    <HelpCircle size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                    Quiz ({subtopic.quiz?.length || 0})
                </button>
                <button
                    onClick={() => setActiveTab('flashcards')}
                    style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: 'none',
                        background: activeTab === 'flashcards' ? '#eef2ff' : 'transparent',
                        color: activeTab === 'flashcards' ? '#4f46e5' : '#6b7280',
                        fontWeight: 600,
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                    }}
                >
                    <FileText size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                    Flashcards ({subtopic.flashcards?.length || 0})
                </button>
            </div>

            {/* Tab Content */}
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {activeTab === 'concepts' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {subtopic.concepts?.map((concept, index) => (
                            <div key={concept.id || index} style={{
                                padding: '16px',
                                background: '#f9fafb',
                                borderRadius: '12px',
                                border: '1px solid #e5e7eb',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                                    <span style={{ fontSize: '1.5rem' }}>{concept.icon || '📚'}</span>
                                    <span style={{ fontWeight: 600, color: '#1f2937' }}>{concept.title}</span>
                                    {concept.generated?.svg && (
                                        <span style={{
                                            marginLeft: 'auto',
                                            fontSize: '0.7rem',
                                            padding: '2px 8px',
                                            background: '#dcfce7',
                                            color: '#16a34a',
                                            borderRadius: '10px',
                                        }}>
                                            Has SVG
                                        </span>
                                    )}
                                </div>
                                <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
                                    {concept.description || concept.generated?.bullets?.replace(/<[^>]*>/g, ' ').substring(0, 150) + '...'}
                                </div>
                            </div>
                        ))}
                        {(!subtopic.concepts || subtopic.concepts.length === 0) && (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
                                No concepts found
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'quiz' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {subtopic.quiz?.map((question, index) => (
                            <div key={question.id || index} style={{
                                padding: '16px',
                                background: '#f9fafb',
                                borderRadius: '12px',
                                border: '1px solid #e5e7eb',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                                    <span style={{
                                        padding: '4px 10px',
                                        background: '#1f2937',
                                        color: 'white',
                                        borderRadius: '20px',
                                        fontSize: '0.75rem',
                                        fontWeight: 600,
                                    }}>
                                        Q{question.question_num || index + 1}
                                    </span>
                                    {question.difficulty && (
                                        <span style={{
                                            fontSize: '0.7rem',
                                            padding: '2px 8px',
                                            background: question.difficulty === 'easy' ? '#dcfce7' :
                                                       question.difficulty === 'hard' ? '#fee2e2' : '#fef3c7',
                                            color: question.difficulty === 'easy' ? '#16a34a' :
                                                   question.difficulty === 'hard' ? '#dc2626' : '#d97706',
                                            borderRadius: '10px',
                                        }}>
                                            {question.difficulty}
                                        </span>
                                    )}
                                </div>
                                <div style={{ fontWeight: 500, color: '#374151', marginBottom: '8px' }}>
                                    {question.question_text}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: '#22c55e' }}>
                                    Answer: {question.correct_answer}
                                </div>
                            </div>
                        ))}
                        {(!subtopic.quiz || subtopic.quiz.length === 0) && (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>
                                No quiz questions found
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'flashcards' && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                        {subtopic.flashcards?.map((card, index) => (
                            <div key={card.id || index} style={{
                                padding: '16px',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                borderRadius: '12px',
                                color: 'white',
                                minHeight: '120px',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'space-between',
                            }}>
                                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                                    {card.front}
                                </div>
                                <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                                    {card.back?.substring(0, 80)}...
                                </div>
                            </div>
                        ))}
                        {(!subtopic.flashcards || subtopic.flashcards.length === 0) && (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', gridColumn: '1 / -1' }}>
                                No flashcards found
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Regenerate Button */}
            <div style={{ marginTop: '20px', borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
                <button
                    onClick={onRegenerate}
                    disabled={regenerating}
                    style={{
                        ...buttonSecondary,
                        width: '100%',
                        justifyContent: 'center',
                    }}
                >
                    {regenerating ? (
                        <>
                            <Loader2 size={16} className="animate-spin" />
                            Regenerating...
                        </>
                    ) : (
                        <>
                            <RefreshCw size={16} />
                            Regenerate V8 Content
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default V8ContentBrowser;
