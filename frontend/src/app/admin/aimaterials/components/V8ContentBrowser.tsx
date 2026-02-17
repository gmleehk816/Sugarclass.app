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
    Info,
    Search,
    Edit2,
    Trash2,
    AlertTriangle
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
                padding: isMobile ? '16px' : '32px',
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
    const [editingConcept, setEditingConcept] = useState<any>(null);
    const [isSavingConcept, setIsSavingConcept] = useState(false);
    const [selectedSubtopicId, setSelectedSubtopicId] = useState<string | null>(null);
    const [subtopicStatus, setSubtopicStatus] = useState<V8SubtopicStatus | null>(null);
    const [fullSubtopic, setFullSubtopic] = useState<V8FullSubtopic | null>(null);
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

    const handleSaveConcept = async (conceptId: number, data: any) => {
        setIsSavingConcept(true);
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
        } finally {
            setIsSavingConcept(false);
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
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : (isTablet ? '280px 1fr' : '320px 280px 1fr'),
            gap: '24px',
            alignItems: 'start',
            height: isMobile ? 'auto' : 'calc(100vh - 200px)',
            minHeight: '600px',
        }}>
            {/* Left Sidebar: Hierarchical Subjects Tree */}
            <div style={{
                ...cardStyle(isMobile),
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                height: isMobile ? 'auto' : '100%',
                overflowY: 'auto'
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

            {/* V8 Content Details */}
            <div style={{
                marginTop: '12px',
                width: '100%',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                minHeight: '600px'
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

            {/* Chunk Editor Modal for V8 Concepts */}
            {editingConcept && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200,
                    padding: isMobile ? '0' : '40px'
                }}>
                    <div style={{ width: '100%', maxWidth: '1000px', height: '100%', maxHeight: '90vh' }}>
                        <ChunkEditor
                            content={{
                                id: editingConcept.id,
                                subtopic_id: parseInt(selectedSubtopicId || '0'),
                                subtopic_name: subtopicStatus?.subtopic_id,
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

            {/* Rename Modal */}
            {itemToRename && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100
                }}>
                    <div style={{ background: 'white', padding: '24px', borderRadius: '16px', width: '400px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', fontWeight: 700 }}>Rename {itemToRename.type}</h3>
                        <input
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            style={{ ...inputStyle, marginBottom: '20px' }}
                            placeholder={`Enter new ${itemToRename.type} name`}
                            autoFocus
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                            <button
                                onClick={() => setItemToRename(null)}
                                style={{ ...buttonSecondary, padding: '8px 16px' }}
                                disabled={isProcessingAction}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRename}
                                style={{ ...buttonPrimary, padding: '8px 24px' }}
                                disabled={isProcessingAction || !newName.trim() || newName.trim() === itemToRename.name}
                            >
                                {isProcessingAction ? 'Renaming...' : 'Rename'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* SVG Regeneration Modal */}
            {editingSVGConcept && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200,
                    padding: isMobile ? '0' : '20px'
                }}>
                    <div style={{ background: 'white', padding: '32px', borderRadius: '24px', width: '100%', maxWidth: '500px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Refine SVG</h3>
                            <button onClick={() => setEditingSVGConcept(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><XCircle size={24} /></button>
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem', color: '#64748b' }}>Existing Generation Prompt</label>
                            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '0.9rem', color: '#475569', minHeight: '60px' }}>
                                {editingSVGConcept.description}
                            </div>
                        </div>

                        <div style={{ marginBottom: '24px' }}>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem', color: '#7c3aed' }}>Refinement Prompt (Optional)</label>
                            <textarea
                                value={customSVGPrompt}
                                onChange={(e) => setCustomSVGPrompt(e.target.value)}
                                placeholder="E.g. Make it more colorful, add labels for energy levels, or change the animation speed..."
                                style={{ ...inputStyle, minHeight: '120px', padding: '12px', border: '1.5px solid #ddd', fontSize: '0.95rem' }}
                            />
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                            <button onClick={() => setEditingSVGConcept(null)} style={{ ...buttonSecondary, padding: '10px 20px' }}>Cancel</button>
                            <button
                                onClick={() => handleRegenerateSVG(editingSVGConcept.id, customSVGPrompt)}
                                style={{ ...buttonPrimary, padding: '10px 24px' }}
                                disabled={isRegeneratingSVG}
                            >
                                {isRegeneratingSVG ? (
                                    <>
                                        <Loader2 size={16} className="animate-spin" />
                                        <span>Starting...</span>
                                    </>
                                ) : (
                                    <>
                                        <Zap size={16} />
                                        <span>Regenerate SVG</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Quiz Question Editor Modal */}
            {editingQuiz && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200,
                    padding: isMobile ? '0' : '20px'
                }}>
                    <div style={{ background: 'white', padding: '32px', borderRadius: '24px', width: '100%', maxWidth: '600px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', maxHeight: '95vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Edit Quiz Question</h3>
                            <button onClick={() => setEditingQuiz(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><XCircle size={24} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Question Text</label>
                                <textarea
                                    value={editingQuiz.question_text}
                                    onChange={(e) => setEditingQuiz({ ...editingQuiz, question_text: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '100px', padding: '12px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Options</label>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                    {['A', 'B', 'C', 'D'].map(key => (
                                        <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <strong style={{ fontSize: '0.9rem' }}>{key}:</strong>
                                            <input
                                                value={editingQuiz.options[key] || ''}
                                                onChange={(e) => setEditingQuiz({
                                                    ...editingQuiz,
                                                    options: { ...editingQuiz.options, [key]: e.target.value }
                                                })}
                                                style={{ ...inputStyle, padding: '8px 12px' }}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Correct Answer</label>
                                <select
                                    value={editingQuiz.correct_answer}
                                    onChange={(e) => setEditingQuiz({ ...editingQuiz, correct_answer: e.target.value })}
                                    style={{ ...inputStyle, padding: '8px 12px' }}
                                >
                                    {['A', 'B', 'C', 'D'].map(key => (
                                        <option key={key} value={key}>Option {key}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Explanation</label>
                                <textarea
                                    value={editingQuiz.explanation || ''}
                                    onChange={(e) => setEditingQuiz({ ...editingQuiz, explanation: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '80px', padding: '12px' }}
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '32px' }}>
                            <button onClick={() => setEditingQuiz(null)} style={{ ...buttonSecondary, padding: '10px 20px' }}>Cancel</button>
                            <button
                                onClick={() => handleSaveQuizQuestion(editingQuiz.id, editingQuiz)}
                                style={{ ...buttonPrimary, padding: '10px 24px' }}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Flashcard Editor Modal */}
            {editingFlashcard && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200,
                }}>
                    <div style={{ background: 'white', padding: '32px', borderRadius: '24px', width: '100%', maxWidth: '500px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Edit Flashcard</h3>
                            <button onClick={() => setEditingFlashcard(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><XCircle size={24} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Front (Term/Concept)</label>
                                <textarea
                                    value={editingFlashcard.front}
                                    onChange={(e) => setEditingFlashcard({ ...editingFlashcard, front: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '80px', padding: '12px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Back (Definition/Explanation)</label>
                                <textarea
                                    value={editingFlashcard.back}
                                    onChange={(e) => setEditingFlashcard({ ...editingFlashcard, back: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '120px', padding: '12px' }}
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '32px' }}>
                            <button onClick={() => setEditingFlashcard(null)} style={{ ...buttonSecondary, padding: '10px 20px' }}>Cancel</button>
                            <button
                                onClick={() => handleSaveFlashcard(editingFlashcard.id, editingFlashcard)}
                                style={{ ...buttonPrimary, padding: '10px 24px' }}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Real Life Image Editor Modal */}
            {editingRealLife && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200,
                }}>
                    <div style={{ background: 'white', padding: '32px', borderRadius: '24px', width: '100%', maxWidth: '600px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Edit Example Details</h3>
                            <button onClick={() => setEditingRealLife(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}><XCircle size={24} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Title</label>
                                <input
                                    value={editingRealLife.title}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, title: e.target.value })}
                                    style={{ ...inputStyle, padding: '12px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Description</label>
                                <textarea
                                    value={editingRealLife.description}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, description: e.target.value })}
                                    style={{ ...inputStyle, minHeight: '120px', padding: '12px' }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>Image Type / Category</label>
                                <input
                                    value={editingRealLife.image_type || ''}
                                    onChange={(e) => setEditingRealLife({ ...editingRealLife, image_type: e.target.value })}
                                    style={{ ...inputStyle, padding: '12px' }}
                                    placeholder="e.g. Schematic, Real-world example"
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '32px' }}>
                            <button onClick={() => setEditingRealLife(null)} style={{ ...buttonSecondary, padding: '10px 20px' }}>Cancel</button>
                            <button
                                onClick={() => handleSaveRealLifeImage(editingRealLife.id, editingRealLife)}
                                style={{ ...buttonPrimary, padding: '10px 24px' }}
                                disabled={isSaving}
                            >
                                {isSaving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
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
    regenerating,
    onEditConcept,
    onEditQuiz,
    onEditFlashcard,
    onEditRealLife,
    onEditSVG
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
}) => {
    const [activeTab, setActiveTab] = useState<'concepts' | 'quiz' | 'flashcards' | 'reallife'>('concepts');
    const [activeConceptId, setActiveConceptId] = useState<number | null>(null);

    // Initial concept selection
    useEffect(() => {
        if (subtopic.concepts && subtopic.concepts.length > 0 && activeConceptId === null) {
            setActiveConceptId(subtopic.concepts[0].id);
        }
    }, [subtopic.concepts]);

    if (!subtopic) return null;

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            maxHeight: '92vh', // Increased height
            width: '100%',
            background: '#ffffff',
            borderRadius: '24px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0,0,0,0.03)', // Premium shadow
            fontFamily: "'Outfit', sans-serif",
            color: '#1e293b',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
            {/* V8 Header */}
            <div style={{
                padding: '24px 32px',
                background: 'white',
                borderBottom: '1px solid rgba(0,0,0,0.06)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{
                        width: '42px', height: '42px', background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                        borderRadius: '12px', display: 'grid', placeItems: 'center',
                        color: '#927559', fontWeight: 800, fontSize: '14px',
                        boxShadow: '0 8px 16px rgba(30, 41, 59, 0.2)'
                    }}>V8</div>
                    <div>
                        <div style={{ fontWeight: 800, fontSize: '1.2rem', color: '#0f172a', letterSpacing: '-0.02em' }}>{subtopic.name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#927559', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '2px' }}>Interactive Designer Preview</div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
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
                padding: '16px 32px',
                background: '#f8fafc',
                display: 'flex',
                gap: '12px',
                borderBottom: '1px solid rgba(0,0,0,0.05)',
                justifyContent: 'center'
            }}>
                {[
                    { id: 'concepts', label: 'Learn', Icon: Layers, color: '#4f46e5' },
                    { id: 'quiz', label: 'Quiz', Icon: HelpCircle, color: '#d97706' },
                    { id: 'flashcards', label: 'Cards', Icon: FileText, color: '#db2777' },
                    { id: 'reallife', label: 'Real Life', Icon: ImageIcon, color: '#059669' }
                ].map(tab => {
                    const TabIcon = tab.Icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            style={{
                                padding: '12px 28px',
                                borderRadius: '16px',
                                border: 'none',
                                background: activeTab === tab.id ? 'white' : 'transparent',
                                color: activeTab === tab.id ? tab.color : '#64748b',
                                fontWeight: 800,
                                fontSize: '1rem',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                boxShadow: activeTab === tab.id ? '0 12px 20px -5px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)' : 'none',
                                transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                opacity: activeTab === tab.id ? 1 : 0.6,
                                transform: activeTab === tab.id ? 'scale(1.05)' : 'scale(1)'
                            }}
                        >
                            <TabIcon size={22} color={activeTab === tab.id ? tab.color : '#94a3b8'} strokeWidth={2.5} />
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
                        <div style={{
                            width: '260px',
                            borderRight: '1px solid rgba(0,0,0,0.05)',
                            padding: '24px 16px',
                            overflowY: 'auto',
                            background: 'white'
                        }}>
                            <div style={{
                                fontSize: '0.7rem',
                                fontWeight: 800,
                                color: '#927559',
                                textTransform: 'uppercase',
                                letterSpacing: '0.15em',
                                marginBottom: '16px',
                                paddingLeft: '12px'
                            }}>Contents</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {subtopic.concepts?.map(concept => (
                                    <button
                                        key={concept.id}
                                        onClick={() => {
                                            setActiveConceptId(concept.id);
                                            document.getElementById(`concept-${concept.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }}
                                        style={{
                                            padding: '12px 16px',
                                            borderRadius: '12px',
                                            border: 'none',
                                            background: activeConceptId === concept.id ? 'rgba(146, 117, 89, 0.08)' : 'transparent',
                                            color: activeConceptId === concept.id ? '#0f172a' : '#64748b',
                                            textAlign: 'left',
                                            fontSize: '0.85rem',
                                            fontWeight: activeConceptId === concept.id ? 700 : 500,
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px',
                                            transition: 'all 0.2s',
                                            borderLeft: activeConceptId === concept.id ? '3px solid #927559' : '3px solid transparent'
                                        }}
                                    >
                                        <span style={{ fontSize: '1.1rem' }}>{concept.icon || '📚'}</span>
                                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{concept.title}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Concept Display */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '32px', background: '#fcfafb' }} id="concept-scroll-area">
                            {subtopic.concepts?.map(concept => (
                                <section key={concept.id} id={`concept-${concept.id}`} style={{ marginBottom: '64px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                                        <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '12px', letterSpacing: '-0.02em' }}>
                                            <span style={{
                                                width: '40px', height: '40px', background: 'white', borderRadius: '10px',
                                                display: 'grid', placeItems: 'center', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
                                            }}>{concept.icon || '📚'}</span>
                                            {concept.title}
                                        </h3>
                                        <button
                                            onClick={() => onEditConcept(concept)}
                                            style={{
                                                padding: '12px', borderRadius: '14px', border: '1px solid #e2e8f0',
                                                background: 'white', cursor: 'pointer', color: '#4f46e5',
                                                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                transition: 'all 0.2s'
                                            }}
                                            className="hover:shadow-md hover:border-indigo-200"
                                            title="Edit Concept"
                                        >
                                            <Edit2 size={20} color="#4f46e5" />
                                        </button>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
                                        {/* Left: Text */}
                                        <div style={{
                                            background: 'white', padding: '32px', borderRadius: '24px',
                                            border: '1px solid rgba(0,0,0,0.04)', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.03)'
                                        }}>
                                            <div style={{ fontSize: '1rem', lineHeight: 1.8, color: '#334155' }}>
                                                {concept.description && <p style={{ marginBottom: '20px', fontWeight: 600, color: '#1e293b', fontSize: '1.1rem' }}>{concept.description}</p>}
                                                {concept.generated?.bullets && (
                                                    <div
                                                        dangerouslySetInnerHTML={{ __html: concept.generated.bullets }}
                                                        style={{
                                                            fontSize: '0.95rem',
                                                            color: '#475569'
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        </div>

                                        {/* Right: Visual */}
                                        <div style={{
                                            background: 'white', padding: '24px', borderRadius: '24px',
                                            border: '1px solid rgba(0,0,0,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            minHeight: '500px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)', position: 'relative',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10 }}>
                                                <button
                                                    onClick={() => onEditSVG(concept)}
                                                    style={{
                                                        background: 'rgba(255, 255, 255, 0.9)', border: '1px solid #e2e8f0',
                                                        borderRadius: '50%', width: '36px', height: '36px',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        cursor: 'pointer', boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                                                        color: '#7c3aed'
                                                    }}
                                                    title="Refine SVG"
                                                >
                                                    <Sparkles size={16} />
                                                </button>
                                            </div>
                                            <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#927559', opacity: 0.1 }}></div>
                                            {concept.generated?.svg ? (
                                                <div
                                                    dangerouslySetInnerHTML={{ __html: concept.generated.svg }}
                                                    style={{ width: '100%', height: '100%' }}
                                                />
                                            ) : (
                                                <div style={{ opacity: 0.2, textAlign: 'center' }}>
                                                    <Sparkles size={60} style={{ marginBottom: '16px', color: '#927559' }} />
                                                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Visual Rendering</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </section>
                            ))}
                        </div>
                    </>
                )}

                {activeTab === 'quiz' && (
                    <div style={{ flex: 1, overflowY: 'auto', padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px', background: '#f8fafc' }}>
                        {subtopic.quiz?.map((q, idx) => (
                            <div key={idx} style={{
                                background: 'white', borderRadius: '28px', padding: '32px',
                                border: '1px solid rgba(0,0,0,0.03)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.05)'
                            }}>
                                <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
                                    <span style={{
                                        background: '#0f172a', color: 'white', padding: '6px 16px',
                                        borderRadius: '999px', fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em'
                                    }}>Question {q.question_num || idx + 1}</span>
                                    {q.difficulty && <span style={{
                                        fontSize: '0.75rem', padding: '6px 16px', borderRadius: '999px', fontWeight: 700,
                                        background: q.difficulty === 'easy' ? '#ecfdf5' : q.difficulty === 'hard' ? '#fef2f2' : '#fffbeb',
                                        color: q.difficulty === 'easy' ? '#059669' : q.difficulty === 'hard' ? '#dc2626' : '#d97706',
                                        textTransform: 'capitalize'
                                    }}>{q.difficulty}</span>}
                                    <button
                                        onClick={() => onEditQuiz(q)}
                                        style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                                    >
                                        <Edit2 size={16} />
                                    </button>
                                </div>
                                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f172a', marginBottom: '24px', lineHeight: 1.4, letterSpacing: '-0.01em' }}>{q.question_text}</div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                    {Object.entries((() => {
                                        if (typeof q.options === 'string') {
                                            try { return JSON.parse(q.options); } catch { return {}; }
                                        }
                                        return q.options || {};
                                    })()).map(([key, val]) => (
                                        <div key={key} style={{
                                            padding: '16px 20px', borderRadius: '16px', border: '2px solid',
                                            borderColor: key === q.correct_answer ? '#10b981' : 'rgba(0,0,0,0.03)',
                                            background: key === q.correct_answer ? '#f0fdf4' : 'white',
                                            fontSize: '1rem', fontWeight: 600, color: '#4b5563',
                                            transition: 'all 0.2s'
                                        }}>
                                            <strong style={{ color: key === q.correct_answer ? '#059669' : '#927559', marginRight: '8px' }}>{key}.</strong> {val as string}
                                            {key === q.correct_answer && <CheckCircle2 size={16} style={{ float: 'right', color: '#10b981', marginTop: '4px' }} />}
                                        </div>
                                    ))}
                                </div>
                                {q.explanation && (
                                    <div style={{
                                        marginTop: '24px', padding: '20px', background: 'rgba(146, 117, 89, 0.04)',
                                        borderRadius: '16px', borderLeft: '5px solid #927559', fontSize: '0.95rem', color: '#475569', lineHeight: 1.6
                                    }}>
                                        <div style={{ fontWeight: 800, color: '#927559', marginBottom: '4px', textTransform: 'uppercase', fontSize: '0.75rem' }}>Explanation</div>
                                        {q.explanation}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'flashcards' && (
                    <div style={{ flex: 1, overflowY: 'auto', padding: '32px', background: '#fcfaf7' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
                            {subtopic.flashcards?.map((card, idx) => (
                                <div key={idx} style={{
                                    height: '220px', perspective: '1000px'
                                }}>
                                    <div style={{
                                        position: 'relative', width: '100%', height: '100%',
                                        background: 'white', borderRadius: '24px', padding: '32px',
                                        border: '1px solid rgba(0,0,0,0.04)', display: 'flex', flexDirection: 'column',
                                        justifyContent: 'center', alignItems: 'center', textAlign: 'center',
                                        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05)',
                                        transition: 'transform 0.3s ease'
                                    }} className="hover:scale-[1.02]">
                                        <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                            <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#ec4899', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Front</div>
                                            <button
                                                onClick={() => onEditFlashcard(card)}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#cbd5e1' }}
                                            >
                                                <Edit2 size={14} />
                                            </button>
                                        </div>
                                        <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', marginBottom: '16px', lineHeight: 1.3 }}>{card.front}</div>
                                        <div style={{ width: '40px', height: '1px', background: 'rgba(0,0,0,0.05)', marginBottom: '16px' }}></div>
                                        <div style={{ fontSize: '0.9rem', color: '#64748b', fontStyle: 'italic', lineHeight: 1.5 }}>{card.back}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'reallife' && (
                    <div style={{ flex: 1, overflowY: 'auto', padding: '32px', background: '#f0fdfa' }}>
                        {subtopic.reallife_images && subtopic.reallife_images.length > 0 ? (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '40px' }}>
                                {subtopic.reallife_images.map((item, idx) => (
                                    <div key={idx} style={{
                                        background: 'white', borderRadius: '32px', padding: '32px',
                                        border: '1px solid rgba(0,0,0,0.03)', boxShadow: '0 15px 30px -10px rgba(0, 0, 0, 0.05)'
                                    }}>
                                        <div style={{ display: 'flex', gap: '40px', alignItems: 'center' }}>
                                            <div style={{
                                                width: '400px', height: '280px', flexShrink: 0, borderRadius: '24px',
                                                overflow: 'hidden', background: '#f1f5f9', boxShadow: '0 10px 20px rgba(0,0,0,0.05)'
                                            }}>
                                                {item.image_url ? (
                                                    <img src={item.image_url} alt={item.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                                ) : <div style={{ width: '100%', height: '100%', display: 'grid', placeItems: 'center', fontSize: '4rem' }}>🖼️</div>}
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{
                                                    display: 'inline-block', padding: '6px 16px', borderRadius: '999px',
                                                    background: idx % 2 === 0 ? '#fff1f2' : '#e0f2fe',
                                                    color: idx % 2 === 0 ? '#be123c' : '#0369a1',
                                                    fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px'
                                                }}>
                                                    {item.image_type || 'Contextual Example'}
                                                </div>
                                                <button
                                                    onClick={() => onEditRealLife(item)}
                                                    style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                                                >
                                                    <Edit2 size={18} />
                                                </button>
                                                <h4 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0', letterSpacing: '-0.02em' }}>{item.title}</h4>
                                                <p style={{ fontSize: '1.05rem', color: '#475569', lineHeight: 1.7, marginBottom: '24px' }}>{item.description}</p>
                                                {item.prompt && (
                                                    <div style={{
                                                        marginTop: '24px', padding: '20px', background: '#f8fafc',
                                                        borderRadius: '20px', borderLeft: '5px solid #3b82f6',
                                                        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
                                                    }}>
                                                        <strong style={{ fontSize: '0.8rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                                            <Sparkles size={14} color="#3b82f6" />
                                                            Generation Insight
                                                        </strong>
                                                        <p style={{ fontSize: '0.95rem', color: '#334155', margin: 0, lineHeight: 1.5 }}>{item.prompt}</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{ padding: '80px', textAlign: 'center', color: '#94a3b8' }}>
                                <ImageIcon size={64} style={{ opacity: 0.1, marginBottom: '24px', color: '#10b981' }} />
                                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>No real-life examples generated yet.</div>
                                <div style={{ fontSize: '0.9rem', marginTop: '8px' }}>These will provide visual context for student understanding.</div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};



export default V8ContentBrowser;
