"use client";

import React, { useState, useEffect } from 'react';
import { serviceFetch } from '@/lib/microservices';
import {
    Zap,
    RefreshCw,
    CheckCircle2,
    XCircle,
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    Folder,
    FolderOpen,
    FileText,
    Layers,
    HelpCircle,
    Image as ImageIcon,
    Edit,
    Sparkles,
    Loader2,
    AlertCircle,
    Eye,
    Info,
    Search,
    Edit2,
    Trash2,
    Menu,
    ListOrdered
} from "lucide-react";
import { DATATREE, matchSubjectsToTree, DbSubject, sanitizeId } from '../lib/treeUtils';
import ChunkEditor from './ChunkEditor';

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

const premiumColors = {
    primary: '#1e293b',
    accent: '#7c3aed',
    accentSoft: 'rgba(124, 58, 237, 0.08)',
    text: '#1e293b',
    textSoft: '#64748b',
    border: 'rgba(0,0,0,0.06)',
    bg: '#fcfaf7',
    sidebarBg: '#ffffff'
};

const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    border: `1.5px solid ${premiumColors.border}`,
    borderRadius: '14px',
    fontSize: '0.9rem',
    fontFamily: "'Outfit', sans-serif",
    background: '#f8fafc',
    transition: 'all 0.2s ease',
};

const cardStyle = (isMobile?: boolean) => ({
    background: 'white',
    padding: isMobile ? '20px' : '32px',
    borderRadius: '24px',
    border: `1px solid ${premiumColors.border}`,
    boxShadow: '0 10px 30px -5px rgba(0,0,0,0.04)',
});

const buttonPrimary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 24px',
    borderRadius: '14px',
    background: premiumColors.primary,
    color: 'white',
    border: 'none',
    fontWeight: 700,
    fontSize: '0.9rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 8px 16px -4px rgba(30, 41, 59, 0.25)',
};

const buttonSecondary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 24px',
    borderRadius: '14px',
    background: 'white',
    color: premiumColors.primary,
    border: `1.5px solid ${premiumColors.border}`,
    fontWeight: 700,
    fontSize: '0.9rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
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

