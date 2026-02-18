"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { serviceFetch } from '@/lib/microservices';
import ChunkEditor from './components/ChunkEditor';
import V8ContentBrowser from './components/V8ContentBrowser';
import {
    Upload,
    Book,
    Zap,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Clock,
    Search,
    Terminal,
    LayoutDashboard,
    Database,
    Trash2,
    AlertTriangle,
    ListOrdered,
    Edit,
    Edit2,
    Plus,
    GripVertical,
    Save,
    X as XIcon,
    Folder,
    FolderOpen,
    ChevronRight,
    ChevronDown,
    FileText,
    Settings,
    Image,
    Video,
    Bold,
    Italic,
    Heading,
    List,
    Quote,
    Code,
    Eye,
    EyeOff,
    Undo2,
    Redo2,
    Type,
    Loader2,
    Underline,
    Strikethrough,
    Palette,
    Highlighter,
    Link as LinkIcon,
    Minus,
    Maximize2,
    Minimize2,
    AlignLeft,
    AlignCenter,
    AlignRight,
    ArrowUp,
    ArrowDown,
    Move,
    Trash,
    MousePointer2,
    Sparkles,
    ArrowLeft,
    MessageSquare,
    Activity,
    Image as ImageIcon,
    Layers,
    Info
} from "lucide-react";
import { SERVICE_URLS } from '@/lib/microservices';

const prefixImageUrls = (html: string) => {
    if (!html) return '';
    return html
        .replace(/src="\/generated_images\//g, `src="${SERVICE_URLS.aimaterials}/generated_images/`)
        .replace(/src="\/exercise_images\//g, `src="${SERVICE_URLS.aimaterials}/exercise_images/`);
};

const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontFamily: 'inherit'
};

// ===========================================================================
// DATATREE â€” Full educational hierarchy from datatree.md
// Structure: Level â†’ Subject â†’ Board-specific variants (with exam codes)
// ===========================================================================
const DATATREE: Record<string, Record<string, string[]>> = {
    "A-Level": {
        "Accounting": ["AQA Accounting (7127)", "Cie Accounting (9706)", "Edexcel Accounting (9AC0)"],
        "Biology": ["AQA Biology (7402)", "Cie Biology (9700)", "Edexcel Biology (9BI0)"],
        "Business": ["AQA Business (7132)", "Cie Business (9609)", "Edexcel Business (9BS0)"],
        "Chemistry": ["AQA Chemistry (7405)", "Cie Chemistry (9701)", "Edexcel Chemistry (9CH0)"],
        "Computer Science": ["AQA Computer Science (7517)", "Cie Computer Science (9618)"],
        "Design Technology": ["AQA Design Technology (7552)", "Edexcel Design Technology Product Design (9DT0)"],
        "Economics": ["AQA Economics (7136)", "Cie Economics (9708)", "Edexcel Economics (9EC0)"],
        "Engineering": ["AQA Engineering (8852)"],
        "English Language": ["AQA English Language (7702)", "Cie English Language (9093)", "Edexcel English Language (9EN0)"],
        "English Literature": ["AQA English Literature (7712)", "Cie Literature English (9695)", "Edexcel English Literature (9ET0)"],
        "Food Science Nutrition": ["AQA Food Science Nutrition (7272)"],
        "French": ["AQA French (7652)"],
        "Further Mathematics": ["AQA Further Mathematics (7367)", "Cie Further Mathematics (9231)", "Edexcel Further Mathematics (9FM0)"],
        "Geography": ["AQA Geography (7037)", "Cie Geography (9696)", "Edexcel Geography (9GE0)"],
        "Global perspectives": ["Cie Global Perspectives Research (9239)"],
        "History": ["AQA History (7041)", "AQA History (7042)", "Cie History (9389)", "Cie History (9489)", "Edexcel History (9HI0)"],
        "Information Technology": ["Edexcel Information Technology (9IT0)"],
        "Mathematics": ["AQA Mathematics (7357)", "Cie Mathematics (9709)", "Edexcel Mathematics (9MA0)"],
        "Physical Education": ["AQA Physical Education (7357)", "AQA Physical Education (7582)", "Edexcel Physical Education (9PE0)"],
        "Physics": ["AQA Physics (7408)", "Cie Physics (9702)", "Edexcel Physics (9PH0)"],
        "Psychology": ["AQA Psychology (7182)", "Cie Psychology (9990)", "Edexcel Psychology (9PS0)"],
        "Sociology": ["AQA Sociology (7192)", "Cie Sociology (9699)", "Edexcel Sociology (9SC0)"],
    },
    "HKDSE": {
        "Biology": [], "Business, Accounting and Financial Studies": [], "Chemistry": [],
        "Chinese History": [], "Chinese Language": [], "Chinese Literature": [],
        "Citizenship and Social Development": [], "Design and Applied Technology": [],
        "Economics": [], "English Language": [], "Ethics and Religious Studies": [],
        "Geography": [], "Health Management and Social Care": [], "History": [],
        "Information and Communication Technology": [], "Literature in English": [],
        "Mathematics": [], "Music": [], "Physical Education": [], "Physics": [],
        "Technology and Living": [], "Tourism and Hospitality Studies": [], "Visual Arts": [],
    },
    "IB": {
        "Biology": [], "Business Management": [], "Chemistry": [], "Computer Science": [],
        "Design Technology": [], "Economics": [], "English A Language Literature": [],
        "Environmental Systems Societies": [], "Film": [], "Geography": [],
        "Global Politics": [], "History": [], "Mathematics AA": [], "Music": [],
        "Physics": [], "Psychology": [], "Spanish B": [], "Theory of Knowledge": [],
        "Visual Arts": [],
    },
    "IGCSE": {
        "Accounting": ["Cie Accounting (0452)", "Edexcel Accounting", "Edexcel Accounting (4AC1)"],
        "Additional Mathematics": ["Cie Additional Mathematics (0606)", "Edexcel Further Mathematics", "Edexcel Mathematics (4MA0)"],
        "Biology": ["Cie Biology (0610)", "Edexcel Biology (4BI1)"],
        "Business": ["Cie Business (0450)", "Edexcel Business (4BS1)"],
        "Business Studies": ["Cie Business (0450)", "Edexcel Business (4BS1)"],
        "Chemistry": ["Cie Chemistry (0620)", "Edexcel Chemistry (4CH1)"],
        "Chinese First Language": ["Cie Chinese First Language (0509)", "Edexcel Chinese (4CN0)"],
        "Chinese Mandarin Foreign Language": ["Cie Chinese Mandarin Foreign Language (0547)", "Edexcel Chinese (4CN0)"],
        "Chinese Second Language": ["Cie Chinese Second Language (0523)", "Edexcel Chinese (4CN0)"],
        "Combined Science": ["Cie Combined Science (0653)", "Edexcel Science (Double Award) (4SC0)"],
        "Computer Science": ["Cie Computer Science (0478)", "Edexcel Computer Science (4CP0)"],
        "Design Technology": ["Cie Design Technology (0445)"],
        "Economics": ["Cie Economics (0455)", "Edexcel Economic", "Edexcel Economics"],
        "English Literature": ["Cie Literature English (0475)", "Edexcel English literature (4ET1)"],
        "English Second Language": ["Cie English Second Language (0510)", "Edexcel English as a Second Language (4ES0)"],
        "Enterprise": ["Cie Enterprise (0454)"],
        "Environmental Management": ["Cie Environmental Management (0680)"],
        "First Language English": ["Cie First Language English (0500)", "Edexcel English Language (4EA0)"],
        "Food and Nutrition": ["Cie Food and Nutrition (0648)"],
        "Geography": ["Cie Geography (0460)", "Edexcel Geography (4GE1)"],
        "Global Perspectives": ["Cie Global Perspectives (0457)"],
        "History": ["Cie History (0470)", "Edexcel History (4HI1)"],
        "Human Biology": ["Edexcel Human Biology"],
        "ICT": ["Cie ICT (0417)", "Edexcel ICT (4IT1)"],
        "International Mathematics": ["Cie Mathematics - International (0607)", "Edexcel Mathematics (4MA0)"],
        "Mathematics": ["Cie Mathematics (0580)", "Edexcel Mathematics (4MA1)"],
        "Physical Education": ["Cie Physical Education (0413)"],
        "Physical Science": ["Cie Physical Science (0652)"],
        "Physics": ["Cie Physics (0625)", "Edexcel Physics (4PH1)"],
        "Psychology": ["Cie Psychology (0990)"],
        "Sociology": ["Cie Sociology (0495)"],
    },
    "primary": {},
    "secondary": {},
};

type DbSubject = {
    id: string;
    name: string;
    syllabus_id: string;
    topic_count: number;
    subtopic_count: number;
    content_count: number;
};

// Helper: Sanitize string for matching (must match backend logic)
function sanitizeId(name: string): string {
    return name.toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .trim()
        .replace(/[-\s]+/g, '_')
        .substring(0, 50);
}

// Must stay aligned with backend _sanitize_code (admin_v8.py)
function sanitizeIngestCode(name: string): string {
    return sanitizeId(name);
}

type AdminV8TaskStatus = 'idle' | 'pending' | 'running' | 'cancelling' | 'completed' | 'failed' | 'cancelled';

const V8_ACTIVE_TASK_STORAGE_KEY = 'aimaterials_v8_active_task_id';

function normalizeV8TaskStatus(value: unknown): AdminV8TaskStatus {
    switch (value) {
        case 'pending':
        case 'running':
        case 'cancelling':
        case 'completed':
        case 'failed':
        case 'cancelled':
            return value;
        default:
            return 'idle';
    }
}

function matchSubjectsToTree(dbSubjects: DbSubject[]) {
    const matched = new Set<string>();
    const subjectIdMap: Record<string, DbSubject> = {};

    // Build a lookup: subject ID → DbSubject
    for (const sub of dbSubjects) {
        subjectIdMap[sub.id] = sub;
    }

    // Try to match each tree leaf to a DB subject
    const treeWithData: Record<string, Record<string, { boards: { name: string; dbSubject?: DbSubject }[]; dbSubject?: DbSubject }>> = {};

    for (const [level, subjects] of Object.entries(DATATREE)) {
        treeWithData[level] = {};
        const levelCode = sanitizeId(level || 'IGCSE');

        for (const [subjectName, boards] of Object.entries(subjects)) {
            const boardEntries = boards.map(boardName => {
                // IMPORTANT: V8 IDs are prefixed with syllabus code: e.g. "igcse_physics_0625"
                const targetId = `${levelCode}_${sanitizeId(boardName)}`;
                const db = subjectIdMap[targetId];
                if (db) matched.add(db.id);
                return { name: boardName, dbSubject: db };
            });

            const subjectId = `${levelCode}_${sanitizeId(subjectName)}`;
            const subjectDb = subjectIdMap[subjectId];
            if (subjectDb) matched.add(subjectDb.id);

            treeWithData[level][subjectName] = {
                boards: boardEntries,
                dbSubject: subjectDb,
            };
        }
    }

    const unmatched = dbSubjects.filter(s => !matched.has(s.id));

    return { treeWithData, unmatched };
}

// ===========================================================================
// Exercise Interfaces
// ===========================================================================
interface Exercise {
    id?: number;
    question_num?: number;
    question_text: string;
    options: {
        A: string;
        B: string;
        C: string;
        D: string;
    };
    correct_answer: string;
    explanation?: string;
}