const sanitizeSvgMarkup = (svgMarkup?: string) => {
    if (!svgMarkup) return '';
    return svgMarkup
        .replace(/<\?xml[\s\S]*?\?>/gi, '')
        .replace(/<!doctype[\s\S]*?>/gi, '')
        .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
        .replace(/\son[a-z]+\s*=\s*(['"]).*?\1/gi, '')
        .replace(/\son[a-z]+\s*=\s*[^\s>]+/gi, '')
        .trim();
};

const sanitizeHtmlMarkup = (htmlMarkup?: string) => {
    if (!htmlMarkup) return '';
    return htmlMarkup
        .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, '')
        .replace(/\son[a-z]+\s*=\s*(['"]).*?\1/gi, '')
        .replace(/\son[a-z]+\s*=\s*[^\s>]+/gi, '')
        .trim();
};

const svgMarkupToDataUrl = (svgMarkup: string) => {
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgMarkup)}`;
};

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
                borderRadius: '32px', // Match main viewer
                padding: isMobile ? '24px' : '48px',
                width: '100%',
                margin: '0 auto',
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
                                borderRadius: '16px',
                                border: 'none',
                                background: generating ? '#94a3b8' : '#1e293b',
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
    isMobile
}: {
    subjects: any[];
    loadingSubjects: boolean;
    isMobile: boolean;
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
    const [editingConcept, setEditingConcept] = useState<any>(null);
    const [selectedSubtopicId, setSelectedSubtopicId] = useState<string | null>(null);
    const [subtopicStatus, setSubtopicStatus] = useState<V8SubtopicStatus | null>(null);
    const [fullSubtopic, setFullSubtopic] = useState<V8FullSubtopic | null>(null);
    const [isSidebarVisible, setIsSidebarVisible] = useState(true); // New state
    const [loadingContent, setLoadingContent] = useState(false);

    // Editing state for Quiz, Flashcards, Real Life
    const [editingQuiz, setEditingQuiz] = useState<any>(null);
    const [editingFlashcard, setEditingFlashcard] = useState<any>(null);
    const [editingRealLife, setEditingRealLife] = useState<any>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [editingSVGConcept, setEditingSVGConcept] = useState<any>(null);
    const [customSVGPrompt, setCustomSVGPrompt] = useState('');
    const [isRegeneratingSVG, setIsRegeneratingSVG] = useState(false);

    // Generation state
    const [generating, setGenerating] = useState(false);
    const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
    const [taskStatus, setTaskStatus] = useState<V8Task | null>(null);
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

    // Rename/Delete state
    const [itemToRename, setItemToRename] = useState<{ id: string, type: 'topic' | 'subtopic' | 'subject', name: string } | null>(null);
    const [newName, setNewName] = useState('');
    const [isProcessingAction, setIsProcessingAction] = useState(false);

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
            // We'll let the tree component handle selection or auto-select first one if desired
            // But for V8 we might wait for user to click a tree node
        } catch (err) {
            console.error('Error loading subjects', err);
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

    const handleDeleteSubject = async (subjectId: string, name: string) => {
        if (!window.confirm(`Are you sure you want to delete the subject "${name}" and all its topics/subtopics?`)) return;

        try {
            setIsProcessingAction(true);
            await serviceFetch('aimaterials', `/api/admin/v8/subjects/${subjectId}`, { method: 'DELETE' });
            loadSubjects();
            if (selectedSubjectId === subjectId) {
                setSelectedSubjectId(null);
            }
        } catch (err) {
            console.error('Error deleting subject', err);
            alert('Failed to delete subject');
        } finally {
            setIsProcessingAction(false);
        }
    };

    const handleDeleteTopic = async (topicId: string, name: string) => {
        if (!window.confirm(`Are you sure you want to delete the topic "${name}" and all its subtopics?`)) return;

        try {
            setIsProcessingAction(true);
            await serviceFetch('aimaterials', `/api/admin/v8/topics/${topicId}`, { method: 'DELETE' });
            loadTopics(selectedSubjectId!);
            if (selectedTopicId === topicId) {
                setSelectedTopicId(null);
            }
        } catch (err) {
            console.error('Error deleting topic', err);
            alert('Failed to delete topic');
        } finally {
            setIsProcessingAction(false);
        }
    };

    const handleDeleteSubtopic = async (subtopicId: string, name: string) => {
        if (!window.confirm(`Are you sure you want to delete the subtopic "${name}"?`)) return;

        try {
            setIsProcessingAction(true);
            await serviceFetch('aimaterials', `/api/admin/v8/subtopics/${subtopicId}`, { method: 'DELETE' });
            loadSubtopics(selectedTopicId!);
            if (selectedSubtopicId === subtopicId) {
                setSelectedSubtopicId(null);
            }
        } catch (err) {
            console.error('Error deleting subtopic', err);
            alert('Failed to delete subtopic');
        } finally {
            setIsProcessingAction(false);
        }
    };

    const handleRename = async () => {
        if (!itemToRename || !newName.trim()) return;

        const { id, type } = itemToRename;
        const endpoint = type === 'subject' ? `/api/admin/v8/subjects/${id}` :
            type === 'topic' ? `/api/admin/v8/topics/${id}` :
                `/api/admin/v8/subtopics/${id}`;

        try {
            setIsProcessingAction(true);
            await serviceFetch('aimaterials', endpoint, {
                method: 'PATCH',
                body: JSON.stringify({ name: newName.trim() })
            });

            if (type === 'subject') loadSubjects();
            else if (type === 'topic') loadTopics(selectedSubjectId!);
            else loadSubtopics(selectedTopicId!);

            setItemToRename(null);
            setNewName('');
        } catch (err) {
            console.error(`Error renaming ${type}`, err);
            alert(`Failed to rename ${type}`);
        } finally {
            setIsProcessingAction(false);
        }
    };

    const handleGenerateV8 = async (forceRegenerate = false) => {
        if (!selectedSubtopicId) return;

        setGenerating(true);
        setTaskStatus(null);
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

    const handleSaveConcept = async (conceptId: number, data: any) => {
        try {
            await serviceFetch('aimaterials', `/api/admin/v8/concepts/${conceptId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    title: data.summary,
                    bullets: data.html_content,
                    description: "" // Clear description to avoid duplication with bullets
                })
            });
            loadSubtopicContent(selectedSubtopicId!);
            setEditingConcept(null);
        } catch (err) {
            console.error('Error saving concept', err);
            alert('Failed to save concept');
        }
    };

    const handleSaveQuizQuestion = async (questionId: number, questionData: any) => {
        setIsSaving(true);
        try {
            await serviceFetch('aimaterials', `/api/admin/v8/quiz/${questionId}`, {
                method: 'PUT',
                body: JSON.stringify(questionData)
            });
            loadSubtopicContent(selectedSubtopicId!);
            setEditingQuiz(null);
        } catch (err) {
            console.error('Error saving quiz question', err);
            alert('Failed to save quiz question');
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveFlashcard = async (cardId: number, cardData: any) => {
        setIsSaving(true);
        try {
            await serviceFetch('aimaterials', `/api/admin/v8/flashcards/${cardId}`, {
                method: 'PUT',
                body: JSON.stringify(cardData)
            });
            loadSubtopicContent(selectedSubtopicId!);
            setEditingFlashcard(null);
        } catch (err) {
            console.error('Error saving flashcard', err);
            alert('Failed to save flashcard');
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveRealLifeImage = async (imageId: number, imageData: any) => {
        setIsSaving(true);
        try {
            await serviceFetch('aimaterials', `/api/admin/v8/reallife_images/${imageId}`, {
                method: 'PUT',
                body: JSON.stringify(imageData)
            });
            loadSubtopicContent(selectedSubtopicId!);
            setEditingRealLife(null);
        } catch (err) {
            console.error('Error saving real-life image', err);
            alert('Failed to save real-life image');
        } finally {
            setIsSaving(false);
        }
    };

    const handleRegenerateSVG = async (conceptId: number, prompt?: string) => {
        setIsRegeneratingSVG(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/v8/concepts/${conceptId}/regenerate-svg`, {
                method: 'POST',
                body: JSON.stringify({ prompt })
            });

            if (data.task_id) {
                setCurrentTaskId(data.task_id);
                setGenerating(true);
                setEditingSVGConcept(null);
                setCustomSVGPrompt('');
            }
        } catch (err) {
            console.error('Error regenerating SVG', err);
            alert('Failed to start SVG regeneration');
        } finally {
            setIsRegeneratingSVG(false);
        }
    };

    // Find selected subject
    const selectedSubject = subjects.find(s => s.id === selectedSubjectId);

    // Hierarchical Tree State
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set());
    const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());

    const { treeWithData, unmatched } = matchSubjectsToTree(subjects as any);

    const toggleLevel = (level: string) => {
        setExpandedLevels(prev => {
            const next = new Set(prev);
            if (next.has(level)) next.delete(level);
            else next.add(level);
            return next;
        });
    };

    const toggleSubject = (key: string) => {
        setExpandedSubjects(prev => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    };

    const filterMatches = (name: string) => {
        if (!searchQuery) return true;
        return name.toLowerCase().includes(searchQuery.toLowerCase());
    };

    const levelStats = (level: string) => {
        const subjectsInLevel = treeWithData[level];
        if (!subjectsInLevel) return { total: 0, withContent: 0 };
        let total = 0;
        let withContent = 0;
        for (const subjectData of Object.values(subjectsInLevel)) {
            const hasBoards = subjectData.boards.length > 0;
            if (hasBoards) {
                total += subjectData.boards.length;
                withContent += subjectData.boards.filter(b => b.dbSubject).length;
            } else {
                total += 1;
                if (subjectData.dbSubject) withContent += 1;
            }
        }
        return { total, withContent };
    };

    return (
        <div style={{
            display: 'flex',
            height: 'calc(100vh - 120px)', // Adjusted for header+padding
            background: premiumColors.sidebarBg,
            borderRadius: '16px', // Reduced for more space
            overflow: 'hidden',
            border: `1px solid ${premiumColors.border}`,
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05)',
            fontFamily: "'Outfit', sans-serif",
        }}>
            {/* Sidebar Pane: Subjects & Topics */}
            <div style={{
                width: isMobile ? '100%' : (isSidebarVisible ? '300px' : '0'), // Collapsible
                borderRight: isSidebarVisible ? `1px solid ${premiumColors.border}` : 'none',
                display: isMobile && !isSidebarVisible ? 'none' : 'flex',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                flexDirection: 'column',
                overflow: 'hidden',
                background: 'white',
                position: 'relative',
                zIndex: 20
            }}>
                {/* Subject Selector Header */}
                <div style={{
                    padding: '32px 24px 20px',
                    borderBottom: `1px solid ${premiumColors.border}`,
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Sparkles size={18} color="#be123c" /> Subjects
                        </h3>
                        <button
                            onClick={loadSubjects}
                            disabled={loadingSubjects}
                            style={{
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                color: '#64748b',
                                display: 'flex',
                                alignItems: 'center',
                                transition: 'transform 0.2s',
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.transform = 'rotate(180deg)')}
                            onMouseLeave={(e) => (e.currentTarget.style.transform = 'rotate(0deg)')}
                        >
                            <RefreshCw size={16} className={loadingSubjects ? 'animate-spin' : ''} />
                        </button>
                    </div>

                    {/* Search */}
                    <div style={{ position: 'relative' }}>
                        <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                        <input
                            type="text"
                            placeholder="Search subjects..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{
                                ...inputStyle,
                                paddingLeft: '34px',
                                fontSize: '0.85rem'
                            }}
                        />
                    </div>

                    {loadingSubjects ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: '12px', color: '#94a3b8' }}>
                            <Loader2 className="animate-spin" size={24} />
                            <span style={{ fontSize: '0.85rem' }}>Loading hierarchy...</span>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            {Object.entries(treeWithData).map(([level, subjectsMap]) => {
                                const stats = levelStats(level);
                                const isExpanded = expandedLevels.has(level);

                                const visibleSubjects = Object.entries(subjectsMap).filter(([name, data]) => {
                                    if (searchQuery) return filterMatches(name) || data.boards.some(b => filterMatches(b.name));
                                    return data.dbSubject || data.boards.some(b => b.dbSubject);
                                });

                                if (visibleSubjects.length === 0) return null;

                                return (
                                    <div key={level} style={{ marginBottom: '2px' }}>
                                        <button
                                            onClick={() => toggleLevel(level)}
                                            style={{
                                                width: '100%', padding: '10px', border: 'none',
                                                background: isExpanded ? '#fff1f2' : 'transparent',
                                                cursor: 'pointer', textAlign: 'left',
                                                display: 'flex', alignItems: 'center', gap: '8px',
                                                borderRadius: '10px', transition: 'all 0.2s',
                                            }}
                                        >
                                            {isExpanded ? <ChevronDown size={14} color="#be123c" /> : <ChevronRight size={14} color="#64748b" />}
                                            <Folder size={16} color={isExpanded ? "#be123c" : "#64748b"} />
                                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: isExpanded ? '#9f1239' : '#1e293b' }}>{level}</span>
                                            <span style={{
                                                marginLeft: 'auto', fontSize: '0.65rem', padding: '2px 6px',
                                                borderRadius: '8px', background: stats.withContent > 0 ? '#fee2e2' : '#f1f5f9',
                                                color: stats.withContent > 0 ? '#be123c' : '#94a3b8', fontWeight: 600,
                                            }}>
                                                {stats.withContent}/{stats.total}
                                            </span>
                                        </button>

                                        {isExpanded && (
                                            <div style={{ paddingLeft: '20px', marginLeft: '12px', borderLeft: '1px solid #fecaca', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                {visibleSubjects.map(([sName, sData]) => {
                                                    const hasBoards = sData.boards.length > 0;
                                                    const sKey = `${level}/${sName}`;
                                                    const isEx = expandedSubjects.has(sKey);

                                                    if (!hasBoards) {
                                                        const db = sData.dbSubject;
                                                        return (
                                                            <div
                                                                key={sKey}
                                                                onClick={() => db && setSelectedSubjectId(db.id)}
                                                                style={{
                                                                    display: 'flex', alignItems: 'center', gap: '8px',
                                                                    padding: '6px 10px', borderRadius: '8px',
                                                                    cursor: db ? 'pointer' : 'default',
                                                                    background: selectedSubjectId === db?.id ? '#fef2f2' : 'transparent',
                                                                    opacity: db ? 1 : 0.4,
                                                                    position: 'relative'
                                                                }}
                                                            >
                                                                <FileText size={14} color={selectedSubjectId === db?.id ? '#be123c' : '#94a3b8'} />
                                                                <span style={{ fontSize: '0.8rem', fontWeight: selectedSubjectId === db?.id ? 700 : 500, color: selectedSubjectId === db?.id ? '#9f1239' : '#475569' }}>
                                                                    {db?.name || sName}
                                                                </span>
                                                                {db && selectedSubjectId === db.id && (
                                                                    <div style={{ display: 'flex', gap: '4px', marginLeft: 'auto' }}>
                                                                        <button onClick={(e) => { e.stopPropagation(); setItemToRename({ id: db.id, type: 'subject', name: db.name }); setNewName(db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8' }}><Edit2 size={12} /></button>
                                                                        <button onClick={(e) => { e.stopPropagation(); handleDeleteSubject(db.id, db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#f87171' }}><Trash2 size={12} /></button>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    }

                                                    const boardsWithC = sData.boards.filter(b => b.dbSubject).length;
                                                    return (
                                                        <div key={sKey}>
                                                            <button
                                                                onClick={() => toggleSubject(sKey)}
                                                                style={{
                                                                    width: '100%', padding: '6px 10px', border: 'none',
                                                                    background: isEx ? '#fff5f5' : 'transparent',
                                                                    cursor: 'pointer', textAlign: 'left',
                                                                    display: 'flex', alignItems: 'center', gap: '6px',
                                                                    borderRadius: '8px',
                                                                }}
                                                            >
                                                                {isEx ? <ChevronDown size={12} color="#be123c" /> : <ChevronRight size={12} color="#94a3b8" />}
                                                                <Folder size={14} color={boardsWithC > 0 ? "#be123c" : "#cbd5e1"} />
                                                                <span style={{ fontSize: '0.8rem', color: boardsWithC > 0 ? '#1e293b' : '#94a3b8', fontWeight: 600 }}>{sName}</span>
                                                            </button>
                                                            {isEx && (
                                                                <div style={{ paddingLeft: '16px', marginLeft: '10px', borderLeft: '1px solid #fee2e2', marginTop: '2px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                                    {sData.boards.map(board => {
                                                                        const db = board.dbSubject;
                                                                        return (
                                                                            <div
                                                                                key={board.name}
                                                                                onClick={() => db && setSelectedSubjectId(db.id)}
                                                                                style={{
                                                                                    display: 'flex', alignItems: 'center', gap: '6px',
                                                                                    padding: '4px 8px', borderRadius: '6px',
                                                                                    cursor: db ? 'pointer' : 'default',
                                                                                    background: selectedSubjectId === db?.id ? '#fef2f2' : 'transparent',
                                                                                    opacity: db ? 1 : 0.4
                                                                                }}
                                                                            >
                                                                                <FileText size={12} color={selectedSubjectId === db?.id ? '#be123c' : '#cbd5e1'} />
                                                                                <span style={{ fontSize: '0.75rem', fontWeight: selectedSubjectId === db?.id ? 700 : 500, color: selectedSubjectId === db?.id ? '#9f1239' : '#64748b' }}>
                                                                                    {db?.name || board.name}
                                                                                </span>
                                                                                {db && selectedSubjectId === db.id && (
                                                                                    <div style={{ display: 'flex', gap: '4px', marginLeft: 'auto' }}>
                                                                                        <button onClick={(e) => { e.stopPropagation(); setItemToRename({ id: db.id, type: 'subject', name: db.name }); setNewName(db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8' }}><Edit2 size={10} /></button>
                                                                                        <button onClick={(e) => { e.stopPropagation(); handleDeleteSubject(db.id, db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#f87171' }}><Trash2 size={10} /></button>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })}
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}

                            {/* Unmatched Subjects */}
                            {unmatched.length > 0 && (
                                <div style={{ marginTop: '12px' }}>
                                    <div style={{ padding: '8px 10px', display: 'flex', alignItems: 'center', gap: '8px', background: '#f8fafc', borderRadius: '10px' }}>
                                        <FolderOpen size={16} color="#64748b" />
                                        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#475569' }}>Unlinked</span>
                                        <span style={{ marginLeft: 'auto', fontSize: '0.65rem', padding: '2px 6px', borderRadius: '8px', background: '#e2e8f0', color: '#64748b' }}>{unmatched.length}</span>
                                    </div>
                                    <div style={{ paddingLeft: '12px', marginLeft: '12px', borderLeft: '1px solid #e2e8f0', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                        {unmatched.map(db => (
                                            <div
                                                key={db.id}
                                                onClick={() => setSelectedSubjectId(db.id)}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: '8px',
                                                    padding: '6px 10px', borderRadius: '8px',
                                                    cursor: 'pointer',
                                                    background: selectedSubjectId === db.id ? '#f3f4f6' : 'transparent',
                                                }}
                                            >
                                                <FileText size={14} color={selectedSubjectId === db.id ? '#475569' : '#94a3b8'} />
                                                <span style={{ fontSize: '0.8rem', fontWeight: selectedSubjectId === db.id ? 700 : 500, color: selectedSubjectId === db.id ? '#1e293b' : '#64748b' }}>{db.name}</span>
                                                {selectedSubjectId === db.id && (
                                                    <div style={{ display: 'flex', gap: '4px', marginLeft: 'auto' }}>
                                                        <button onClick={(e) => { e.stopPropagation(); setItemToRename({ id: db.id, type: 'subject', name: db.name }); setNewName(db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#94a3b8' }}><Edit2 size={12} /></button>
                                                        <button onClick={(e) => { e.stopPropagation(); handleDeleteSubject(db.id, db.name); }} style={{ padding: '2px', border: 'none', background: 'none', cursor: 'pointer', color: '#f87171' }}><Trash2 size={12} /></button>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
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
                                    <div
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
                                        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#374151', flex: 1 }}>
                                            {topic.topic_id} - {topic.name}
                                        </span>

                                        <div style={{ display: 'flex', gap: '4px', marginRight: '8px' }}>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setItemToRename({ id: topic.id, type: 'topic', name: topic.name }); setNewName(topic.name); }}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }}
                                            >
                                                <Edit size={12} />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDeleteTopic(topic.id, topic.name); }}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#ef4444' }}
                                            >
                                                <XCircle size={12} />
                                            </button>
                                        </div>
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
                                    </div>

                                    {/* Subtopics */}
                                    {selectedTopicId === topic.id && (
                                        <div style={{ paddingLeft: '20px', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                            {loadingSubtopics ? (
                                                <div style={{ padding: '10px', textAlign: 'center' }}>
                                                    <Loader2 size={16} className="animate-spin" />
                                                </div>
                                            ) : subtopics.map((subtopic) => (
                                                <div
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
                                                    <span style={{ fontSize: '0.8rem', color: '#4b5563', flex: 1 }}>
                                                        {subtopic.subtopic_id} {subtopic.name}
                                                    </span>

                                                    <div style={{ display: 'flex', gap: '4px', marginRight: '4px' }}>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); setItemToRename({ id: subtopic.id, type: 'subtopic', name: subtopic.name }); setNewName(subtopic.name); }}
                                                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#64748b' }}
                                                        >
                                                            <Edit size={12} />
                                                        </button>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); handleDeleteSubtopic(subtopic.id, subtopic.name); }}
                                                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', color: '#ef4444' }}
                                                        >
                                                            <XCircle size={12} />
                                                        </button>
                                                    </div>
                                                    {subtopic.v8_concepts_count > 0 && (
                                                        <CheckCircle2 size={12} color="#22c55e" style={{ marginLeft: 'auto' }} />
                                                    )}
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

            {/* Main Content Area - Right Pane */}
            <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                background: premiumColors.bg,
                position: 'relative'
            }}>
                {/* Sidebar Toggle Button */}
                {!isMobile && (
                    <button
                        onClick={() => setIsSidebarVisible(!isSidebarVisible)}
                        style={{
                            position: 'absolute',
                            left: '0',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            zIndex: 100,
                            width: '24px',
                            height: '48px',
                            background: 'white',
                            border: `1px solid ${premiumColors.border}`,
                            borderLeft: 'none',
                            borderRadius: '0 12px 12px 0',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            color: premiumColors.primary,
                            boxShadow: '4px 0 10px rgba(0,0,0,0.05)',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                    >
                        {isSidebarVisible ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
                    </button>
                )}
                {/* Scrollable Content Container */}
                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: isMobile ? '16px' : (subtopicStatus && fullSubtopic ? '0' : '40px'), // Reduced padding when content is shown
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '40px'
                }}>
                    {!selectedSubtopicId ? (
                        <div style={{ ...cardStyle(isMobile), padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                            <Eye size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
                            <div style={{ fontSize: '1rem' }}>Select a subtopic to view V8 content</div>
                        </div>
                    ) : loadingContent ? (
                        <div style={{ ...cardStyle(isMobile), padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                            <Loader2 size={32} className="animate-spin" />
                        </div>
                    ) : subtopicStatus && !subtopicStatus.has_concepts ? (
                        <div style={{ ...cardStyle(isMobile), padding: '40px 20px', textAlign: 'center' }}>
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
                            isParentSidebarVisible={isSidebarVisible}
                            onToggleParentSidebar={() => setIsSidebarVisible(!isSidebarVisible)}
                            onRegenerate={() => openGenerateModal(true)}
                            regenerating={generating}
                            onEditConcept={(concept: any) => setEditingConcept(concept)}
                            onEditQuiz={(q: any) => setEditingQuiz(q)}
                            onEditFlashcard={(c: any) => setEditingFlashcard(c)}
                            onEditRealLife={(img: any) => setEditingRealLife(img)}
                            onEditSVG={(concept: any) => { setEditingSVGConcept(concept); setCustomSVGPrompt(''); }}
                        />
                    ) : null}
                </div>
            </div>

            {/* Modals & Overlays - Correctly Scoped */}
            {editingConcept && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000,
                    padding: isMobile ? '0' : '40px'
                }}>
                    <div style={{ width: '100%', maxWidth: '1000px', height: '100%', maxHeight: '90vh' }}>
                        <ChunkEditor
                            content={{
                                id: editingConcept.id,
                                subtopic_id: parseInt(selectedSubtopicId || '0'),
                                subtopic_name: fullSubtopic?.name || subtopicStatus?.subtopic_id,
                                html_content: (() => {
                                    const desc = editingConcept.description ? `<p style="font-weight: 600; color: #1e293b; font-size: 1.1rem; margin-bottom: 20px;">${editingConcept.description}</p>` : '';
                                    const bullets = editingConcept.generated?.bullets || '';
                                    return desc + bullets;
                                })(),
                                summary: editingConcept.title,
                                key_terms: ''
                            }}
                            onClose={() => setEditingConcept(null)}
                            onSave={(data) => handleSaveConcept(editingConcept.id, data)}
                        />
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

            {itemToRename && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2100
                }}>
                    <div style={{ background: 'white', padding: '32px', borderRadius: '24px', width: '400px', boxShadow: '0 30px 60px -12px rgba(0,0,0,0.15)' }}>
                        <h3 style={{ margin: '0 0 20px 0', fontSize: '1.25rem', fontWeight: 800 }}>Rename {itemToRename.type}</h3>
                        <input
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            style={{ ...inputStyle, marginBottom: '24px' }}
                            placeholder={`Enter new ${itemToRename.type} name`}
                            autoFocus
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                            <button onClick={() => setItemToRename(null)} style={buttonSecondary} disabled={isProcessingAction}>Cancel</button>
                            <button onClick={handleRename} style={buttonPrimary} disabled={isProcessingAction || !newName.trim() || newName.trim() === itemToRename.name}>
                                {isProcessingAction ? 'Renaming...' : 'Rename'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {editingSVGConcept && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2200,
                    padding: isMobile ? '0' : '20px'
                }}>
                    <div style={{ background: 'white', padding: '40px', borderRadius: '32px', width: '100%', maxWidth: '550px', boxShadow: '0 40px 80px -20px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>Refine Visualization</h3>
                            <button onClick={() => setEditingSVGConcept(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: premiumColors.textSoft }}><XCircle size={28} /></button>
                        </div>
                        <div style={{ marginBottom: '24px' }}>
                            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem', color: premiumColors.textSoft }}>Context</label>
                            <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '16px', border: `1px solid ${premiumColors.border}`, fontSize: '0.9rem', color: premiumColors.text, minHeight: '60px', lineHeight: 1.5 }}>
                                {editingSVGConcept.description}
                            </div>
                        </div>
                        <div style={{ marginBottom: '32px' }}>
                            <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem', color: premiumColors.accent }}>Design Guidance</label>
                            <textarea
                                value={customSVGPrompt}
                                onChange={(e) => setCustomSVGPrompt(e.target.value)}
                                placeholder="e.g. Enhance mechanical detail, use a warm color palette, or slow down the animation..."
                                style={{ ...inputStyle, minHeight: '140px', background: 'white' }}
                            />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
                            <button onClick={() => setEditingSVGConcept(null)} style={buttonSecondary}>Cancel</button>
                            <button
                                onClick={() => handleRegenerateSVG(editingSVGConcept.id, customSVGPrompt)}
                                style={buttonPrimary}
                                disabled={isRegeneratingSVG}
                            >
                                {isRegeneratingSVG ? (
                                    <>
                                        <Loader2 size={18} className="animate-spin" />
                                        <span>Re-imagining...</span>
                                    </>
                                ) : (
                                    <>
                                        <RefreshCw size={18} />
                                        <span>Regenerate SVG</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {editingQuiz && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2300,
                    padding: isMobile ? '0' : '40px'
                }}>
                    <div style={{ background: 'white', padding: '40px', borderRadius: '32px', width: '100%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 30px 60px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>Refine Question</h3>
                            <button onClick={() => setEditingQuiz(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: premiumColors.textSoft }}><XCircle size={28} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Question Prompt</label>
                                <textarea
                                    value={editingQuiz.question_text}
                                    onChange={(e) => setEditingQuiz({ ...editingQuiz, question_text: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '100px' }}
                                />
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                {Object.keys(editingQuiz.options || {}).map((key) => (
                                    <div key={key}>
                                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.8rem', fontWeight: 600, color: premiumColors.textSoft }}>Option {key}</label>
                                        <input
                                            value={editingQuiz.options[key]}
                                            onChange={(e) => {
                                                const newOpts = { ...editingQuiz.options, [key]: e.target.value };
                                                setEditingQuiz({ ...editingQuiz, options: newOpts });
                                            }}
                                            style={inputStyle}
                                        />
                                    </div>
                                ))}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Correct Answer</label>
                                    <select
                                        value={editingQuiz.correct_answer}
                                        onChange={(e) => setEditingQuiz({ ...editingQuiz, correct_answer: e.target.value })}
                                        style={inputStyle}
                                    >
                                        {['A', 'B', 'C', 'D'].map(key => (
                                            <option key={key} value={key}>Option {key}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Explanation</label>
                                    <textarea
                                        value={editingQuiz.explanation || ''}
                                        onChange={(e) => setEditingQuiz({ ...editingQuiz, explanation: e.target.value })}
                                        style={{ ...inputStyle, minHeight: '60px' }}
                                    />
                                </div>
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px', marginTop: '40px' }}>
                            <button onClick={() => setEditingQuiz(null)} style={buttonSecondary}>Cancel</button>
                            <button
                                onClick={() => handleSaveQuizQuestion(editingQuiz.id, editingQuiz)}
                                style={buttonPrimary}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Synchronizing...' : 'Update Question'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {editingFlashcard && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2400,
                    padding: isMobile ? '0' : '40px'
                }}>
                    <div style={{ background: 'white', padding: '40px', borderRadius: '32px', width: '100%', maxWidth: '600px', boxShadow: '0 30px 60px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>Edit Flashcard</h3>
                            <button onClick={() => setEditingFlashcard(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: premiumColors.textSoft }}><XCircle size={28} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Front (Concept)</label>
                                <textarea
                                    value={editingFlashcard.front}
                                    onChange={(e) => setEditingFlashcard({ ...editingFlashcard, front: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '100px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Back (Explanation)</label>
                                <textarea
                                    value={editingFlashcard.back}
                                    onChange={(e) => setEditingFlashcard({ ...editingFlashcard, back: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '120px' }}
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px', marginTop: '40px' }}>
                            <button onClick={() => setEditingFlashcard(null)} style={buttonSecondary}>Cancel</button>
                            <button
                                onClick={() => handleSaveFlashcard(editingFlashcard.id, editingFlashcard)}
                                style={buttonPrimary}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Synchronizing...' : 'Update Card'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {editingRealLife && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2500,
                    padding: isMobile ? '0' : '40px'
                }}>
                    <div style={{ background: 'white', padding: '40px', borderRadius: '32px', width: '100%', maxWidth: '650px', boxShadow: '0 30px 60px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>Refine Real-world Insight</h3>
                            <button onClick={() => setEditingRealLife(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: premiumColors.textSoft }}><XCircle size={28} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Insight Title</label>
                                <input
                                    value={editingRealLife.title}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, title: e.target.value })}
                                    style={inputStyle}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Description</label>
                                <textarea
                                    value={editingRealLife.description}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, description: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '120px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '10px', fontWeight: 700, fontSize: '0.9rem' }}>Application Category</label>
                                <input
                                    value={editingRealLife.image_type || ''}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, image_type: e.target.value })}
                                    style={inputStyle}
                                    placeholder="e.g. Industrial Automation, Aerospace Engineering..."
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px', marginTop: '40px' }}>
                            <button onClick={() => setEditingRealLife(null)} style={buttonSecondary}>Cancel</button>
                            <button
                                onClick={() => handleSaveRealLifeImage(editingRealLife.id, editingRealLife)}
                                style={buttonPrimary}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Synchronizing...' : 'Update Insight'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const V8ContentDetails = ({
    status,
    subtopic,
    onRegenerate,
    regenerating,
    onEditConcept,
    onEditQuiz,
    onEditFlashcard,
    onEditRealLife,
    onEditSVG,
    isParentSidebarVisible,
    onToggleParentSidebar
}: {
    status: V8SubtopicStatus;
    subtopic: V8FullSubtopic;
    onRegenerate: () => void;
    regenerating: boolean;
    onEditConcept: (concept: any) => void;
    onEditQuiz: (question: any) => void;
    onEditFlashcard: (card: any) => void;
    onEditRealLife: (image: any) => void;
    onEditSVG: (concept: any) => void;
    isParentSidebarVisible?: boolean;
    onToggleParentSidebar?: () => void;
}) => {
    const [activeTab, setActiveTab] = useState<'concepts' | 'quiz' | 'flashcards' | 'reallife'>('concepts');
    const [activeConceptId, setActiveConceptId] = useState<number | null>(null);
    const [flippedCards, setFlippedCards] = useState<Record<number, boolean>>({});
    const [isTocVisible, setIsTocVisible] = useState(true); // Internal TOC state

    // Initial concept selection
    useEffect(() => {
        if (subtopic.concepts && subtopic.concepts.length > 0 && activeConceptId === null) {
            setActiveConceptId(subtopic.concepts[0].id);
        }
    }, [subtopic.concepts]);

    if (!subtopic) return null;

    const toggleCard = (cardId: number) => {
        setFlippedCards(prev => ({ ...prev, [cardId]: !prev[cardId] }));
    };

    return (
        <>
            <style>{`
            @keyframes v8FadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `}</style>
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                maxHeight: '94vh',
                width: '100%',
                background: '#fcfaf7', // Soft background
                borderRadius: '32px', // More rounded
                overflow: 'hidden',
                boxShadow: '0 30px 60px -12px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0,0,0,0.02)',
                fontFamily: "'Outfit', sans-serif",
                color: '#1a1a1b',
                transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)'
            }}>
                {/* V8 Header */}
                <div style={{
                    padding: '24px 40px',
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(12px)',
                    borderBottom: '1px solid rgba(0,0,0,0.04)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    zIndex: 10
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                        <div style={{
                            width: '44px', height: '44px', background: '#1e293b',
                            borderRadius: '14px', display: 'grid', placeItems: 'center',
                            color: '#927559', fontWeight: 800, fontSize: '15px',
                            boxShadow: '0 8px 16px rgba(30, 41, 59, 0.2)',
                            cursor: 'pointer'
                        }} onClick={onToggleParentSidebar} title={isParentSidebarVisible ? "Hide Side Panel" : "Show Side Panel"}>
                            {isParentSidebarVisible ? "V8" : <Menu size={20} />}
                        </div>
                        <div>
                            <div style={{ fontWeight: 800, fontSize: '1.4rem', color: '#1e293b', letterSpacing: '-0.03em', lineHeight: 1.2 }}>{subtopic.name}</div>
                            <div style={{ fontSize: '0.75rem', color: '#927559', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '2px' }}>Interactive Designer Preview</div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                        {activeTab === 'concepts' && (
                            <button
                                onClick={() => setIsTocVisible(!isTocVisible)}
                                style={{
                                    padding: '10px 18px',
                                    borderRadius: '14px',
                                    border: '1.5px solid #e2e8f0',
                                    background: 'white',
                                    color: isTocVisible ? '#927559' : '#64748b',
                                    fontSize: '0.85rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    transition: 'all 0.2s'
                                }}
                            >
                                <ListOrdered size={18} />
                                {isTocVisible ? 'Hide Index' : 'Show Index'}
                            </button>
                        )}
                        <button
                            onClick={onRegenerate}
                            disabled={regenerating}
                            className="hover:scale-105 transition-transform"
                            style={{
                                padding: '10px 20px',
                                borderRadius: '14px',
                                border: '1.5px solid #7c3aed',
                                background: regenerating ? '#f8fafc' : 'white',
                                color: '#7c3aed',
                                fontSize: '0.85rem',
                                fontWeight: 700,
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                boxShadow: '0 4px 6px -1px rgba(124, 58, 237, 0.1)'
                            }}
                        >
                            {regenerating ? (
                                <Loader2 size={18} className="animate-spin" color="#7c3aed" />
                            ) : (
                                <RefreshCw size={18} color="#7c3aed" strokeWidth={2.5} />
                            )}
                            {regenerating ? 'Syncing...' : 'Regenerate Chunk'}
                        </button>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <div style={{
                    padding: '16px 40px',
                    background: 'rgba(248, 250, 252, 0.5)',
                    display: 'flex',
                    gap: '8px',
                    borderBottom: '1px solid rgba(0,0,0,0.04)',
                    justifyContent: 'center'
                }}>
                    {[
                        { id: 'concepts', label: 'Learn', Icon: Layers, color: '#927559' }, // Theme color
                        { id: 'quiz', label: 'Quiz', Icon: HelpCircle, color: '#0f172a' },
                        { id: 'flashcards', label: 'Cards', Icon: FileText, color: '#0f172a' },
                        { id: 'reallife', label: 'Real Life', Icon: ImageIcon, color: '#0f172a' }
                    ].map(tab => {
                        const TabIcon = tab.Icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                style={{
                                    padding: '10px 24px',
                                    borderRadius: '14px',
                                    border: 'none',
                                    background: isActive ? 'white' : 'transparent',
                                    color: isActive ? '#927559' : '#64748b',
                                    fontWeight: isActive ? 800 : 600,
                                    fontSize: '0.95rem',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    boxShadow: isActive ? '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)' : 'none',
                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    transform: isActive ? 'scale(1.02)' : 'scale(1)',
                                }}
                            >
                                <TabIcon size={20} color={isActive ? '#927559' : '#94a3b8'} strokeWidth={2.5} />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* Main Content Area */}
                <div style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
                    {activeTab === 'concepts' && (
                        <>
                            {/* Inner Sidebar (TOC) */}
                            <aside style={{
                                width: isTocVisible ? '220px' : '0', // Collapsible
                                opacity: isTocVisible ? 1 : 0,
                                transform: isTocVisible ? 'translateX(0)' : 'translateX(-20px)',
                                pointerEvents: isTocVisible ? 'auto' : 'none',
                                borderRight: isTocVisible ? '1px solid rgba(0,0,0,0.04)' : 'none',
                                padding: isTocVisible ? '24px 16px' : '0',
                                overflow: 'hidden',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                background: 'rgba(255, 255, 255, 0.5)',
                            }}>
                                <div style={{
                                    fontSize: '0.7rem',
                                    fontWeight: 800,
                                    color: '#927559',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.12em',
                                    marginBottom: '20px',
                                    paddingLeft: '12px'
                                }}>Table of Contents</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                    {subtopic.concepts?.map(concept => (
                                        <button
                                            key={concept.id}
                                            onClick={() => {
                                                setActiveConceptId(concept.id);
                                                document.getElementById(`concept-${concept.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                            }}
                                            style={{
                                                padding: '12px 16px',
                                                borderRadius: '14px',
                                                border: 'none',
                                                background: activeConceptId === concept.id ? 'rgba(146, 117, 89, 0.08)' : 'transparent',
                                                color: activeConceptId === concept.id ? '#1e293b' : '#64748b',
                                                textAlign: 'left',
                                                fontSize: '0.9rem',
                                                fontWeight: activeConceptId === concept.id ? 700 : 500,
                                                cursor: 'pointer',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '12px',
                                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                                boxShadow: activeConceptId === concept.id ? 'inset 0 0 0 1px rgba(146, 117, 89, 0.15)' : 'none'
                                            }}
                                        >
                                            <span style={{ fontSize: '1.2rem', opacity: activeConceptId === concept.id ? 1 : 0.6 }}>{concept.icon || '📚'}</span>
                                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{concept.title}</span>
                                        </button>
                                    ))}
                                </div>
                            </aside>

                            {/* Concept Display */}
                            <div style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', background: '#fcfaf7' }} id="concept-scroll-area">
                                {subtopic.concepts?.map(concept => {
                                    const sanitizedSvgMarkup = sanitizeSvgMarkup(concept.generated?.svg);
                                    const sanitizedBulletsMarkup = sanitizeHtmlMarkup(concept.generated?.bullets)
                                        .replace(/\$\$([^$]+)\$\$/g, '<span style="font-family: serif; font-style: italic; color: #927559;">$1</span>')
                                        .replace(/\$([^$]+)\$/g, '<span style="font-family: serif; font-style: italic; color: #927559;">$1</span>');
                                    return (
                                    <section key={concept.id} id={`concept-${concept.id}`} style={{ marginBottom: '80px', animation: 'fadeIn 0.8s ease' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                                            <h3 style={{ fontSize: '2rem', fontWeight: 800, color: '#1e293b', margin: 0, display: 'flex', alignItems: 'center', gap: '16px', letterSpacing: '-0.04em' }}>
                                                <span style={{ opacity: 0.9 }}>{concept.icon || '📚'}</span>
                                                {concept.title}
                                            </h3>
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                <button
                                                    onClick={() => onEditSVG(concept)}
                                                    style={{
                                                        padding: '10px 18px', borderRadius: '12px', border: '1px solid #e2e8f0',
                                                        background: 'white', cursor: 'pointer', color: '#7c3aed',
                                                        display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 700,
                                                        transition: 'all 0.2s'
                                                    }}
                                                    className="hover:shadow-md hover:border-violet-100"
                                                >
                                                    <Sparkles size={16} /> Refine SVG
                                                </button>
                                                <button
                                                    onClick={() => onEditConcept(concept)}
                                                    style={{
                                                        padding: '10px 18px', borderRadius: '12px', border: '1px solid #e2e8f0',
                                                        background: 'white', cursor: 'pointer', color: '#1e293b',
                                                        display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 700,
                                                        transition: 'all 0.2s'
                                                    }}
                                                    className="hover:shadow-md"
                                                >
                                                    <Edit2 size={16} /> Edit Content
                                                </button>
                                            </div>
                                        </div>

                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: (isTocVisible || isParentSidebarVisible) ? '1.2fr 1fr' : '1fr 1fr',
                                            gap: '40px',
                                            alignItems: 'stretch'
                                        }}>
                                            {/* Left: Text */}
                                            <article style={{
                                                background: 'rgba(255, 255, 255, 0.8)', padding: '32px', borderRadius: '28px',
                                                border: '1px solid rgba(0,0,0,0.04)', boxShadow: '0 10px 30px -5px rgba(0,0,0,0.03)',
                                                backdropFilter: 'blur(8px)'
                                            }}>
                                                <div style={{ fontSize: '1.05rem', lineHeight: 1.9, color: '#334155' }}>
                                                    {concept.description && <p style={{ marginBottom: '24px', fontWeight: 700, color: '#1a1a1b', fontSize: '1.2rem', letterSpacing: '-0.01em' }}>{concept.description}</p>}
                                                    {sanitizedBulletsMarkup && (
                                                        <div
                                                            dangerouslySetInnerHTML={{
                                                                __html: sanitizedBulletsMarkup
                                                            }}
                                                            style={{
                                                                fontSize: '1.05rem',
                                                                color: '#475569'
                                                            }}
                                                        />
                                                    )}
                                                </div>
                                            </article>

                                            {/* Right: Visual */}
                                            <div style={{
                                                background: 'rgba(252, 250, 247, 0.7)', padding: '32px', borderRadius: '28px',
                                                border: '1px solid rgba(0,0,0,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                minHeight: '500px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.01)', position: 'relative',
                                                overflow: 'hidden'
                                            }}>
                                                <div style={{ background: 'white', borderRadius: '20px', padding: '24px', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(0,0,0,0.03)', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.01)' }}>
                                                    {sanitizedSvgMarkup ? (
                                                        <img
                                                            src={svgMarkupToDataUrl(sanitizedSvgMarkup)}
                                                            alt={`${concept.title} diagram`}
                                                            style={{
                                                                width: '100%',
                                                                height: '100%',
                                                                objectFit: 'contain'
                                                            }}
                                                        />
                                                    ) : (
                                                        <div style={{ opacity: 0.2, textAlign: 'center' }}>
                                                            <Sparkles size={64} style={{ marginBottom: '20px', color: '#927559' }} />
                                                            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Designer Visual Space</div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </section>
                                );
                                })}
                            </div>
                        </>
                    )}

                    {activeTab === 'quiz' && (
                        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', display: 'flex', flexDirection: 'column', gap: '32px', background: '#fcfaf7' }}>
                            <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                                <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px', letterSpacing: '-0.04em' }}>❓ Practice Assessment</h2>
                                <p style={{ color: '#64748b', fontSize: '0.95rem', fontWeight: 500 }}>Validating knowledge transfer through curated questions</p>
                            </div>
                            {subtopic.quiz?.map((q, idx) => (
                                <div key={idx} style={{
                                    background: 'white', borderRadius: '32px', padding: '48px',
                                    border: '1px solid rgba(0,0,0,0.03)', boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.06)'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                                        <div style={{ display: 'flex', gap: '12px' }}>
                                            <span style={{
                                                background: '#1e293b', color: 'white', padding: '6px 16px',
                                                borderRadius: '999px', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em'
                                            }}>Question {q.question_num || idx + 1}</span>
                                            {q.difficulty && <span style={{
                                                fontSize: '0.75rem', padding: '6px 16px', borderRadius: '999px', fontWeight: 800,
                                                background: q.difficulty === 'easy' ? '#ecfdf5' : q.difficulty === 'hard' ? '#fef2f2' : '#fffbeb',
                                                color: q.difficulty === 'easy' ? '#065f46' : q.difficulty === 'hard' ? '#991b1b' : '#92400e',
                                                textTransform: 'uppercase', letterSpacing: '0.05em'
                                            }}>{q.difficulty}</span>}
                                        </div>
                                        <button
                                            onClick={() => onEditQuiz(q)}
                                            style={{ background: 'rgba(30, 41, 59, 0.05)', border: 'none', width: '36px', height: '36px', borderRadius: '10px', display: 'grid', placeItems: 'center', cursor: 'pointer', color: '#64748b' }}
                                        >
                                            <Edit2 size={16} />
                                        </button>
                                    </div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#1e293b', marginBottom: '32px', lineHeight: 1.4, letterSpacing: '-0.02em' }}>{q.question_text}</div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                        {Object.entries((() => {
                                            if (typeof q.options === 'string') {
                                                try { return JSON.parse(q.options); } catch { return {}; }
                                            }
                                            return q.options || {};
                                        })()).map(([key, val]) => (
                                            <div key={key} style={{
                                                padding: '20px 24px', borderRadius: '20px', border: '2px solid',
                                                borderColor: key === q.correct_answer ? '#059669' : 'rgba(0,0,0,0.03)',
                                                background: key === q.correct_answer ? 'rgba(5, 150, 105, 0.04)' : 'white',
                                                fontSize: '1.05rem', fontWeight: 600, color: '#1e293b',
                                                display: 'flex', alignItems: 'center', gap: '12px',
                                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                                            }}>
                                                <strong style={{ color: key === q.correct_answer ? '#065f46' : '#927559', fontSize: '1.1rem' }}>{key}.</strong> {val as string}
                                                {key === q.correct_answer && <CheckCircle2 size={18} style={{ marginLeft: 'auto', color: '#059669' }} />}
                                            </div>
                                        ))}
                                    </div>
                                    {q.explanation && (
                                        <div style={{
                                            marginTop: '32px', padding: '24px 32px', background: 'rgba(146, 117, 89, 0.05)',
                                            borderRadius: '20px', borderLeft: '5px solid #927559', fontSize: '1rem', color: '#475569', lineHeight: 1.7
                                        }}>
                                            <div style={{ fontWeight: 800, color: '#927559', marginBottom: '8px', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.1em' }}>Explanation</div>
                                            {q.explanation}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'flashcards' && (
                        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', background: '#fcfaf7' }}>
                            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                                <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px', letterSpacing: '-0.04em' }}>⚡ Flashcards</h2>
                                <p style={{ color: '#64748b', fontSize: '0.95rem', fontWeight: 500 }}>Micro-learning cards for rapid concept recall</p>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '32px' }}>
                                {subtopic.flashcards?.map((card, idx) => (
                                    <div
                                        key={idx}
                                        style={{ height: '300px', perspective: '1200px', cursor: 'pointer' }}
                                        onClick={() => toggleCard(idx)}
                                    >
                                        <div style={{
                                            position: 'relative', width: '100%', height: '100%',
                                            transition: 'transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                            transformStyle: 'preserve-3d',
                                            transform: flippedCards[idx] ? 'rotateY(180deg)' : 'rotateY(0deg)',
                                            borderRadius: '28px',
                                            boxShadow: '0 15px 35px -5px rgba(0,0,0,0.06)'
                                        }}>
                                            {/* Front */}
                                            <div style={{
                                                position: 'absolute', width: '100%', height: '100%',
                                                backfaceVisibility: 'hidden', borderRadius: '28px',
                                                padding: '40px', display: 'flex', flexDirection: 'column',
                                                justifyContent: 'center', alignItems: 'center', textAlign: 'center',
                                                background: 'white', border: '1px solid rgba(0,0,0,0.03)'
                                            }}>
                                                <div style={{ position: 'absolute', top: '24px', right: '24px' }}>
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); onEditFlashcard(card); }}
                                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cbd5e1' }}
                                                    >
                                                        <Edit2 size={16} />
                                                    </button>
                                                </div>
                                                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', lineHeight: 1.3, letterSpacing: '-0.02em' }}>{card.front}</div>
                                                <div style={{ marginTop: '24px', fontSize: '0.75rem', fontWeight: 800, color: '#927559', textTransform: 'uppercase', letterSpacing: '0.1em', opacity: 0.5 }}>Tap to reveal</div>
                                            </div>
                                            {/* Back */}
                                            <div style={{
                                                position: 'absolute', width: '100%', height: '100%',
                                                backfaceVisibility: 'hidden', borderRadius: '28px',
                                                padding: '40px', display: 'flex', flexDirection: 'column',
                                                justifyContent: 'center', alignItems: 'center', textAlign: 'center',
                                                background: '#1e293b', color: 'white', transform: 'rotateY(180deg)'
                                            }}>
                                                <div style={{ fontSize: '1.1rem', fontWeight: 500, lineHeight: 1.6, color: 'rgba(255,255,255,0.9)' }}>{card.back}</div>
                                                <div style={{ marginTop: '24px', fontSize: '0.75rem', fontWeight: 800, color: '#927559', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Solution</div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'reallife' && (
                        <div style={{ flex: 1, overflowY: 'auto', padding: '40px 60px', background: '#fcfaf7' }}>
                            <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                                <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px', letterSpacing: '-0.04em' }}>🌍 Real Life Applications</h2>
                                <p style={{ color: '#64748b', fontSize: '0.95rem', fontWeight: 500 }}>Connecting theoretical concepts to tangible world examples</p>
                            </div>
                            {subtopic.reallife_images && subtopic.reallife_images.length > 0 ? (
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '48px', maxWidth: '1200px', margin: '0 auto' }}>
                                    {subtopic.reallife_images.map((item, idx) => (
                                        <div key={idx} style={{
                                            background: 'white', borderRadius: '40px', padding: '48px',
                                            border: '1px solid rgba(0,0,0,0.03)', boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.08)'
                                        }}>
                                            <div style={{ display: 'flex', gap: '60px', alignItems: 'flex-start' }}>
                                                <div style={{
                                                    width: '440px', height: '320px', flexShrink: 0, borderRadius: '32px',
                                                    overflow: 'hidden', background: '#f1f5f9', boxShadow: '0 20px 40px -10px rgba(0,0,0,0.1)'
                                                }}>
                                                    {item.image_url ? (
                                                        <img src={item.image_url} alt={item.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                                    ) : <div style={{ width: '100%', height: '100%', display: 'grid', placeItems: 'center', fontSize: '5rem' }}>🌍</div>}
                                                </div>
                                                <div style={{ flex: 1, paddingTop: '10px' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                                                        <div style={{
                                                            padding: '6px 16px', borderRadius: '999px',
                                                            background: idx % 3 === 0 ? '#fff1f2' : idx % 3 === 1 ? '#e0f2fe' : '#fef3c7',
                                                            color: idx % 3 === 0 ? '#be123c' : idx % 3 === 1 ? '#0369a1' : '#92400e',
                                                            fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em'
                                                        }}>
                                                            {item.image_type || 'Application'}
                                                        </div>
                                                        <button
                                                            onClick={() => onEditRealLife(item)}
                                                            style={{ background: 'rgba(30, 41, 59, 0.05)', border: 'none', width: '36px', height: '36px', borderRadius: '10px', display: 'grid', placeItems: 'center', cursor: 'pointer', color: '#64748b' }}
                                                        >
                                                            <Edit2 size={18} />
                                                        </button>
                                                    </div>
                                                    <h4 style={{ fontSize: '2rem', fontWeight: 800, color: '#1e293b', margin: '0 0 20px 0', letterSpacing: '-0.03em' }}>{item.title}</h4>
                                                    <p style={{ fontSize: '1.1rem', color: '#475569', lineHeight: 1.8, marginBottom: '32px' }}>{item.description}</p>
                                                    {item.prompt && (
                                                        <div style={{
                                                            marginTop: '32px', padding: '28px', background: 'rgba(146, 117, 89, 0.04)',
                                                            borderRadius: '24px', borderLeft: '6px solid #927559',
                                                            boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.01)'
                                                        }}>
                                                            <strong style={{ fontSize: '0.8rem', color: '#927559', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                                                                <Sparkles size={16} /> Key Instructional Insight
                                                            </strong>
                                                            <p style={{ fontSize: '1rem', color: '#334155', margin: 0, lineHeight: 1.6, fontWeight: 500 }}>{item.prompt}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div style={{ padding: '120px 40px', textAlign: 'center', color: '#94a3b8', background: 'white', borderRadius: '40px', border: '1px solid rgba(0,0,0,0.03)' }}>
                                    <ImageIcon size={80} style={{ opacity: 0.1, marginBottom: '32px', color: '#1e293b' }} />
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b' }}>No real-life applications discovered yet.</div>
                                    <div style={{ fontSize: '0.95rem', marginTop: '12px', maxWidth: '400px', margin: '12px auto 0' }}>Request a V8 generation with "Real-world examples" enabled to enrich this subtopic.</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default V8ContentBrowser;