// Exercise Modal Component
const ExerciseModal = ({
    exercise,
    onClose,
    onSave
}: {
    exercise: Exercise | null,
    onClose: () => void,
    onSave: (data: Partial<Exercise>) => Promise<void>
}) => {
    const [formData, setFormData] = useState<Exercise>({
        question_text: exercise?.question_text || '',
        options: exercise?.options || { A: '', B: '', C: '', D: '' },
        correct_answer: exercise?.correct_answer || 'A',
        explanation: exercise?.explanation || ''
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (!formData.question_text.trim()) {
            setError('Question text is required');
            return;
        }
        if (!formData.options.A || !formData.options.B || !formData.options.C || !formData.options.D) {
            setError('All 4 options are required');
            return;
        }

        setSaving(true);
        try {
            await onSave(formData);
        } catch (err: any) {
            setError(err.message || 'Failed to save exercise');
            setSaving(false);
        }
    };

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
                borderRadius: '16px',
                padding: '32px',
                maxWidth: '600px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
                        {exercise ? 'Edit Question' : 'Add New Question'}
                    </h2>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '1.5rem',
                            cursor: 'pointer',
                            color: '#64748b',
                            padding: '4px'
                        }}
                    >
                        Ã—
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    {/* Question Text */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Question Text *
                        </label>
                        <textarea
                            value={formData.question_text}
                            onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
                            style={{
                                ...inputStyle,
                                minHeight: '100px',
                                resize: 'vertical'
                            }}
                            placeholder="Enter the question text..."
                        />
                    </div>

                    {/* Options */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Answer Options *
                        </label>
                        {['A', 'B', 'C', 'D'].map((key) => (
                            <div key={key} style={{ marginBottom: '12px' }}>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span style={{
                                        fontWeight: 600,
                                        minWidth: '24px',
                                        color: '#64748b'
                                    }}>
                                        {key}:
                                    </span>
                                    <input
                                        type="text"
                                        value={formData.options[key as 'A' | 'B' | 'C' | 'D']}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            options: { ...formData.options, [key]: e.target.value }
                                        })}
                                        style={inputStyle}
                                        placeholder={`Option ${key}`}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Correct Answer */}
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Correct Answer *
                        </label>
                        <select
                            value={formData.correct_answer}
                            onChange={(e) => setFormData({ ...formData, correct_answer: e.target.value })}
                            style={{
                                ...inputStyle,
                                cursor: 'pointer'
                            }}
                        >
                            <option value="A">A</option>
                            <option value="B">B</option>
                            <option value="C">C</option>
                            <option value="D">D</option>
                        </select>
                    </div>

                    {/* Explanation */}
                    <div style={{ marginBottom: '24px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Explanation (Optional)
                        </label>
                        <textarea
                            value={formData.explanation}
                            onChange={(e) => setFormData({ ...formData, explanation: e.target.value })}
                            style={{
                                ...inputStyle,
                                minHeight: '80px',
                                resize: 'vertical'
                            }}
                            placeholder="Explain why this is the correct answer..."
                        />
                    </div>

                    {/* Error */}
                    {error && (
                        <div style={{
                            padding: '12px',
                            background: '#fee2e2',
                            color: '#dc2626',
                            borderRadius: '8px',
                            marginBottom: '20px',
                            fontSize: '0.9rem'
                        }}>
                            {error}
                        </div>
                    )}

                    {/* Buttons */}
                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={saving}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '8px',
                                border: '1px solid #e2e8f0',
                                background: 'white',
                                color: '#64748b',
                                cursor: saving ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                opacity: saving ? 0.5 : 1
                            }}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={saving}
                            style={{
                                padding: '10px 20px',
                                borderRadius: '8px',
                                border: 'none',
                                background: '#10b981',
                                color: 'white',
                                cursor: saving ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                opacity: saving ? 0.6 : 1
                            }}
                        >
                            {saving ? 'Saving...' : (exercise ? 'Update' : 'Create')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Question Card Component
const QuestionCard = ({
    exercise,
    onEdit,
    onDelete,
    onRegenerate
}: {
    exercise: Exercise,
    onEdit: () => void,
    onDelete: () => void,
    onRegenerate: () => void
}) => {
    return (
        <div style={{
            background: '#fafafa',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #e5e7eb'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b', flex: 1 }}>
                    Q{exercise.question_num}: {exercise.question_text}
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={onEdit}
                        title="Edit Question"
                        style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: 'none',
                            background: '#e0e7ff',
                            color: '#4f46e5',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Edit size={14} />
                    </button>
                    <button
                        onClick={onRegenerate}
                        title="Regenerate with AI"
                        style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: 'none',
                            background: '#f3e8ff',
                            color: '#9333ea',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Zap size={14} />
                    </button>
                    <button
                        onClick={onDelete}
                        title="Delete Question"
                        style={{
                            padding: '6px 12px',
                            borderRadius: '6px',
                            border: 'none',
                            background: '#fee2e2',
                            color: '#dc2626',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                {Object.entries(exercise.options).map(([key, value]: [string, any]) => (
                    <div
                        key={key}
                        style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            background: key === exercise.correct_answer ? '#d1fae5' : 'white',
                            border: `1px solid ${key === exercise.correct_answer ? '#10b981' : '#e5e7eb'}`,
                            fontSize: '0.85rem'
                        }}
                    >
                        <strong>{key}:</strong> {value}
                    </div>
                ))}
            </div>

            {exercise.explanation && (
                <div style={{
                    padding: '10px 12px',
                    background: '#fef3c7',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    borderLeft: '3px solid #f59e0b'
                }}>
                    <strong>Explanation:</strong> {exercise.explanation}
                </div>
            )}
        </div>
    );
};

// ===========================================================================
// Interfaces
// ===========================================================================
interface ResourceContent {
    id: number;
    subtopic_id: number;
    subtopic_name?: string;
    topic_id?: string;
    topic_name?: string;
    subject_id?: string;
    subject_name?: string;
    html_content: string;
    summary?: string;
    key_terms?: string;
}



// ===========================================================================
// Content Regenerate Modal Component
// ===========================================================================
interface RegenerateOptions {
    focus: string;
    temperature: number;
    include_key_terms: boolean;
    include_summary: boolean;
    include_think_about_it: boolean;
    generate_images: boolean;
    generate_videos: boolean;
    custom_prompt: string;
    apply_to_full_book: boolean;
}

// ===========================================================================
// Content Regenerate Modal Component
// ===========================================================================
const ContentRegenerateModal = ({
    options,
    setOptions,
    onConfirm,
    onClose,
    regenerating,
    subjectName,
    isMobile
}: {
    options: RegenerateOptions;
    setOptions: (options: RegenerateOptions) => void;
    onConfirm: () => void;
    onClose: () => void;
    regenerating: boolean;
    subjectName?: string;
    isMobile: boolean;
}) => {
    const { apply_to_full_book } = options;
    const focusOptions = [
        { value: '', label: 'Standard (balanced)' },
        { value: 'more creative', label: 'More Creative & Engaging' },
        { value: 'simpler', label: 'Simpler & More Concise' },
        { value: 'focus on examples', label: 'Focus on Real-World Examples' },
        { value: 'focus on visual learning', label: 'Focus on Visual Learning' },
        { value: 'more detailed', label: 'More Detailed & Comprehensive' }
    ];

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
                maxWidth: '900px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                position: 'relative'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                    <div>
                        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, color: '#1e293b', letterSpacing: '-0.025em' }}>
                            Regenerate Content v2
                        </h2>
                        <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
                            Configure AI enhancement for your educational materials
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        disabled={regenerating}
                        style={{
                            background: '#f1f5f9',
                            border: 'none',
                            width: '40px',
                            height: '40px',
                            borderRadius: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: regenerating ? 'not-allowed' : 'pointer',
                            color: '#64748b',
                            transition: 'all 0.2s',
                            fontSize: '1.2rem'
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = '#e2e8f0'; e.currentTarget.style.color = '#0f172a'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = '#f1f5f9'; e.currentTarget.style.color = '#64748b'; }}
                    >
                        ✕
                    </button>
                </div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: isMobile ? '1fr' : '1.2fr 1fr',
                    gap: isMobile ? '24px' : '40px',
                    alignItems: 'start'
                }}>
                    {/* Left Column: Primary Configurations */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        {/* Focus Option */}
                        <div style={{
                            background: '#f8fafc',
                            padding: '20px',
                            borderRadius: '16px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                                <Zap size={18} color="#7c3aed" /> Enhancement Focus
                            </label>
                            <select
                                value={options.focus}
                                onChange={(e) => setOptions({ ...options, focus: e.target.value })}
                                disabled={regenerating}
                                style={{
                                    ...inputStyle,
                                    cursor: regenerating ? 'not-allowed' : 'pointer',
                                    background: regenerating ? '#f1f5f9' : 'white',
                                    height: '48px',
                                    borderRadius: '10px',
                                    fontSize: '0.95rem'
                                }}
                            >
                                {focusOptions.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Custom Prompt */}
                        <div style={{
                            background: '#f8fafc',
                            padding: '20px',
                            borderRadius: '16px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                                <MessageSquare size={18} color="#7c3aed" /> Additional Instructions
                            </label>
                            <textarea
                                value={options.custom_prompt}
                                onChange={(e) => setOptions({ ...options, custom_prompt: e.target.value })}
                                disabled={regenerating}
                                placeholder="e.g. Focus on practical applications, translate to French, add more case studies..."
                                style={{
                                    ...inputStyle,
                                    minHeight: '130px',
                                    resize: 'vertical',
                                    background: regenerating ? '#f1f5f9' : 'white',
                                    cursor: regenerating ? 'not-allowed' : 'pointer',
                                    fontSize: '0.9rem',
                                    borderRadius: '10px',
                                    lineHeight: '1.5'
                                }}
                            />
                        </div>

                        {/* Creativity Level */}
                        <div style={{
                            background: '#f8fafc',
                            padding: '20px',
                            borderRadius: '16px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Activity size={18} color="#7c3aed" /> Creativity Level
                                </span>
                                <span style={{ background: '#7c3aed', color: 'white', padding: '2px 8px', borderRadius: '6px', fontSize: '0.8rem' }}>
                                    {options.temperature.toFixed(1)}
                                </span>
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.1"
                                value={options.temperature}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, temperature: parseFloat(e.target.value) })}
                                disabled={regenerating}
                                style={{ width: '100%', cursor: regenerating ? 'not-allowed' : 'pointer', accentColor: '#7c3aed' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginTop: '8px', fontWeight: 500 }}>
                                <span>Conservative</span>
                                <span>Balanced</span>
                                <span>Creative</span>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Scope & Features */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        {/* Scope Selection (Full Book) */}
                        <div style={{
                            padding: '20px',
                            background: apply_to_full_book ? '#fff1f2' : '#f8fafc',
                            borderRadius: '16px',
                            border: apply_to_full_book ? '2px solid #fecaca' : '1px solid #e2e8f0',
                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            boxShadow: apply_to_full_book ? '0 10px 15px -3px rgba(220, 38, 38, 0.1)' : 'none'
                        }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: regenerating ? 'not-allowed' : 'pointer' }}>
                                <div style={{
                                    width: '24px',
                                    height: '24px',
                                    position: 'relative',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}>
                                    <input
                                        type="checkbox"
                                        checked={apply_to_full_book || false}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, apply_to_full_book: e.target.checked })}
                                        disabled={regenerating}
                                        style={{
                                            width: '20px',
                                            height: '20px',
                                            cursor: regenerating ? 'not-allowed' : 'pointer',
                                            accentColor: '#dc2626'
                                        }}
                                    />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <span style={{
                                        fontWeight: 800,
                                        fontSize: '1rem',
                                        color: apply_to_full_book ? '#991b1b' : '#334155',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}>
                                        Regenerate Full Book {apply_to_full_book && <Zap size={14} fill="#dc2626" />}
                                    </span>
                                    {subjectName && (
                                        <div style={{ fontSize: '0.8rem', color: apply_to_full_book ? '#b91c1c' : '#64748b', marginTop: '2px', fontWeight: 500 }}>
                                            Subject: <span style={{ textDecoration: 'underline' }}>{subjectName}</span>
                                        </div>
                                    )}
                                </div>
                            </label>
                            {apply_to_full_book && (
                                <div style={{
                                    marginTop: '16px',
                                    padding: '12px',
                                    background: 'rgba(255, 255, 255, 0.5)',
                                    borderRadius: '10px',
                                    fontSize: '0.8rem',
                                    color: '#b91c1c',
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '8px',
                                    lineHeight: '1.4',
                                    border: '1px solid rgba(220, 38, 38, 0.1)'
                                }}>
                                    <AlertTriangle size={16} style={{ marginTop: '1px', flexShrink: 0 }} />
                                    <span><strong>Warning:</strong> This will regenerate ALL subtopics for this subject sequentially. Best for final polish.</span>
                                </div>
                            )}
                        </div>

                        {/* Media Generation */}
                        <div style={{
                            background: '#f8fafc',
                            padding: '20px',
                            borderRadius: '16px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                                <ImageIcon size={18} color="#7c3aed" /> Media Generation
                            </label>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: regenerating ? 'not-allowed' : 'pointer', padding: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={options.generate_images}
                                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, generate_images: e.target.checked })}
                                        disabled={regenerating}
                                        style={{ width: '18px', height: '18px', accentColor: '#7c3aed' }}
                                    />
                                    <span style={{ fontSize: '0.95rem', color: '#475569', fontWeight: 500 }}>🖼️ Generate Section Images</span>
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'not-allowed', opacity: 0.5, padding: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={options.generate_videos}
                                        disabled={true}
                                        style={{ width: '18px', height: '18px' }}
                                    />
                                    <span style={{ fontSize: '0.95rem', color: '#475569' }}>🎬 Generate Videos <span style={{ fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', fontWeight: 400 }}>(Beta)</span></span>
                                </label>
                            </div>
                        </div>

                        {/* Content Sections */}
                        <div style={{
                            background: '#f8fafc',
                            padding: '20px',
                            borderRadius: '16px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontWeight: 700, fontSize: '0.95rem', color: '#334155' }}>
                                <Layers size={18} color="#7c3aed" /> Include Sections
                            </label>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                                {[
                                    { key: 'include_key_terms', label: 'Key Terms & Definitions', icon: '🔑' },
                                    { key: 'include_summary', label: 'Summary Section', icon: '📝' },
                                    { key: 'include_think_about_it', label: 'Think About It Questions', icon: '🤔' }
                                ].map(section => (
                                    <label key={section.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: regenerating ? 'not-allowed' : 'pointer', padding: '4px' }}>
                                        <input
                                            type="checkbox"
                                            checked={(options as any)[section.key]}
                                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, [section.key]: e.target.checked })}
                                            disabled={regenerating}
                                            style={{ width: '18px', height: '18px', accentColor: '#7c3aed' }}
                                        />
                                        <span style={{ fontSize: '0.95rem', color: '#475569', fontWeight: 500 }}>{section.icon} {section.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Info & Actions */}
                <div style={{
                    marginTop: '32px',
                    paddingTop: '24px',
                    borderTop: '1px solid #f1f5f9',
                    display: 'flex',
                    flexDirection: isMobile ? 'column' : 'row',
                    alignItems: isMobile ? 'stretch' : 'center',
                    justifyContent: 'space-between',
                    gap: '20px'
                }}>
                    <div style={{
                        padding: '12px 16px',
                        background: '#eff6ff',
                        borderRadius: '12px',
                        fontSize: '0.85rem',
                        color: '#1e40af',
                        borderLeft: '4px solid #3b82f6',
                        maxWidth: isMobile ? 'none' : '450px'
                    }}>
                        <div style={{ fontWeight: 700, marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Info size={14} /> System Notice
                        </div>
                        Regeneration runs in the background. You can monitor progress in the Task Panel on the right.
                    </div>

                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={regenerating}
                            style={{
                                padding: '12px 24px',
                                borderRadius: '12px',
                                border: '1px solid #e2e8f0',
                                background: 'white',
                                color: '#64748b',
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                fontSize: '0.95rem',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => { if (!regenerating) e.currentTarget.style.background = '#f8fafc'; }}
                            onMouseLeave={(e) => { if (!regenerating) e.currentTarget.style.background = 'white'; }}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={regenerating}
                            style={{
                                padding: '12px 32px',
                                borderRadius: '12px',
                                border: 'none',
                                background: regenerating ? '#94a3b8' : 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
                                color: 'white',
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                fontWeight: 700,
                                fontSize: '0.95rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                boxShadow: regenerating ? 'none' : '0 10px 15px -3px rgba(124, 58, 237, 0.3)',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => { if (!regenerating) e.currentTarget.style.transform = 'translateY(-2px)'; }}
                            onMouseLeave={(e) => { if (!regenerating) e.currentTarget.style.transform = 'translateY(0)'; }}
                        >
                            {regenerating ? <RefreshCw size={18} className="animate-spin" /> : <Zap size={18} />}
                            {regenerating ? 'Initialising...' : 'Start Regeneration'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// ===========================================================================
// Content Browser Component
// ===========================================================================
const ContentBrowser = ({
    subjects,
    loadingSubjects,
    onRefresh,
    selectedSubtopicId,
    onSelectSubtopic,
    contents,
    loadingContents,
    selectedContent,
    onSelectContent,
    onEdit,
    onRegenerate,
    onDelete,
    regeneratingContent,
    onShowAdvancedOptions,
    isMobile,
    isTablet
}: {
    subjects: any[];
    loadingSubjects: boolean;
    onRefresh: () => void;
    selectedSubtopicId: string;
    onSelectSubtopic: (subtopicId: string) => void;
    contents: any[];
    loadingContents: boolean;
    selectedContent: any | null;
    onSelectContent: (content: any) => void;
    onEdit: (content: any) => void;
    onRegenerate: (content: any) => void;
    onDelete: (contentId: number) => void;
    regeneratingContent: Record<string, boolean>;
    onShowAdvancedOptions?: (subtopicId: string) => void;
    isMobile: boolean;
    isTablet: boolean;
}) => {
    const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
    const [expandedTopics, setExpandedTopics] = useState<Set<string>>(new Set());

    const toggleSubject = (subjectId: string) => {
        setExpandedSubjects(prev => {
            const next = new Set(prev);
            next.has(subjectId) ? next.delete(subjectId) : next.add(subjectId);
            return next;
        });
    };

    const toggleTopic = (topicId: string) => {
        setExpandedTopics(prev => {
            const next = new Set(prev);
            next.has(topicId) ? next.delete(topicId) : next.add(topicId);
            return next;
        });
    };

    // Fetch topics for a subject
    const [topicsCache, setTopicsCache] = useState<Record<string, any[]>>({});
    const [subtopicsCache, setSubtopicsCache] = useState<Record<string, any[]>>({});
    const [loadingSubtopics, setLoadingSubtopics] = useState<Record<string, boolean>>({});

    const fetchTopicsForSubject = async (subjectId: string) => {
        if (topicsCache[subjectId]) return;

        try {
            const data = await serviceFetch('aimaterials', `/api/db/subjects/${subjectId}/topics`);
            setTopicsCache(prev => ({ ...prev, [subjectId]: data }));
        } catch (err) {
            console.error('Error fetching topics', err);
        }
    };

    const fetchSubtopicsForTopic = async (topicId: string) => {
        if (subtopicsCache[topicId]) return;

        setLoadingSubtopics(prev => ({ ...prev, [topicId]: true }));
        try {
            const data = await serviceFetch('aimaterials', `/api/db/topics/${topicId}/subtopics`);
            setSubtopicsCache(prev => ({ ...prev, [topicId]: data }));
        } catch (err) {
            console.error('Error fetching subtopics', err);
        } finally {
            setLoadingSubtopics(prev => ({ ...prev, [topicId]: false }));
        }
    };

    const handleSubjectClick = (subjectId: string) => {
        toggleSubject(subjectId);
        if (!expandedSubjects.has(subjectId)) {
            fetchTopicsForSubject(subjectId);
        }
    };

    const handleTopicClick = (topicId: string) => {
        toggleTopic(topicId);
        if (!expandedTopics.has(topicId)) {
            fetchSubtopicsForTopic(topicId);
        }
    };

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : (isTablet ? '220px minmax(0, 1fr)' : '280px minmax(0, 1fr)'),
            gap: '24px',
            minWidth: 0
        }}>
            {/* Left: Tree View */}
            <div style={cardStyle(isMobile)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Browse Content</h3>
                    <button
                        onClick={onRefresh}
                        style={{ padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0', background: 'white', cursor: 'pointer' }}
                        disabled={loadingSubjects}
                    >
                        <RefreshCw size={16} color="#64748b" className={loadingSubjects ? 'animate-spin' : ''} />
                    </button>
                </div>

                {loadingSubjects ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>Loading...</div>
                ) : subjects.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>No subjects found</div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {subjects.map((subject: any) => (
                            <div key={subject.id}>
                                <div
                                    onClick={() => handleSubjectClick(subject.id)}
                                    style={{
                                        padding: '10px 12px',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        background: expandedSubjects.has(subject.id) ? '#f1f5f9' : 'transparent'
                                    }}
                                >
                                    {expandedSubjects.has(subject.id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                    <FolderOpen size={16} color="#3b82f6" />
                                    <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{subject.name}</span>
                                    <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: '#94a3b8' }}>
                                        {subject.content_count || 0}
                                    </span>
                                </div>

                                {expandedSubjects.has(subject.id) && topicsCache[subject.id] && (
                                    <div style={{ marginLeft: '20px', marginTop: '4px' }}>
                                        {topicsCache[subject.id].map((topic: any) => (
                                            <div key={topic.id}>
                                                <div
                                                    onClick={() => handleTopicClick(topic.id)}
                                                    style={{
                                                        padding: '8px 12px',
                                                        borderRadius: '6px',
                                                        cursor: 'pointer',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: '6px',
                                                        background: expandedTopics.has(topic.id) ? '#f8fafc' : 'transparent'
                                                    }}
                                                >
                                                    {expandedTopics.has(topic.id) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                                                    <span style={{ fontSize: '0.85rem' }}>{topic.name}</span>
                                                </div>

                                                {expandedTopics.has(topic.id) && loadingSubtopics[topic.id] && (
                                                    <div style={{ marginLeft: '20px', padding: '8px 12px', fontSize: '0.8rem', color: '#94a3b8' }}>
                                                        Loading subtopics...
                                                    </div>
                                                )}
                                                {expandedTopics.has(topic.id) && subtopicsCache[topic.id] && (
                                                    <div style={{ marginLeft: '20px' }}>
                                                        {subtopicsCache[topic.id].map((subtopic: any) => (
                                                            <div
                                                                key={subtopic.id}
                                                                onClick={() => onSelectSubtopic(subtopic.id)}
                                                                style={{
                                                                    padding: '6px 12px',
                                                                    borderRadius: '6px',
                                                                    cursor: 'pointer',
                                                                    display: 'flex',
                                                                    alignItems: 'center',
                                                                    gap: '6px',
                                                                    fontSize: '0.85rem',
                                                                    background: selectedSubtopicId === subtopic.id ? '#dbeafe' : 'transparent',
                                                                    color: selectedSubtopicId === subtopic.id ? '#1e40af' : 'inherit'
                                                                }}
                                                            >
                                                                <FileText size={14} />
                                                                {subtopic.name}
                                                            </div>
                                                        ))}
                                                    </div>
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

            {/* Right: Content Display */}
            <div style={{ ...cardStyle(isMobile), minWidth: 0, overflow: 'hidden' }}>
                {selectedContent ? (
                    <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <div>
                                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{selectedContent.subtopic_name}</h3>
                                <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
                                    {selectedContent.subject_name} → {selectedContent.topic_name}
                                </p>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    onClick={() => onRegenerate(selectedContent)}
                                    disabled={regeneratingContent[selectedContent.subtopic_id]}
                                    style={{
                                        padding: '8px 16px',
                                        borderRadius: '8px',
                                        border: 'none',
                                        background: regeneratingContent[selectedContent.subtopic_id] ? '#94a3b8' : '#7c3aed',
                                        color: 'white',
                                        cursor: regeneratingContent[selectedContent.subtopic_id] ? 'not-allowed' : 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        fontSize: '0.9rem',
                                        fontWeight: 600
                                    }}
                                >
                                    <Zap size={16} /> Regenerate
                                </button>
                                <button
                                    onClick={() => onEdit(selectedContent)}
                                    style={{
                                        padding: '8px 16px',
                                        borderRadius: '8px',
                                        border: 'none',
                                        background: '#2563eb',
                                        color: 'white',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        fontSize: '0.9rem',
                                        fontWeight: 600
                                    }}
                                >
                                    <Edit size={16} /> Edit
                                </button>
                                <button
                                    onClick={() => onDelete(selectedContent.id)}
                                    style={{
                                        padding: '8px 16px',
                                        borderRadius: '8px',
                                        border: 'none',
                                        background: '#ef4444',
                                        color: 'white',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        fontSize: '0.9rem',
                                        fontWeight: 600
                                    }}
                                >
                                    <Trash2 size={16} /> Delete
                                </button>
                            </div>
                        </div>

                        {/* Metadata */}
                        <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', fontSize: '0.8rem', color: '#64748b' }}>
                            <span>Version: {selectedContent.processor_version || 'unknown'}</span>
                            <span>â€¢</span>
                            <span>Processed: {new Date(selectedContent.processed_at).toLocaleDateString()}</span>
                        </div>

                        {/* HTML Content */}
                        <div style={{
                            padding: '24px',
                            border: '1px solid #e2e8f0',
                            borderRadius: '12px',
                            background: '#fafafa',
                            minHeight: '600px',
                            maxHeight: '850px',
                            overflowY: 'auto',
                            overflowX: 'hidden'
                        }}>
                            <div
                                dangerouslySetInnerHTML={{ __html: prefixImageUrls(selectedContent.html_content) }}
                                className="content-html-scope"
                            />
                        </div>

                        {/* Summary & Key Terms */}
                        {selectedContent.summary && (
                            <div style={{
                                marginTop: '16px',
                                padding: '16px',
                                background: '#fef3c7',
                                borderRadius: '8px',
                                borderLeft: '3px solid #f59e0b'
                            }}>
                                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginTop: 0, marginBottom: '8px' }}>Summary</h4>
                                <p style={{ fontSize: '0.9rem', margin: 0 }}>{selectedContent.summary}</p>
                            </div>
                        )}

                        {selectedContent.key_terms && (
                            <div style={{
                                marginTop: '16px',
                                padding: '16px',
                                background: '#dbeafe',
                                borderRadius: '8px',
                                borderLeft: '3px solid #3b82f6'
                            }}>
                                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginTop: 0, marginBottom: '8px' }}>Key Terms</h4>
                                <div
                                    className="content-html-scope"
                                    dangerouslySetInnerHTML={{ __html: prefixImageUrls(selectedContent.key_terms) }}
                                />
                            </div>
                        )}
                    </>
                ) : selectedSubtopicId ? (
                    loadingContents ? (
                        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>Loading content...</div>
                    ) : contents.length === 0 ? (
                        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#64748b' }}>
                            <FileText size={48} style={{ margin: '0 auto 20px', opacity: 0.3 }} />
                            <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '12px' }}>No Processed Content</div>
                            <div style={{ fontSize: '0.9rem', marginBottom: '24px', color: '#94a3b8' }}>
                                This subtopic has raw content but no processed version yet.
                            </div>
                            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginBottom: '16px' }}>
                                <button
                                    onClick={() => {
                                        // Create a dummy content object with just the subtopic_id for regeneration
                                        const dummyContent = { subtopic_id: selectedSubtopicId };
                                        onRegenerate(dummyContent);
                                    }}
                                    disabled={regeneratingContent[selectedSubtopicId]}
                                    style={{
                                        padding: '14px 28px',
                                        borderRadius: '12px',
                                        border: 'none',
                                        background: regeneratingContent[selectedSubtopicId] ? '#94a3b8' : '#7c3aed',
                                        color: 'white',
                                        cursor: regeneratingContent[selectedSubtopicId] ? 'not-allowed' : 'pointer',
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        fontSize: '1rem',
                                        fontWeight: 600
                                    }}
                                >
                                    {regeneratingContent[selectedSubtopicId] ? (
                                        <>
                                            <RefreshCw size={20} className="animate-spin" />
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <Zap size={20} />
                                            Quick Generate
                                        </>
                                    )}
                                </button>
                                <button
                                    onClick={() => {
                                        // Show modal with advanced options
                                        const dummyContent = { subtopic_id: selectedSubtopicId };
                                        onSelectContent(dummyContent);
                                        // This will trigger the modal through the parent component
                                        onShowAdvancedOptions?.(selectedSubtopicId);
                                    }}
                                    disabled={regeneratingContent[selectedSubtopicId]}
                                    style={{
                                        padding: '14px 28px',
                                        borderRadius: '12px',
                                        border: '1px solid #7c3aed',
                                        background: 'white',
                                        color: '#7c3aed',
                                        cursor: regeneratingContent[selectedSubtopicId] ? 'not-allowed' : 'pointer',
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        fontSize: '1rem',
                                        fontWeight: 600
                                    }}
                                >
                                    <Settings size={20} />
                                    Advanced Options
                                </button>
                            </div>
                            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                                This will process the raw content and create an enhanced version with AI.
                            </div>
                        </div>
                    ) : null
                ) : (
                    <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                        <FileText size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                        <div style={{ fontSize: '1rem' }}>Select a subtopic to view content</div>
                    </div>
                )}
            </div>
        </div>
    );
};

const AIMaterialsAdmin = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [subjectName, setSubjectName] = useState('');
    const [syllabus, setSyllabus] = useState('');
    const [uploading, setUploading] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');
    const [subtopicId, setSubtopicId] = useState('');

    // Tree picker state for upload form
    const [selectedLevel, setSelectedLevel] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedBoard, setSelectedBoard] = useState('');
    const [manualEntry, setManualEntry] = useState(false);
    const [activeTab, setActiveTab] = useState<'uploader' | 'database' | 'v8'>('uploader');
    const [subjects, setSubjects] = useState<any[]>([]);
    const [loadingSubjects, setLoadingSubjects] = useState(false);
    const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1200);
    const [currentV8TaskId, setCurrentV8TaskId] = useState<string | null>(null);
    const [v8TaskLogs, setV8TaskLogs] = useState<{ log_level: string; message: string; created_at: string }[]>([]);
    const [v8TaskProgress, setV8TaskProgress] = useState(0);
    const [v8TaskStatus, setV8TaskStatus] = useState<AdminV8TaskStatus>('idle');
    const [v8TaskMessage, setV8TaskMessage] = useState('');
    const [cancelRequestInFlight, setCancelRequestInFlight] = useState(false);

    useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const isTablet = windowWidth <= 1024;
    const isMobile = windowWidth <= 768;
    const isV8TaskActive = v8TaskStatus === 'pending' || v8TaskStatus === 'running' || v8TaskStatus === 'cancelling';
    const canCancelV8Task = !!currentV8TaskId && (v8TaskStatus === 'pending' || v8TaskStatus === 'running' || v8TaskStatus === 'cancelling');
    const showV8TaskPanel = !!currentV8TaskId || v8TaskStatus !== 'idle' || v8TaskLogs.length > 0;

    const fetchSubjects = async () => {
        setLoadingSubjects(true);
        try {
            const data = await serviceFetch('aimaterials', '/api/db/subjects');
            setSubjects(data);
        } catch (err) {
            console.error('Error fetching subjects', err);
        } finally {
            setLoadingSubjects(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'database') {
            fetchSubjects();
        }
        if (activeTab === 'v8') {
            fetchSubjects(); // Load subjects for V8 content browser (as fallback)
        }
    }, [activeTab]);

    useEffect(() => {
        let mounted = true;

        const recoverActiveTask = async () => {
            if (typeof window === 'undefined') return;

            const storedTaskId = window.localStorage.getItem(V8_ACTIVE_TASK_STORAGE_KEY);
            if (storedTaskId) {
                if (mounted) {
                    setCurrentV8TaskId(storedTaskId);
                }
                return;
            }

            try {
                const tasksData = await serviceFetch(
                    'aimaterials',
                    '/api/admin/v8/tasks?only_active=true&task_type=full_ingestion&limit=1'
                );
                const latestTask = Array.isArray(tasksData?.tasks) && tasksData.tasks.length > 0
                    ? tasksData.tasks[0]
                    : null;

                if (!mounted || !latestTask?.task_id) return;

                setCurrentV8TaskId(latestTask.task_id);
                setV8TaskProgress(Number(latestTask.progress || 0));
                setV8TaskStatus(normalizeV8TaskStatus(latestTask.status));
                setV8TaskMessage(latestTask.message || '');
                window.localStorage.setItem(V8_ACTIVE_TASK_STORAGE_KEY, latestTask.task_id);
            } catch (err) {
                console.error('Error recovering active V8 task', err);
            }
        };

        recoverActiveTask();
        return () => {
            mounted = false;
        };
    }, []);

    useEffect(() => {
        if (!currentV8TaskId) return;

        let mounted = true;
        let consecutivePollErrors = 0;
        let pollInterval: ReturnType<typeof setInterval> | null = null;

        const stopPolling = () => {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
        };

        const pollTask = async () => {
            try {
                const taskData = await serviceFetch('aimaterials', `/api/admin/v8/tasks/${currentV8TaskId}`);
                if (!mounted) return;

                consecutivePollErrors = 0;

                const taskStatus = normalizeV8TaskStatus(taskData.status);
                const taskProgress = Number(taskData.progress || 0);
                const taskMessage = taskData.message || '';

                setV8TaskStatus(taskStatus);
                setV8TaskProgress(taskProgress);
                setV8TaskMessage(taskMessage);
                if (taskData.logs) {
                    setV8TaskLogs(taskData.logs);
                }

                const activeTask = taskStatus === 'pending' || taskStatus === 'running' || taskStatus === 'cancelling';
                setUploading(activeTask);

                if (taskStatus === 'pending') {
                    setStatusMessage(`⏳ V8 ingestion queued... ${taskMessage}`.trim());
                } else if (taskStatus === 'running') {
                    setStatusMessage(`⚙️ V8 Processing: ${taskProgress}% — ${taskMessage}`.trim());
                } else if (taskStatus === 'cancelling') {
                    setStatusMessage('🛑 Cancellation requested. Waiting for current AI call to finish (can take 1-6 minutes).');
                } else if (taskStatus === 'completed') {
                    setStatusMessage(`✅ V8 ingestion complete! ${taskMessage}`.trim());
                    setTimeout(() => setActiveTab('v8'), 1000);
                } else if (taskStatus === 'failed') {
                    setStatusMessage(`❌ V8 ingestion failed: ${taskData.error || taskMessage || 'Unknown error'}`);
                } else if (taskStatus === 'cancelled') {
                    setStatusMessage('🛑 V8 ingestion cancelled.');
                }

                if (!activeTask) {
                    if (typeof window !== 'undefined') {
                        window.localStorage.removeItem(V8_ACTIVE_TASK_STORAGE_KEY);
                    }
                    stopPolling();
                }
            } catch (pollErr) {
                if (!mounted) return;

                console.error('Error polling V8 task', pollErr);
                consecutivePollErrors += 1;
                if (consecutivePollErrors >= 3) {
                    setStatusMessage('⚠️ Temporary connection issue while polling V8 task. Processing may still be running.');
                }
            }
        };

        pollTask();
        pollInterval = setInterval(pollTask, 3000);

        return () => {
            mounted = false;
            stopPolling();
        };
    }, [currentV8TaskId]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleUploadAndIngest = async () => {
        if (files.length === 0) {
            setStatusMessage('Please select at least one file.');
            return;
        }

        const mdFile = files.find(f => f.name.toLowerCase().endsWith('.md'));
        const pdfFile = files.find(f => f.name.toLowerCase().endsWith('.pdf'));
        if (!mdFile && !pdfFile) {
            setStatusMessage('At least one .md or .pdf file is required for ingestion.');
            return;
        }

        setUploading(true);
        setStatusMessage('📤 Uploading files...');

        try {
            const formData = new FormData();
            files.forEach(f => {
                formData.append('files', f);
            });

            const uploadRes = await serviceFetch('aimaterials', '/api/admin/upload', {
                method: 'POST',
                body: formData
            });

            // IMPORTANT: user-selected tree/manual values must take precedence.
            // Suggestions from upload/PDF conversion are only fallbacks.
            const treeSelectedSubject = (selectedBoard || selectedSubject || '').trim();
            const treeSelectedSyllabus = (selectedLevel || '').trim();

            const normalizedSubject = (treeSelectedSubject || subjectName).trim();
            const normalizedSyllabus = (treeSelectedSyllabus || syllabus).trim();

            const extractedSubject = normalizedSubject || (uploadRes.suggested_subject || '').trim();
            const extractedSyllabus = normalizedSyllabus || (uploadRes.suggested_syllabus || '').trim();
            const targetSubjectId = extractedSubject
                ? `${sanitizeIngestCode(extractedSyllabus || 'IGCSE')}_${sanitizeIngestCode(extractedSubject)}`
                : undefined;

            // Check for PDF conversion errors
            if (uploadRes.error) {
                setStatusMessage(`❌ Error: ${uploadRes.error}`);
                setUploading(false);
                return;
            }

            // Show conversion info if PDF was converted
            if (uploadRes.pdf_converted) {
                setStatusMessage('📝 PDF converted to markdown. Starting V8 ingestion...');
            } else {
                setStatusMessage('✅ Upload successful. Starting V8 ingestion...');
            }

            // Auto-populate only when user did not already provide values.
            if (uploadRes.suggested_subject && !normalizedSubject) {
                setSubjectName(uploadRes.suggested_subject);
            }
            if (uploadRes.suggested_syllabus && !normalizedSyllabus) {
                setSyllabus(uploadRes.suggested_syllabus);
            }

            if (!extractedSubject) {
                setStatusMessage('❌ Subject is required. Select it from the tree (Level → Subject/Board) or enter manually.');
                setUploading(false);
                return;
            }

            // Call V8 ingest endpoint instead of old pipeline
            const ingestRes = await serviceFetch('aimaterials', '/api/admin/v8/ingest', {
                method: 'POST',
                body: JSON.stringify({
                    batch_id: uploadRes.batch_id,
                    filename: uploadRes.main_markdown || mdFile?.name,
                    subject_name: extractedSubject,
                    syllabus: extractedSyllabus || 'IGCSE',
                    target_subject_id: targetSubjectId,
                })
            });

            setStatusMessage(`🚀 V8 ingestion started! Task ID: ${ingestRes.task_id}`);
            setFiles([]); // Clear after success
            setV8TaskLogs([]);
            setV8TaskProgress(0);
            setV8TaskStatus('pending');
            setV8TaskMessage('Task created');

            if (ingestRes.task_id) {
                setCurrentV8TaskId(ingestRes.task_id);
                if (typeof window !== 'undefined') {
                    window.localStorage.setItem(V8_ACTIVE_TASK_STORAGE_KEY, ingestRes.task_id);
                }
            } else {
                setUploading(false);
            }
        } catch (err: any) {
            console.error('Error in upload/V8 ingest', err);
            setStatusMessage(`❌ Error: ${err.message}`);
            setUploading(false);
        }
    };

    const handleDeleteSubject = async (subjectId: string) => {
        if (!confirm(`Are you sure you want to delete "${subjectId}"? This will recursively delete all topics, subtopics, content, and exercises. This action CANNOT be undone.`)) {
            return;
        }

        try {
            const res = await serviceFetch('aimaterials', `/api/admin/db/subjects/${subjectId}`, {
                method: 'DELETE'
            });
            setStatusMessage(`Subject deleted: ${res.message}`);
            fetchSubjects();
        } catch (err: any) {
            console.error('Error deleting subject', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleRenameSubject = async (subjectId: string, newName: string) => {
        try {
            const res = await serviceFetch('aimaterials', `/api/admin/db/subjects/${subjectId}`, {
                method: 'PATCH',
                body: JSON.stringify({ name: newName })
            });
            setStatusMessage(`Subject renamed: ${res.message}`);
            fetchSubjects();
        } catch (err: any) {
            console.error('Error renaming subject', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleCancelIngestion = async () => {
        if (!canCancelV8Task || !currentV8TaskId) return;
        if (!window.confirm('Cancel the currently running ingestion task?')) return;

        setCancelRequestInFlight(true);
        try {
            const cancelRes = await serviceFetch('aimaterials', `/api/admin/v8/tasks/${currentV8TaskId}/cancel`, {
                method: 'POST'
            });
            const nextStatus = normalizeV8TaskStatus(cancelRes?.status);
            if (nextStatus === 'cancelled') {
                setV8TaskStatus('cancelled');
                setV8TaskMessage(cancelRes?.message || 'Task cancelled before start');
                setStatusMessage('🛑 V8 ingestion cancelled.');
            } else {
                setV8TaskStatus('cancelling');
                setV8TaskMessage(cancelRes?.message || 'Cancellation requested by user');
                setStatusMessage('🛑 Cancellation requested. Waiting for current AI call to finish (can take 1-6 minutes).');
            }
        } catch (err: any) {
            console.error('Error cancelling V8 ingestion task', err);
            setStatusMessage(`❌ Failed to cancel ingestion: ${err.message || 'Unknown error'}`);
        } finally {
            setCancelRequestInFlight(false);
        }
    };

    const handleDismissTaskPanel = () => {
        if (isV8TaskActive) return;
        if (typeof window !== 'undefined') {
            window.localStorage.removeItem(V8_ACTIVE_TASK_STORAGE_KEY);
        }
        setCurrentV8TaskId(null);
        setV8TaskLogs([]);
        setV8TaskProgress(0);
        setV8TaskStatus('idle');
        setV8TaskMessage('');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <Link
                href="/admin"
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: '#64748b',
                    textDecoration: 'none',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    width: 'fit-content',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    transition: 'all 0.2s',
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0'
                }}
                onMouseOver={(e) => {
                    e.currentTarget.style.background = '#f1f5f9';
                    e.currentTarget.style.color = '#1e293b';
                }}
                onMouseOut={(e) => {
                    e.currentTarget.style.background = '#f8fafc';
                    e.currentTarget.style.color = '#64748b';
                }}
            >
                <ArrowLeft size={16} />
                Back to Admin Dashboard
            </Link>

            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr',
                gap: '24px',
                alignItems: 'start'
            }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', minWidth: 0 }}>
                    {/* Tab Navigation */}
                    <div style={{
                        display: 'flex',
                        gap: '8px',
                        background: '#f1f5f9',
                        padding: '6px',
                        borderRadius: '12px',
                        width: isMobile ? '100%' : 'fit-content',
                        overflowX: 'auto',
                        whiteSpace: 'nowrap',
                        WebkitOverflowScrolling: 'touch'
                    }}>
                        <button
                            onClick={() => setActiveTab('uploader')}
                            style={{
                                ...tabButtonStyle,
                                background: activeTab === 'uploader' ? 'white' : 'transparent',
                                boxShadow: activeTab === 'uploader' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                color: activeTab === 'uploader' ? '#1e293b' : '#64748b'
                            }}
                        >
                            <Upload size={16} /> Uploader
                        </button>
                        <button
                            onClick={() => setActiveTab('database')}
                            style={{
                                ...tabButtonStyle,
                                background: activeTab === 'database' ? 'white' : 'transparent',
                                boxShadow: activeTab === 'database' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                color: activeTab === 'database' ? '#1e293b' : '#64748b'
                            }}
                        >
                            <Database size={16} /> Database
                        </button>
                        <button
                            onClick={() => setActiveTab('v8')}
                            style={{
                                ...tabButtonStyle,
                                background: activeTab === 'v8' ? 'white' : 'transparent',
                                boxShadow: activeTab === 'v8' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                color: activeTab === 'v8' ? '#1e293b' : '#64748b'
                            }}
                        >
                            <Sparkles size={16} /> V8 Content
                        </button>
                    </div>

                    {showV8TaskPanel && (
                        <div style={{
                            background: v8TaskStatus === 'failed' ? '#fef2f2' :
                                v8TaskStatus === 'completed' ? '#f0fdf4' :
                                    v8TaskStatus === 'cancelled' ? '#fff7ed' : '#f8fafc',
                            borderRadius: '16px',
                            border: `1px solid ${v8TaskStatus === 'failed' ? '#fecaca' :
                                v8TaskStatus === 'completed' ? '#bbf7d0' :
                                    v8TaskStatus === 'cancelled' ? '#fed7aa' : '#e2e8f0'}`,
                            overflow: 'hidden',
                        }}>
                            <div style={{
                                padding: '16px 20px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                gap: '12px',
                                borderBottom: '1px solid #f1f5f9',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                                    {(v8TaskStatus === 'pending' || v8TaskStatus === 'running') && <RefreshCw size={18} className="animate-spin" color="#3b82f6" />}
                                    {v8TaskStatus === 'cancelling' && <AlertTriangle size={18} color="#ea580c" />}
                                    {v8TaskStatus === 'completed' && <CheckCircle2 size={18} color="#22c55e" />}
                                    {v8TaskStatus === 'failed' && <XCircle size={18} color="#ef4444" />}
                                    {v8TaskStatus === 'cancelled' && <Clock size={18} color="#ea580c" />}
                                    {v8TaskStatus === 'idle' && <Clock size={18} color="#64748b" />}
                                    <div style={{ minWidth: 0 }}>
                                        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1e293b' }}>
                                            {v8TaskStatus === 'pending' && `V8 Ingestion Queued — ${v8TaskProgress}%`}
                                            {v8TaskStatus === 'running' && `V8 Processing — ${v8TaskProgress}%`}
                                            {v8TaskStatus === 'cancelling' && `V8 Processing — Cancelling (${v8TaskProgress}%)`}
                                            {v8TaskStatus === 'completed' && 'V8 Ingestion Complete'}
                                            {v8TaskStatus === 'failed' && 'V8 Ingestion Failed'}
                                            {v8TaskStatus === 'cancelled' && 'V8 Ingestion Cancelled'}
                                            {v8TaskStatus === 'idle' && 'V8 Ingestion Monitor'}
                                        </div>
                                        {currentV8TaskId && (
                                            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                                                Task: {currentV8TaskId}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {canCancelV8Task && (
                                        <button
                                            onClick={handleCancelIngestion}
                                            disabled={cancelRequestInFlight || v8TaskStatus === 'cancelling'}
                                            style={{
                                                padding: '8px 12px',
                                                borderRadius: '10px',
                                                border: '1px solid #fdba74',
                                                background: '#fff7ed',
                                                color: '#9a3412',
                                                cursor: cancelRequestInFlight || v8TaskStatus === 'cancelling' ? 'not-allowed' : 'pointer',
                                                fontSize: '0.8rem',
                                                fontWeight: 700,
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '6px'
                                            }}
                                        >
                                            {(cancelRequestInFlight || v8TaskStatus === 'cancelling') ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
                                            {v8TaskStatus === 'cancelling' ? 'Cancelling...' : 'Cancel Ingestion'}
                                        </button>
                                    )}
                                    {!isV8TaskActive && (
                                        <button
                                            onClick={handleDismissTaskPanel}
                                            style={{
                                                background: 'transparent',
                                                border: 'none',
                                                color: '#64748b',
                                                cursor: 'pointer',
                                                padding: '4px',
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}
                                            title="Dismiss"
                                        >
                                            <XIcon size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>

                            {isV8TaskActive && (
                                <div style={{ height: '4px', background: '#e2e8f0' }}>
                                    <div style={{
                                        height: '100%',
                                        width: `${Math.max(0, Math.min(100, v8TaskProgress))}%`,
                                        background: v8TaskStatus === 'cancelling'
                                            ? 'linear-gradient(90deg, #f97316, #fb923c)'
                                            : 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                                        transition: 'width 0.5s ease',
                                    }} />
                                </div>
                            )}

                            {v8TaskMessage && (
                                <div style={{
                                    padding: '10px 16px',
                                    borderBottom: v8TaskLogs.length > 0 ? '1px solid #e2e8f0' : 'none',
                                    fontSize: '0.85rem',
                                    color: '#334155'
                                }}>
                                    {v8TaskMessage}
                                </div>
                            )}

                            {v8TaskLogs.length > 0 && (
                                <div style={{
                                    padding: '12px 16px',
                                    maxHeight: '260px',
                                    overflowY: 'auto',
                                    background: '#1e293b',
                                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                                    fontSize: '0.78rem',
                                    lineHeight: '1.6',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#64748b' }}>
                                        <Terminal size={14} />
                                        <span style={{ fontWeight: 600, fontSize: '0.75rem', textTransform: 'uppercase' as const, letterSpacing: '0.05em' }}>Live Logs</span>
                                    </div>
                                    {v8TaskLogs.slice().reverse().map((log, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                color: log.log_level === 'error' ? '#f87171' :
                                                    log.log_level === 'warning' ? '#fbbf24' : '#94a3b8',
                                                padding: '3px 0',
                                                borderBottom: idx < v8TaskLogs.length - 1 ? '1px solid #334155' : 'none',
                                            }}
                                        >
                                            <span style={{ color: '#475569', marginRight: '10px' }}>
                                                {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}
                                            </span>
                                            {log.message}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'uploader' ? (
                        <>
                            {/* Upload & Ingest Section */}
                            <div style={cardStyle(isMobile)}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                    <div style={{ background: '#fef3c7', padding: '8px', borderRadius: '8px' }}>
                                        <Book size={20} color="#d97706" />
                                    </div>
                                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Ingest New Textbook</h2>
                                </div>

                                {!manualEntry ? (
                                    <div style={{ marginBottom: '24px' }}>
                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: isMobile ? '1fr' : (isTablet ? '1fr 1fr' : '1fr 1fr 1fr'),
                                            gap: '16px',
                                            marginBottom: '12px'
                                        }}>
                                            {/* Level dropdown */}
                                            <div style={inputGroupStyle}>
                                                <label style={labelStyle}>Level</label>
                                                <select
                                                    style={{ ...inputStyle, cursor: 'pointer', background: 'white' }}
                                                    value={selectedLevel}
                                                    onChange={(e) => {
                                                        setSelectedLevel(e.target.value);
                                                        setSelectedSubject('');
                                                        setSelectedBoard('');
                                                        if (e.target.value) {
                                                            setSyllabus(e.target.value);
                                                            setSubjectName('');
                                                        }
                                                    }}
                                                >
                                                    <option value="">Select level...</option>
                                                    {Object.keys(DATATREE).map(level => (
                                                        <option key={level} value={level}>{level}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            {/* Subject dropdown */}
                                            <div style={inputGroupStyle}>
                                                <label style={labelStyle}>Subject</label>
                                                <select
                                                    style={{ ...inputStyle, cursor: selectedLevel ? 'pointer' : 'not-allowed', background: selectedLevel ? 'white' : '#f8fafc' }}
                                                    value={selectedSubject}
                                                    disabled={!selectedLevel}
                                                    onChange={(e) => {
                                                        setSelectedSubject(e.target.value);
                                                        setSelectedBoard('');
                                                        if (e.target.value) {
                                                            const boards = selectedLevel ? DATATREE[selectedLevel]?.[e.target.value] : [];
                                                            if (!boards || boards.length === 0) {
                                                                // No board variants (IB, HKDSE) â€” use subject name directly
                                                                setSubjectName(e.target.value);
                                                            } else {
                                                                // Keep subject selection as fallback even before board is chosen
                                                                setSubjectName(e.target.value);
                                                            }
                                                        }
                                                    }}
                                                >
                                                    <option value="">Select subject...</option>
                                                    {selectedLevel && DATATREE[selectedLevel] && Object.keys(DATATREE[selectedLevel]).sort().map(subject => (
                                                        <option key={subject} value={subject}>{subject}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            {/* Board variant dropdown â€” only show if boards exist */}
                                            <div style={inputGroupStyle}>
                                                <label style={labelStyle}>Board / Exam</label>
                                                <select
                                                    style={{
                                                        ...inputStyle,
                                                        cursor: (selectedSubject && selectedLevel && DATATREE[selectedLevel]?.[selectedSubject]?.length > 0) ? 'pointer' : 'not-allowed',
                                                        background: (selectedSubject && selectedLevel && DATATREE[selectedLevel]?.[selectedSubject]?.length > 0) ? 'white' : '#f8fafc'
                                                    }}
                                                    value={selectedBoard}
                                                    disabled={!selectedSubject || !selectedLevel || !(DATATREE[selectedLevel]?.[selectedSubject]?.length > 0)}
                                                    onChange={(e) => {
                                                        setSelectedBoard(e.target.value);
                                                        if (e.target.value) {
                                                            setSubjectName(e.target.value);
                                                        }
                                                    }}
                                                >
                                                    <option value="">
                                                        {selectedSubject && selectedLevel && DATATREE[selectedLevel]?.[selectedSubject]?.length === 0
                                                            ? 'N/A (no variants)'
                                                            : 'Select board...'}
                                                    </option>
                                                    {selectedLevel && selectedSubject && DATATREE[selectedLevel]?.[selectedSubject]?.map(board => (
                                                        <option key={board} value={board}>{board}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>

                                        {/* Breadcrumb showing selected path */}
                                        {(selectedLevel || subjectName) && (
                                            <div style={{
                                                padding: '8px 14px',
                                                background: '#f0f9ff',
                                                borderRadius: '8px',
                                                fontSize: '0.85rem',
                                                color: '#0369a1',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '6px',
                                                marginBottom: '4px'
                                            }}>
                                                <FileText size={14} />
                                                <span>
                                                    {selectedLevel}
                                                    {selectedSubject && <> â€º {selectedSubject}</>}
                                                    {selectedBoard && <> â€º {selectedBoard}</>}
                                                </span>
                                            </div>
                                        )}

                                        <button
                                            onClick={() => setManualEntry(true)}
                                            style={{ background: 'none', border: 'none', fontSize: '0.8rem', color: '#94a3b8', cursor: 'pointer', padding: '4px 0', textDecoration: 'underline' }}
                                        >
                                            or enter manually
                                        </button>
                                    </div>
                                ) : (
                                    <div style={{ marginBottom: '24px' }}>
                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
                                            gap: '20px',
                                            marginBottom: '8px'
                                        }}>
                                            <div style={inputGroupStyle}>
                                                <label style={labelStyle}>Subject Name</label>
                                                <input
                                                    style={inputStyle}
                                                    type="text"
                                                    value={subjectName}
                                                    onChange={(e) => setSubjectName(e.target.value)}
                                                    placeholder="e.g. AQA Chemistry (7405)"
                                                />
                                            </div>
                                            <div style={inputGroupStyle}>
                                                <label style={labelStyle}>Syllabus</label>
                                                <input
                                                    style={inputStyle}
                                                    type="text"
                                                    value={syllabus}
                                                    onChange={(e) => setSyllabus(e.target.value)}
                                                    placeholder="e.g. A-Level"
                                                />
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setManualEntry(false)}
                                            style={{ background: 'none', border: 'none', fontSize: '0.8rem', color: '#94a3b8', cursor: 'pointer', padding: '4px 0', textDecoration: 'underline' }}
                                        >
                                            â† back to tree selector
                                        </button>
                                    </div>
                                )}

                                <div style={{ marginBottom: '24px' }}>
                                    <label style={labelStyle}>Textbook File (.md or .pdf)</label>
                                    <div style={{
                                        border: '2px dashed #e2e8f0',
                                        borderRadius: '12px',
                                        padding: '32px',
                                        textAlign: 'center',
                                        cursor: 'pointer',
                                        transition: 'border-color 0.2s',
                                    }}>
                                        <input
                                            type="file"
                                            accept=".md,.json,.pdf"
                                            multiple
                                            onChange={handleFileChange}
                                            style={{ display: 'none' }}
                                            id="file-upload"
                                        />
                                        <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                                            <Upload size={40} color="#94a3b8" style={{ marginBottom: '12px' }} />
                                            <div style={{ fontWeight: 600, color: '#475569' }}>
                                                {files.length > 0 ? (
                                                    <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0' }}>
                                                        {files.map((f, i) => (
                                                            <li key={i} style={{ fontSize: '0.9rem', color: '#1e293b' }}>
                                                                {f.name.endsWith('.md') ? '📖 ' : f.name.endsWith('.pdf') ? '📄 ' : '⚙️ '} {f.name}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                ) : "Click to select markdown & structure JSON"}
                                            </div>
                                            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Select textbook (.md, .pdf) and optionally .structure.json</div>
                                        </label>
                                    </div>
                                </div>

                                <div style={{ display: 'flex', gap: '12px', flexDirection: isMobile ? 'column' : 'row' }}>
                                    <button
                                        onClick={() => handleUploadAndIngest()}
                                        disabled={uploading || files.length === 0}
                                        style={{
                                            ...buttonStyle,
                                            flex: 1,
                                            background: uploading || files.length === 0 ? '#94a3b8' : 'linear-gradient(135deg, #be123c 0%, #9f1239 100%)',
                                        }}
                                    >
                                        {uploading ? (
                                            <><RefreshCw size={18} className="animate-spin" /> Processing...</>
                                        ) : (
                                            <><Zap size={18} /> Upload & Generate V8 Content</>
                                        )}
                                    </button>
                                </div>
                            </div>

                        </>
                    ) : activeTab === 'database' ? (
                        /* Database Filesystem Tree */
                        <DatabaseFilesystemTree
                            subjects={subjects}
                            loadingSubjects={loadingSubjects}
                            onRefresh={fetchSubjects}
                            onDeleteSubject={handleDeleteSubject}
                            onRenameSubject={handleRenameSubject}
                            isMobile={isMobile}
                            isTablet={isTablet}
                        />
                    ) : activeTab === 'v8' ? (
                        <V8ContentBrowser
                            subjects={subjects}
                            loadingSubjects={loadingSubjects}
                            isMobile={isMobile}
                        />
                    ) : null}

                    {/* Status Message — visible on all tabs */}
                    {statusMessage && (
                        <div style={{
                            padding: '14px 20px',
                            background: statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? '#fef2f2' : statusMessage.includes('âœ…') ? '#f0fdf4' : '#f0f9ff',
                            borderLeft: `5px solid ${statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? '#ef4444' : statusMessage.includes('âœ…') ? '#22c55e' : '#0ea5e9'}`,
                            borderRadius: '12px',
                            fontSize: '0.95rem',
                            fontWeight: 600,
                            color: statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? '#991b1b' : statusMessage.includes('âœ…') ? '#166534' : '#0369a1',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '16px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                            animation: 'fadeIn 0.3s ease-out'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                {statusMessage.includes('âœ…') ? <CheckCircle2 size={18} /> :
                                    (statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? <AlertTriangle size={18} /> : <Clock size={18} />)}
                                <span>{statusMessage}</span>
                            </div>
                            <button
                                onClick={() => setStatusMessage('')}
                                style={{
                                    background: statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? '#fee2e2' : statusMessage.includes('âœ…') ? '#dcfce7' : '#e0f2fe',
                                    border: 'none',
                                    color: 'inherit',
                                    cursor: 'pointer',
                                    padding: '6px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transition: 'all 0.2s',
                                    flexShrink: 0
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'scale(1.1)';
                                    e.currentTarget.style.background = 'white';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.background = statusMessage.startsWith('Error') || statusMessage.includes('âŒ') ? '#fee2e2' : statusMessage.includes('âœ…') ? '#dcfce7' : '#e0f2fe';
                                }}
                                title="Dismiss"
                            >
                                <XIcon size={18} strokeWidth={2.5} />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const cardStyle = (isMobile?: boolean) => ({
    background: 'white',
    padding: isMobile ? '20px' : '32px',
    borderRadius: '24px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
});

const inputGroupStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
};

const labelStyle = {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#475569',
};


const buttonStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    padding: '14px 24px',
    borderRadius: '12px',
    color: 'white',
    fontWeight: 600,
    fontSize: '0.95rem',
    border: 'none',
    width: '100%',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

const tabButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    fontWeight: 600,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

// ===========================================================================
// Database Filesystem Tree Component
// ===========================================================================
const DatabaseFilesystemTree = ({ subjects, loadingSubjects, onRefresh, onDeleteSubject, onRenameSubject, isMobile, isTablet }: {
    subjects: any[];
    loadingSubjects: boolean;
    onRefresh: () => void;
    onDeleteSubject: (id: string) => void;
    onRenameSubject: (id: string, newName: string) => void;
    isMobile: boolean;
    isTablet: boolean;
}) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set());
    const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [tempName, setTempName] = useState('');

    const { treeWithData, unmatched } = matchSubjectsToTree(subjects);

    const toggleLevel = (level: string) => {
        setExpandedLevels(prev => {
            const next = new Set(prev);
            next.has(level) ? next.delete(level) : next.add(level);
            return next;
        });
    };

    const toggleSubject = (key: string) => {
        setExpandedSubjects(prev => {
            const next = new Set(prev);
            next.has(key) ? next.delete(key) : next.add(key);
            return next;
        });
    };

    // Filter tree by search
    const filterMatches = (name: string) => {
        if (!searchQuery) return true;
        return name.toLowerCase().includes(searchQuery.toLowerCase());
    };

    // Count how many DB subjects exist under a level
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
        <div style={cardStyle(isMobile)}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ background: '#dbeafe', padding: '8px', borderRadius: '8px' }}>
                        <Database size={20} color="#2563eb" />
                    </div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Content Database</h2>
                </div>
                <button
                    onClick={onRefresh}
                    style={{ padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0', background: 'white', cursor: 'pointer' }}
                    disabled={loadingSubjects}
                >
                    <RefreshCw size={16} color="#64748b" className={loadingSubjects ? 'animate-spin' : ''} />
                </button>
            </div>

            {/* Warning */}
            <div style={{
                background: '#fff7ed', border: '1px solid #ffedd5', borderRadius: '12px',
                padding: '12px 16px', marginBottom: '16px', display: 'flex', gap: '10px', alignItems: 'center'
            }}>
                <AlertTriangle size={16} color="#ea580c" style={{ flexShrink: 0 }} />
                <p style={{ color: '#c2410c', fontSize: '0.8rem', lineHeight: '1.4', margin: 0 }}>
                    Unified database â€” deleting subjects here removes them from <strong>AI Tutor</strong> too.
                </p>
            </div>

            {/* Search */}
            <div style={{ position: 'relative', marginBottom: '20px' }}>
                <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                <input
                    type="text"
                    placeholder="Search subjects..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                        ...inputStyle,
                        paddingLeft: '36px',
                    }}
                />
            </div>

            {/* Tree */}
            {loadingSubjects ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Loading database...</div>
            ) : (
                <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace', fontSize: '0.85rem' }}>
                    {Object.entries(treeWithData).map(([level, subjectsMap]) => {
                        const stats = levelStats(level);
                        const isExpanded = expandedLevels.has(level);

                        // Filter: 
                        // 1. If searching, only show levels with matching subjects
                        // 2. If NOT searching, only show levels that have at least one subject with content in DB
                        const visibleSubjects = Object.entries(subjectsMap).filter(([name, data]) => {
                            const matchesSearch = filterMatches(name);
                            if (searchQuery) return matchesSearch;

                            // Check if this subject or any of its boards has content
                            const hasContent = data.dbSubject || data.boards.some(b => b.dbSubject);
                            return hasContent;
                        });

                        if (visibleSubjects.length === 0) return null;

                        return (
                            <div key={level} style={{ marginBottom: '4px' }}>
                                {/* Level row */}
                                <button
                                    onClick={() => toggleLevel(level)}
                                    style={{
                                        width: '100%', padding: '10px 8px', border: 'none',
                                        background: isExpanded ? '#f0f9ff' : 'transparent',
                                        cursor: 'pointer', textAlign: 'left',
                                        display: 'flex', alignItems: 'center', gap: '8px',
                                        borderRadius: '8px', transition: 'background 0.15s',
                                    }}
                                    onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.background = '#f8fafc'; }}
                                    onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.background = 'transparent'; }}
                                >
                                    {isExpanded ? <ChevronDown size={16} color="#3b82f6" /> : <ChevronRight size={16} color="#64748b" />}
                                    {isExpanded ? <FolderOpen size={18} color="#3b82f6" /> : <Folder size={18} color="#64748b" />}
                                    <span style={{ fontWeight: 700, color: isExpanded ? '#1d4ed8' : '#1e293b', fontFamily: 'inherit' }}>{level}/</span>
                                    <span style={{
                                        marginLeft: 'auto', fontSize: '0.7rem', padding: '2px 8px',
                                        borderRadius: '10px', fontFamily: 'system-ui',
                                        background: stats.withContent > 0 ? '#dbeafe' : '#f1f5f9',
                                        color: stats.withContent > 0 ? '#2563eb' : '#94a3b8',
                                        fontWeight: 600,
                                    }}>
                                        {stats.withContent}/{stats.total}
                                    </span>
                                </button>

                                {/* Subjects under this level */}
                                {isExpanded && (
                                    <div style={{ paddingLeft: '24px', borderLeft: '1px solid #e2e8f0', marginLeft: '16px' }}>
                                        {visibleSubjects.map(([subjectName, subjectData]) => {
                                            const hasBoards = subjectData.boards.length > 0;
                                            const subjectKey = `${level}/${subjectName}`;
                                            const isSubjectExpanded = expandedSubjects.has(subjectKey);

                                            // For subjects without boards (IB, HKDSE)
                                            if (!hasBoards) {
                                                const db = subjectData.dbSubject;
                                                const isRenaming = db && renamingId === db.id;

                                                return (
                                                    <div key={subjectKey} style={{
                                                        display: 'flex', alignItems: 'center', gap: '8px',
                                                        padding: '6px 8px', borderRadius: '6px',
                                                        opacity: db ? 1 : 0.5,
                                                    }}>
                                                        <FileText size={15} color={db ? '#3b82f6' : '#cbd5e1'} />
                                                        {isRenaming ? (
                                                            <input
                                                                autoFocus
                                                                value={tempName}
                                                                onChange={(e) => setTempName(e.target.value)}
                                                                onKeyDown={(e) => {
                                                                    if (e.key === 'Enter') {
                                                                        onRenameSubject(db.id, tempName);
                                                                        setRenamingId(null);
                                                                    } else if (e.key === 'Escape') {
                                                                        setRenamingId(null);
                                                                    }
                                                                }}
                                                                onBlur={() => setRenamingId(null)}
                                                                style={{
                                                                    ...inputStyle,
                                                                    padding: '2px 8px',
                                                                    fontSize: '0.85rem',
                                                                    height: 'auto',
                                                                }}
                                                            />
                                                        ) : (
                                                            <span style={{ color: db ? '#1e293b' : '#94a3b8', fontFamily: 'inherit' }}>
                                                                {db?.name || subjectName}
                                                            </span>
                                                        )}
                                                        {db && !isRenaming && (
                                                            <>
                                                                <span style={{
                                                                    fontSize: '0.7rem', padding: '1px 6px', borderRadius: '8px',
                                                                    background: '#ecfdf5', color: '#059669', fontWeight: 600, fontFamily: 'system-ui',
                                                                }}>
                                                                    {db.topic_count}T Â· {db.subtopic_count}S
                                                                </span>
                                                                <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
                                                                    <button
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            setRenamingId(db.id);
                                                                            setTempName(subjectName);
                                                                        }}
                                                                        style={{
                                                                            padding: '3px 6px', borderRadius: '4px',
                                                                            border: 'none', background: '#f1f5f9', color: '#64748b',
                                                                            cursor: 'pointer', fontSize: '0.7rem', fontWeight: 600,
                                                                            display: 'flex', alignItems: 'center',
                                                                        }}
                                                                        title="Rename subject"
                                                                    >
                                                                        <Edit2 size={11} />
                                                                    </button>
                                                                    <button
                                                                        onClick={(e) => { e.stopPropagation(); onDeleteSubject(db.id); }}
                                                                        style={{
                                                                            padding: '3px 6px', borderRadius: '4px',
                                                                            border: 'none', background: '#fee2e2', color: '#dc2626',
                                                                            cursor: 'pointer', fontSize: '0.7rem', fontWeight: 600,
                                                                            display: 'flex', alignItems: 'center', gap: '3px',
                                                                        }}
                                                                        title="Delete subject"
                                                                    >
                                                                        <Trash2 size={11} />
                                                                    </button>
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                );
                                            }

                                            // For subjects with boards (A-Level, IGCSE)
                                            const boardsWithContent = subjectData.boards.filter(b => b.dbSubject).length;
                                            return (
                                                <div key={subjectKey} style={{ marginBottom: '2px' }}>
                                                    <button
                                                        onClick={() => toggleSubject(subjectKey)}
                                                        style={{
                                                            width: '100%', padding: '6px 8px', border: 'none',
                                                            background: isSubjectExpanded ? '#f8fafc' : 'transparent',
                                                            cursor: 'pointer', textAlign: 'left',
                                                            display: 'flex', alignItems: 'center', gap: '6px',
                                                            borderRadius: '6px', transition: 'background 0.15s',
                                                        }}
                                                        onMouseEnter={(e) => { if (!isSubjectExpanded) e.currentTarget.style.background = '#fafafa'; }}
                                                        onMouseLeave={(e) => { if (!isSubjectExpanded) e.currentTarget.style.background = 'transparent'; }}
                                                    >
                                                        {isSubjectExpanded ? <ChevronDown size={14} color="#64748b" /> : <ChevronRight size={14} color="#94a3b8" />}
                                                        {isSubjectExpanded
                                                            ? <FolderOpen size={16} color={boardsWithContent > 0 ? '#3b82f6' : '#94a3b8'} />
                                                            : <Folder size={16} color={boardsWithContent > 0 ? '#3b82f6' : '#cbd5e1'} />
                                                        }
                                                        <span style={{
                                                            color: boardsWithContent > 0 ? '#1e293b' : '#94a3b8',
                                                            fontFamily: 'inherit',
                                                        }}>
                                                            {(subjectData.dbSubject?.name || subjectName)}/
                                                        </span>
                                                        {boardsWithContent > 0 && (
                                                            <span style={{
                                                                fontSize: '0.65rem', padding: '1px 6px', borderRadius: '8px',
                                                                background: '#dbeafe', color: '#2563eb', fontWeight: 600, fontFamily: 'system-ui',
                                                            }}>
                                                                {boardsWithContent}/{subjectData.boards.length}
                                                            </span>
                                                        )}
                                                    </button>

                                                    {/* Board-level items */}
                                                    {isSubjectExpanded && (
                                                        <div style={{ paddingLeft: '24px', borderLeft: '1px solid #f1f5f9', marginLeft: '14px' }}>
                                                            {subjectData.boards.map((board) => {
                                                                const db = board.dbSubject;
                                                                const isRenaming = db && renamingId === db.id;

                                                                return (
                                                                    <div key={board.name} style={{
                                                                        display: 'flex', alignItems: 'center', gap: '6px',
                                                                        padding: '4px 8px', borderRadius: '4px',
                                                                        opacity: db ? 1 : 0.45,
                                                                    }}>
                                                                        <FileText size={14} color={db ? '#3b82f6' : '#cbd5e1'} />
                                                                        {isRenaming ? (
                                                                            <input
                                                                                autoFocus
                                                                                value={tempName}
                                                                                onChange={(e) => setTempName(e.target.value)}
                                                                                onKeyDown={(e) => {
                                                                                    if (e.key === 'Enter') {
                                                                                        onRenameSubject(db.id, tempName);
                                                                                        setRenamingId(null);
                                                                                    } else if (e.key === 'Escape') {
                                                                                        setRenamingId(null);
                                                                                    }
                                                                                }}
                                                                                onBlur={() => setRenamingId(null)}
                                                                                style={{
                                                                                    ...inputStyle,
                                                                                    padding: '1px 6px',
                                                                                    fontSize: '0.8rem',
                                                                                    height: 'auto',
                                                                                    margin: 0,
                                                                                }}
                                                                            />
                                                                        ) : (
                                                                            <span style={{
                                                                                fontSize: '0.8rem', color: db ? '#334155' : '#94a3b8',
                                                                                fontFamily: 'inherit',
                                                                            }}>
                                                                                {db?.name || board.name}
                                                                            </span>
                                                                        )}
                                                                        {db && !isRenaming && (
                                                                            <>
                                                                                <span style={{
                                                                                    fontSize: '0.65rem', padding: '1px 6px', borderRadius: '8px',
                                                                                    background: '#ecfdf5', color: '#059669', fontWeight: 600, fontFamily: 'system-ui',
                                                                                }}>
                                                                                    {db.topic_count}T Â· {db.subtopic_count}S
                                                                                </span>
                                                                                <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
                                                                                    <button
                                                                                        onClick={(e) => {
                                                                                            e.stopPropagation();
                                                                                            setRenamingId(db.id);
                                                                                            setTempName(board.name);
                                                                                        }}
                                                                                        style={{
                                                                                            padding: '2px 5px', borderRadius: '4px',
                                                                                            border: 'none', background: '#f1f5f9', color: '#64748b',
                                                                                            cursor: 'pointer', fontSize: '0.65rem', fontWeight: 600,
                                                                                            display: 'flex', alignItems: 'center',
                                                                                        }}
                                                                                        title="Rename subject"
                                                                                    >
                                                                                        <Edit2 size={10} />
                                                                                    </button>
                                                                                    <button
                                                                                        onClick={(e) => { e.stopPropagation(); onDeleteSubject(db.id); }}
                                                                                        style={{
                                                                                            padding: '2px 5px', borderRadius: '4px',
                                                                                            border: 'none', background: '#fee2e2', color: '#dc2626',
                                                                                            cursor: 'pointer', fontSize: '0.65rem', fontWeight: 600,
                                                                                            display: 'flex', alignItems: 'center', gap: '2px',
                                                                                        }}
                                                                                        title="Delete subject"
                                                                                    >
                                                                                        <Trash2 size={10} />
                                                                                    </button>
                                                                                </div>
                                                                            </>
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

                    {/* Unmatched DB subjects */}
                    {unmatched.length > 0 && (
                        <div style={{ marginTop: '8px' }}>
                            <div style={{
                                padding: '10px 8px', display: 'flex', alignItems: 'center', gap: '8px',
                                borderRadius: '8px', background: '#fefce8',
                            }}>
                                <FolderOpen size={18} color="#ca8a04" />
                                <span style={{ fontWeight: 700, color: '#854d0e', fontFamily: 'inherit' }}>Other (unlinked)/</span>
                                <span style={{
                                    fontSize: '0.7rem', padding: '2px 8px', borderRadius: '10px',
                                    background: '#fef9c3', color: '#a16207', fontWeight: 600, fontFamily: 'system-ui',
                                }}>{unmatched.length}</span>
                            </div>
                            <div style={{ paddingLeft: '24px', borderLeft: '1px solid #fde68a', marginLeft: '16px' }}>
                                {unmatched.map((sub) => (
                                    <div key={sub.id} style={{
                                        display: 'flex', alignItems: 'center', gap: '6px',
                                        padding: '4px 8px', borderRadius: '4px',
                                    }}>
                                        <FileText size={14} color="#ca8a04" />
                                        <span style={{ fontSize: '0.8rem', color: '#854d0e', fontFamily: 'inherit' }}>{sub.name}</span>
                                        <span style={{
                                            fontSize: '0.65rem', padding: '1px 6px', borderRadius: '8px',
                                            background: '#ecfdf5', color: '#059669', fontWeight: 600, fontFamily: 'system-ui',
                                        }}>
                                            {sub.topic_count}T Â· {sub.subtopic_count}S
                                        </span>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onDeleteSubject(sub.id); }}
                                            style={{
                                                marginLeft: 'auto', padding: '2px 5px', borderRadius: '4px',
                                                border: 'none', background: '#fee2e2', color: '#dc2626',
                                                cursor: 'pointer', fontSize: '0.65rem', fontWeight: 600,
                                                display: 'flex', alignItems: 'center', gap: '2px',
                                            }}
                                            title="Delete subject"
                                        >
                                            <Trash2 size={10} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// ===========================================================================
// Subject/Topic/Subtopic Browser Component (for Exercises tab)
// ===========================================================================
const SubjectExerciseBrowser = ({ subject, onSelectSubtopic, selectedSubtopicId, isMobile }: any) => {
    const [expanded, setExpanded] = useState(false);
    const [topics, setTopics] = useState<any[]>([]);
    const [loadingTopics, setLoadingTopics] = useState(false);

    const handleExpand = async () => {
        if (!expanded && topics.length === 0) {
            setLoadingTopics(true);
            try {
                const data = await serviceFetch('aimaterials', `/api/db/subjects/${subject.id}/topics`);
                setTopics(data);
            } catch (err) {
                console.error('Error fetching topics', err);
            } finally {
                setLoadingTopics(false);
            }
        }
        setExpanded(!expanded);
    };

    return (
        <div style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
            <button
                onClick={handleExpand}
                style={{
                    width: '100%',
                    padding: '8px',
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.9rem',
                    fontWeight: 600
                }}
            >
                {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                {subject.name}
            </button>

            {expanded && (
                <div style={{ paddingLeft: '20px', marginTop: '8px' }}>
                    {loadingTopics ? (
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Loading...</div>
                    ) : (
                        topics.map((topic: any) => (
                            <TopicBrowser
                                key={topic.id}
                                topic={topic}
                                onSelectSubtopic={onSelectSubtopic}
                                selectedSubtopicId={selectedSubtopicId}
                            />
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

const TopicBrowser = ({ topic, onSelectSubtopic, selectedSubtopicId }: any) => {
    const [expanded, setExpanded] = useState(false);
    const [subtopics, setSubtopics] = useState<any[]>([]);
    const [loadingSubtopics, setLoadingSubtopics] = useState(false);

    const handleExpand = async () => {
        if (!expanded && subtopics.length === 0) {
            setLoadingSubtopics(true);
            try {
                const data = await serviceFetch('aimaterials', `/api/db/topics/${topic.id}/subtopics`);
                setSubtopics(data);
            } catch (err) {
                console.error('Error fetching subtopics', err);
            } finally {
                setLoadingSubtopics(false);
            }
        }
        setExpanded(!expanded);
    };

    return (
        <div style={{ marginBottom: '4px' }}>
            <button
                onClick={handleExpand}
                style={{
                    width: '100%',
                    padding: '6px',
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.85rem'
                }}
            >
                {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {topic.name}
            </button>

            {expanded && (
                <div style={{ paddingLeft: '16px', marginTop: '4px' }}>
                    {loadingSubtopics ? (
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Loading...</div>
                    ) : (
                        subtopics.map((subtopic: any) => (
                            <button
                                key={subtopic.id}
                                onClick={() => onSelectSubtopic(subtopic.id)}
                                style={{
                                    width: '100%',
                                    padding: '6px 8px',
                                    border: 'none',
                                    background: selectedSubtopicId === subtopic.id ? '#e0e7ff' : 'transparent',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                    fontSize: '0.8rem',
                                    borderRadius: '4px',
                                    marginBottom: '2px',
                                    color: selectedSubtopicId === subtopic.id ? '#4f46e5' : '#475569'
                                }}
                            >
                                {subtopic.name}
                            </button>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};



export default AIMaterialsAdmin;
