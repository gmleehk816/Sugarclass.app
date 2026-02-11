"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { serviceFetch } from '@/lib/microservices';
import ChunkEditor from './components/ChunkEditor';
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
    Link,
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
    CornerDownLeft,
    MousePointer2,
    Sparkles
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
        .replace(/[-\s]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .substring(0, 50);
}

function matchSubjectsToTree(dbSubjects: DbSubject[]) {
    const matched = new Set<string>();
    const subjectIdMap: Record<string, DbSubject> = {};

    // Build a lookup: subject ID â†’ DbSubject
    for (const sub of dbSubjects) {
        subjectIdMap[sub.id] = sub;
    }

    // Try to match each tree leaf to a DB subject
    const treeWithData: Record<string, Record<string, { boards: { name: string; dbSubject?: DbSubject }[]; dbSubject?: DbSubject }>> = {};

    for (const [level, subjects] of Object.entries(DATATREE)) {
        treeWithData[level] = {};
        for (const [subjectName, boards] of Object.entries(subjects)) {
            const boardEntries = boards.map(boardName => {
                const targetId = sanitizeId(boardName);
                const db = subjectIdMap[targetId];
                if (db) matched.add(db.id);
                return { name: boardName, dbSubject: db };
            });

            const subjectId = sanitizeId(subjectName);
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
}

// ===========================================================================
// Content Regenerate Modal Component
// ===========================================================================
const ContentRegenerateModal = ({
    options,
    setOptions,
    onConfirm,
    onClose,
    regenerating
}: {
    options: RegenerateOptions;
    setOptions: (options: RegenerateOptions) => void;
    onConfirm: () => void;
    onClose: () => void;
    regenerating: boolean;
}) => {
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
                borderRadius: '16px',
                padding: '32px',
                maxWidth: '500px',
                width: '100%'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
                        Regenerate Content v2
                    </h2>
                    <button
                        onClick={onClose}
                        disabled={regenerating}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '1.5rem',
                            cursor: regenerating ? 'not-allowed' : 'pointer',
                            color: '#64748b',
                            padding: '4px'
                        }}
                    >
                        x
                    </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {/* Focus Option */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Enhancement Focus
                        </label>
                        <select
                            value={options.focus}
                            onChange={(e) => setOptions({ ...options, focus: e.target.value })}
                            disabled={regenerating}
                            style={{
                                ...inputStyle,
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                background: regenerating ? '#f8fafc' : 'white'
                            }}
                        >
                            {focusOptions.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Media Generation */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Media Generation
                        </label>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: regenerating ? 'not-allowed' : 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={options.generate_images}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, generate_images: e.target.checked })}
                                    disabled={regenerating}
                                />
                                <span style={{ fontSize: '0.9rem' }}>🖼️ Generate Images for Topics</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'not-allowed', opacity: 0.5 }}>
                                <input
                                    type="checkbox"
                                    checked={options.generate_videos}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, generate_videos: e.target.checked })}
                                    disabled={true}
                                />
                                <span style={{ fontSize: '0.9rem' }}>🎬 Generate Videos <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic' }}>(coming soon)</span></span>
                            </label>
                        </div>
                    </div>

                    {/* Creativity Level */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Creativity Level: {options.temperature.toFixed(1)}
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={options.temperature}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, temperature: parseFloat(e.target.value) })}
                            disabled={regenerating}
                            style={{ width: '100%', cursor: regenerating ? 'not-allowed' : 'pointer' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                            <span>Conservative</span>
                            <span>Balanced</span>
                            <span>Creative</span>
                        </div>
                    </div>

                    {/* Content Sections */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600, fontSize: '0.9rem' }}>
                            Include Sections
                        </label>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: regenerating ? 'not-allowed' : 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={options.include_key_terms}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, include_key_terms: e.target.checked })}
                                    disabled={regenerating}
                                />
                                <span style={{ fontSize: '0.9rem' }}>Key Terms & Definitions</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: regenerating ? 'not-allowed' : 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={options.include_summary}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, include_summary: e.target.checked })}
                                    disabled={regenerating}
                                />
                                <span style={{ fontSize: '0.9rem' }}>Summary Section</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: regenerating ? 'not-allowed' : 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={options.include_think_about_it}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOptions({ ...options, include_think_about_it: e.target.checked })}
                                    disabled={regenerating}
                                />
                                <span style={{ fontSize: '0.9rem' }}>Think About It Questions</span>
                            </label>
                        </div>
                    </div>

                    {/* Info */}
                    <div style={{
                        padding: '12px',
                        background: '#eff6ff',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        color: '#1e40af',
                        borderLeft: '3px solid #3b82f6'
                    }}>
                        <strong>Note:</strong> Regeneration will create a new enhanced version using AI. This process runs in the background and may take a minute.
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={regenerating}
                            style={{
                                padding: '12px 24px',
                                borderRadius: '8px',
                                border: '1px solid #e2e8f0',
                                background: 'white',
                                color: '#64748b',
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                fontWeight: 600
                            }}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={regenerating}
                            style={{
                                padding: '12px 24px',
                                borderRadius: '8px',
                                border: 'none',
                                background: regenerating ? '#94a3b8' : '#7c3aed',
                                color: 'white',
                                cursor: regenerating ? 'not-allowed' : 'pointer',
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}
                        >
                            {regenerating ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
                            {regenerating ? 'Starting...' : 'Regenerate'}
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
    onShowAdvancedOptions
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
        <div style={{ display: 'grid', gridTemplateColumns: '280px minmax(0, 1fr)', gap: '24px', minWidth: 0 }}>
            {/* Left: Tree View */}
            <div style={cardStyle}>
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
            <div style={{ ...cardStyle, minWidth: 0, overflow: 'hidden' }}>
                {selectedContent ? (
                    <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <div>
                                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>{selectedContent.subtopic_name}</h3>
                                <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
                                    {selectedContent.subject_name} â†’ {selectedContent.topic_name}
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
                            minHeight: '400px',
                            maxHeight: '600px',
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
    const [tasks, setTasks] = useState<Record<string, any>>({});
    const [statusMessage, setStatusMessage] = useState('');
    const [subtopicId, setSubtopicId] = useState('');

    // Tree picker state for upload form
    const [selectedLevel, setSelectedLevel] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedBoard, setSelectedBoard] = useState('');
    const [manualEntry, setManualEntry] = useState(false);
    const [loadingTasks, setLoadingTasks] = useState(false);
    const [activeTab, setActiveTab] = useState<'uploader' | 'database' | 'exercises' | 'contents'>('uploader');
    const [subjects, setSubjects] = useState<any[]>([]);
    const [loadingSubjects, setLoadingSubjects] = useState(false);

    // Exercise management state
    const [exercises, setExercises] = useState<any[]>([]);
    const [selectedSubtopicId, setSelectedSubtopicId] = useState<string>('');
    const [loadingExercises, setLoadingExercises] = useState(false);
    const [editingExercise, setEditingExercise] = useState<any | null>(null);
    const [showExerciseModal, setShowExerciseModal] = useState(false);
    const [generatingExercises, setGeneratingExercises] = useState<Record<string, boolean>>({});
    const [generationTasks, setGenerationTasks] = useState<Record<string, string>>({});

    // Content management state
    const [contents, setContents] = useState<any[]>([]);
    const [selectedContentSubtopicId, setSelectedContentSubtopicId] = useState<string>('');
    const [loadingContents, setLoadingContents] = useState(false);
    const [selectedContent, setSelectedContent] = useState<any | null>(null);
    const [editingContent, setEditingContent] = useState<any | null>(null);
    const [showContentEditModal, setShowContentEditModal] = useState(false);
    const [showRegenerateModal, setShowRegenerateModal] = useState(false);
    const [regeneratingContent, setRegeneratingContent] = useState<Record<string, boolean>>({});
    const [regenerateOptions, setRegenerateOptions] = useState({
        focus: '',
        temperature: 0.7,
        include_key_terms: true,
        include_summary: true,
        include_think_about_it: true,
        generate_images: false,
        generate_videos: false
    });

    const fetchTasks = async () => {
        try {
            const data = await serviceFetch('aimaterials', '/api/admin/tasks');
            setTasks(data);
        } catch (err) {
            console.error('Error fetching tasks', err);
        }
    };

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
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (activeTab === 'database') {
            fetchSubjects();
        }
        if (activeTab === 'exercises') {
            fetchSubjects(); // Load subjects for exercise browser
        }
        if (activeTab === 'contents') {
            fetchSubjects(); // Load subjects for content browser
        }
    }, [activeTab]);

    const fetchExercises = async (subtopicId: string) => {
        setLoadingExercises(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/exercises?subtopic_id=${subtopicId}`);
            setExercises(data);
            setSelectedSubtopicId(subtopicId);
        } catch (err) {
            console.error('Error fetching exercises', err);
        } finally {
            setLoadingExercises(false);
        }
    };

    const handleSaveExercise = async (formData: any) => {
        try {
            if (editingExercise) {
                // Update existing
                await serviceFetch('aimaterials', `/api/admin/exercises/${editingExercise.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                setStatusMessage('Exercise updated successfully');
            } else {
                // Create new
                await serviceFetch('aimaterials', '/api/admin/exercises', {
                    method: 'POST',
                    body: JSON.stringify({ ...formData, subtopic_id: selectedSubtopicId })
                });
                setStatusMessage('Exercise created successfully');
            }
            setShowExerciseModal(false);
            setEditingExercise(null);
            fetchExercises(selectedSubtopicId);
        } catch (err: any) {
            console.error('Error saving exercise', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleDeleteExercise = async (exerciseId: number) => {
        if (!confirm('Are you sure you want to delete this question?')) return;

        try {
            await serviceFetch('aimaterials', `/api/admin/exercises/${exerciseId}`, {
                method: 'DELETE'
            });
            setStatusMessage('Exercise deleted');
            fetchExercises(selectedSubtopicId);
        } catch (err: any) {
            console.error('Error deleting exercise', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleUploadAndIngest = async () => {
        if (files.length === 0) {
            setStatusMessage('Please select at least one markdown file.');
            return;
        }

        const mdFile = files.find(f => f.name.endsWith('.md'));
        if (!mdFile) {
            setStatusMessage('At least one .md file is required for ingestion.');
            return;
        }

        setUploading(true);
        setStatusMessage('Uploading files...');

        try {
            const formData = new FormData();
            files.forEach(f => {
                formData.append('files', f);
            });

            const uploadRes = await serviceFetch('aimaterials', '/api/admin/upload', {
                method: 'POST',
                body: formData
            });

            // Extract suggested metadata from upload response
            const extractedSubject = uploadRes.suggested_subject || subjectName;
            const extractedSyllabus = uploadRes.suggested_syllabus || syllabus;

            // Auto-populate form fields for visual feedback
            if (uploadRes.suggested_subject) {
                setSubjectName(uploadRes.suggested_subject);
            }
            if (uploadRes.suggested_syllabus) {
                setSyllabus(uploadRes.suggested_syllabus);
            }

            setStatusMessage('Upload successful. Starting ingestion...');

            // Use the extracted values directly (not state, which updates async)
            const ingestRes = await serviceFetch('aimaterials', '/api/admin/ingest', {
                method: 'POST',
                body: JSON.stringify({
                    batch_id: uploadRes.batch_id,
                    filename: uploadRes.main_markdown || mdFile.name,
                    subject_name: extractedSubject,
                    syllabus: extractedSyllabus
                })
            });

            setStatusMessage(`Ingestion started! Task ID: ${ingestRes.task_id}`);
            fetchTasks();
            setFiles([]); // Clear after success
        } catch (err: any) {
            console.error('Error in upload/ingest', err);
            setStatusMessage(`Error: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleGenerateExercises = async (subtopicId: string, generateImages: boolean = true, count: number = 5) => {
        setGeneratingExercises(prev => ({ ...prev, [subtopicId]: true }));
        try {
            const response = await serviceFetch('aimaterials', '/api/admin/generate-exercises', {
                method: 'POST',
                body: JSON.stringify({
                    subtopic_id: subtopicId,
                    generate_images: generateImages,
                    count: count
                }),
            });

            const taskId = response.task_id;
            setGenerationTasks(prev => ({ ...prev, [subtopicId]: taskId }));

            // Poll task status
            const pollInterval = setInterval(async () => {
                try {
                    const taskStatus = await serviceFetch('aimaterials', `/api/admin/tasks/${taskId}`);

                    if (taskStatus.status === 'completed') {
                        clearInterval(pollInterval);
                        setGeneratingExercises(prev => ({ ...prev, [subtopicId]: false }));
                        // Refresh exercises if this is the currently selected subtopic
                        if (selectedSubtopicId === subtopicId) {
                            await fetchExercises(subtopicId);
                        }
                    } else if (taskStatus.status === 'failed') {
                        clearInterval(pollInterval);
                        setGeneratingExercises(prev => ({ ...prev, [subtopicId]: false }));
                        alert(`Generation failed: ${taskStatus.message}`);
                    }
                } catch (err) {
                    console.error('Error polling task status', err);
                }
            }, 3000);

            // Stop polling after 5 minutes
            setTimeout(() => clearInterval(pollInterval), 300000);

        } catch (err) {
            console.error('Error generating exercises', err);
            setGeneratingExercises(prev => ({ ...prev, [subtopicId]: false }));
            alert('Failed to start exercise generation');
        }
    };

    const handleRegenerateExercise = async (exerciseId: number, subtopicId: string) => {
        if (!confirm('Are you sure you want to regenerate this question? The current one will be deleted.')) return;

        try {
            // 1. Delete the exercise
            await serviceFetch('aimaterials', `/api/admin/exercises/${exerciseId}`, {
                method: 'DELETE'
            });

            // 2. Generate a new one
            await handleGenerateExercises(subtopicId, true, 1);

            setStatusMessage('Regeneration started...');
        } catch (err: any) {
            console.error('Error regenerating exercise', err);
            setStatusMessage(`Error: ${err.message}`);
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

    // Content management handlers
    const fetchContents = async (subtopicId: string) => {
        setLoadingContents(true);
        try {
            const data = await serviceFetch('aimaterials', `/api/admin/contents?subtopic_id=${subtopicId}`);
            setContents(data);
            setSelectedContentSubtopicId(subtopicId);
            if (data.length > 0) {
                setSelectedContent(data[0]);
            } else {
                setSelectedContent(null);
            }
        } catch (err) {
            console.error('Error fetching contents', err);
        } finally {
            setLoadingContents(false);
        }
    };

    const handleSaveContent = async (formData: any) => {
        try {
            await serviceFetch('aimaterials', `/api/admin/contents/${editingContent.id}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });
            setStatusMessage('Content updated successfully');
            setShowContentEditModal(false);
            setEditingContent(null);
            fetchContents(selectedContentSubtopicId);
        } catch (err: any) {
            console.error('Error saving content', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleDeleteContent = async (contentId: number) => {
        if (!confirm('Are you sure you want to delete this processed content? The raw content will be preserved for re-processing.')) {
            return;
        }

        try {
            await serviceFetch('aimaterials', `/api/admin/contents/${contentId}`, {
                method: 'DELETE'
            });
            setStatusMessage('Content deleted successfully. Raw content preserved.');
            fetchContents(selectedContentSubtopicId);
        } catch (err: any) {
            console.error('Error deleting content', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleRegenerateContent = async () => {
        if (!selectedContent) return;

        const subtopicId = selectedContent.subtopic_id;
        setRegeneratingContent(prev => ({ ...prev, [subtopicId]: true }));

        try {
            // Use default options for quick generation, or modal options if set
            const options = showRegenerateModal ? regenerateOptions : {
                focus: '',
                temperature: 0.7,
                include_key_terms: true,
                include_summary: true,
                include_think_about_it: true,
                generate_images: false,
                generate_videos: false
            };

            const result = await serviceFetch('aimaterials', `/api/admin/contents/regenerate?subtopic_id=${subtopicId}`, {
                method: 'POST',
                body: JSON.stringify(options)
            });
            setShowRegenerateModal(false);
            setStatusMessage('Content regeneration started...');
            fetchTasks(); // Refresh to see the task

            const taskId = result.task_id;

            // Poll for task completion and refresh contents
            const pollInterval = setInterval(async () => {
                try {
                    fetchTasks();
                    if (taskId) {
                        const taskStatus = await serviceFetch('aimaterials', `/api/admin/tasks/${taskId}`);
                        if (taskStatus.status === 'completed') {
                            clearInterval(pollInterval);
                            setRegeneratingContent(prev => ({ ...prev, [subtopicId]: false }));
                            setStatusMessage('âœ… Content regenerated successfully!');
                            fetchContents(subtopicId);
                        } else if (taskStatus.status === 'failed') {
                            clearInterval(pollInterval);
                            setRegeneratingContent(prev => ({ ...prev, [subtopicId]: false }));
                            setStatusMessage(`âŒ Regeneration failed: ${taskStatus.message}`);
                        }
                    } else {
                        fetchContents(subtopicId);
                    }
                } catch (pollErr) {
                    console.error('Error polling task', pollErr);
                }
            }, 3000);

            // Stop polling after 2 minutes
            setTimeout(() => {
                clearInterval(pollInterval);
                setRegeneratingContent(prev => ({ ...prev, [subtopicId]: false }));
            }, 120000);
        } catch (err: any) {
            console.error('Error regenerating content', err);
            setStatusMessage(`Error: ${err.message}`);
            setRegeneratingContent(prev => ({ ...prev, [selectedContent.subtopic_id]: false }));
        }
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: '24px', alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', minWidth: 0 }}>
                {/* Tab Navigation */}
                <div style={{ display: 'flex', gap: '8px', background: '#f1f5f9', padding: '6px', borderRadius: '12px', width: 'fit-content' }}>
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
                        onClick={() => setActiveTab('exercises')}
                        style={{
                            ...tabButtonStyle,
                            background: activeTab === 'exercises' ? 'white' : 'transparent',
                            boxShadow: activeTab === 'exercises' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                            color: activeTab === 'exercises' ? '#1e293b' : '#64748b'
                        }}
                    >
                        <ListOrdered size={16} /> Exercises
                    </button>
                    <button
                        onClick={() => setActiveTab('contents')}
                        style={{
                            ...tabButtonStyle,
                            background: activeTab === 'contents' ? 'white' : 'transparent',
                            boxShadow: activeTab === 'contents' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                            color: activeTab === 'contents' ? '#1e293b' : '#64748b'
                        }}
                    >
                        <FileText size={16} /> Contents
                    </button>
                </div>

                {activeTab === 'uploader' ? (
                    <>
                        {/* Upload & Ingest Section */}
                        <div style={cardStyle}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                <div style={{ background: '#fef3c7', padding: '8px', borderRadius: '8px' }}>
                                    <Book size={20} color="#d97706" />
                                </div>
                                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Ingest New Textbook</h2>
                            </div>

                            {!manualEntry ? (
                                <div style={{ marginBottom: '24px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '12px' }}>
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
                                                            setSubjectName('');
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
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '8px' }}>
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
                                <label style={labelStyle}>Textbook Markdown (.md)</label>
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
                                        accept=".md,.json"
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
                                                            {f.name.endsWith('.md') ? 'ðŸ“– ' : 'âš™ï¸ '} {f.name}
                                                        </li>
                                                    ))}
                                                </ul>
                                            ) : "Click to select markdown & structure JSON"}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Select textbook (.md) and optionally .structure.json</div>
                                    </label>
                                </div>
                            </div>

                            <button
                                onClick={handleUploadAndIngest}
                                disabled={uploading || files.length === 0}
                                style={{
                                    ...buttonStyle,
                                    background: uploading || files.length === 0 ? '#94a3b8' : '#1e293b',
                                }}
                            >
                                {uploading ? (
                                    <><RefreshCw size={18} className="animate-spin" /> Processing...</>
                                ) : (
                                    <><Zap size={18} /> Upload & Process Content</>
                                )}
                            </button>
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
                    />
                ) : activeTab === 'exercises' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px' }}>
                        {/* Subject/Topic/Subtopic Browser */}
                        <div style={cardStyle}>
                            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '16px' }}>Browse Subjects</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {loadingSubjects ? (
                                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>Loading...</div>
                                ) : subjects.length === 0 ? (
                                    <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>No subjects found</div>
                                ) : (
                                    subjects.map((subject: any) => (
                                        <SubjectExerciseBrowser
                                            key={subject.id}
                                            subject={subject}
                                            onSelectSubtopic={fetchExercises}
                                            selectedSubtopicId={selectedSubtopicId}
                                        />
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Exercise List */}
                        <div style={cardStyle}>
                            {selectedSubtopicId ? (
                                <>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Questions ({exercises.length})</h3>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button
                                                onClick={() => handleGenerateExercises(selectedSubtopicId, true, 1)}
                                                disabled={generatingExercises[selectedSubtopicId]}
                                                style={{
                                                    padding: '8px 16px',
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    background: generatingExercises[selectedSubtopicId] ? '#94a3b8' : '#7c3aed',
                                                    color: 'white',
                                                    cursor: generatingExercises[selectedSubtopicId] ? 'not-allowed' : 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '6px',
                                                    fontSize: '0.9rem',
                                                    fontWeight: 600,
                                                    opacity: generatingExercises[selectedSubtopicId] ? 0.6 : 1
                                                }}
                                            >
                                                <Zap size={16} /> {generatingExercises[selectedSubtopicId] && generationTasks[selectedSubtopicId] ? 'Generating...' : 'Generate One'}
                                            </button>
                                            <button
                                                onClick={() => handleGenerateExercises(selectedSubtopicId, true, 5)}
                                                disabled={generatingExercises[selectedSubtopicId]}
                                                style={{
                                                    padding: '8px 16px',
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    background: generatingExercises[selectedSubtopicId] ? '#94a3b8' : '#4f46e5',
                                                    color: 'white',
                                                    cursor: generatingExercises[selectedSubtopicId] ? 'not-allowed' : 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '6px',
                                                    fontSize: '0.9rem',
                                                    fontWeight: 600,
                                                    opacity: generatingExercises[selectedSubtopicId] ? 0.6 : 1
                                                }}
                                            >
                                                <Zap size={16} /> {generatingExercises[selectedSubtopicId] && generationTasks[selectedSubtopicId] ? 'Generating...' : 'Generate 5 with AI'}
                                            </button>
                                            <button
                                                onClick={() => { setEditingExercise(null); setShowExerciseModal(true); }}
                                                style={{
                                                    padding: '8px 16px',
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    background: '#10b981',
                                                    color: 'white',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '6px',
                                                    fontSize: '0.9rem',
                                                    fontWeight: 600
                                                }}
                                            >
                                                <Plus size={16} /> Add Question
                                            </button>
                                        </div>
                                    </div>

                                    {loadingExercises ? (
                                        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Loading exercises...</div>
                                    ) : exercises.length === 0 ? (
                                        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
                                            No exercises yet. Click "Add Question" to create one.
                                        </div>
                                    ) : (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                            {exercises.map((ex: any) => (
                                                <QuestionCard
                                                    key={ex.id}
                                                    exercise={ex}
                                                    onEdit={() => { setEditingExercise(ex); setShowExerciseModal(true); }}
                                                    onDelete={() => handleDeleteExercise(ex.id)}
                                                    onRegenerate={() => handleRegenerateExercise(ex.id, selectedSubtopicId)}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                                    <ListOrdered size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                                    <div style={{ fontSize: '1rem' }}>Select a subtopic to view exercises</div>
                                </div>
                            )}
                        </div>
                    </div>
                ) : activeTab === 'contents' ? (
                    <ContentBrowser
                        subjects={subjects}
                        loadingSubjects={loadingSubjects}
                        onRefresh={fetchSubjects}
                        selectedSubtopicId={selectedContentSubtopicId}
                        onSelectSubtopic={fetchContents}
                        contents={contents}
                        loadingContents={loadingContents}
                        selectedContent={selectedContent}
                        onSelectContent={setSelectedContent}
                        onEdit={(content) => { setEditingContent(content); setShowContentEditModal(true); }}
                        onRegenerate={(content) => { setSelectedContent(content); setShowRegenerateModal(true); }}
                        onDelete={handleDeleteContent}
                        regeneratingContent={regeneratingContent}
                        onShowAdvancedOptions={(subtopicId) => {
                            setSelectedContent({ subtopic_id: subtopicId });
                            setShowRegenerateModal(true);
                        }}
                    />
                ) : null}

                {/* Status Message â€” visible on all tabs */}
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

            {/* Task monitor on the right */}
            <div style={{ ...cardStyle, border: 'none', background: '#f8fafc', position: 'sticky', top: '120px', width: '300px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Task Monitor</h3>
                    <RefreshCw size={16} color="#64748b" style={{ cursor: 'pointer' }} onClick={fetchTasks} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {Object.keys(tasks).length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <Clock size={32} color="#cbd5e1" style={{ marginBottom: '12px' }} />
                            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>No active tasks</div>
                        </div>
                    ) : (
                        Object.entries(tasks).map(([id, info]: [string, any]) => (
                            <div key={id} style={{
                                background: 'white',
                                padding: '16px',
                                borderRadius: '12px',
                                border: '1px solid #e2e8f0',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '8px'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'monospace', color: '#94a3b8' }}>#{id.slice(0, 8)}</span>
                                    {info.status === 'completed' && <CheckCircle2 size={16} color="#22c55e" />}
                                    {info.status === 'failed' && <XCircle size={16} color="#ef4444" />}
                                    {info.status === 'running' && <RefreshCw size={16} color="#3b82f6" className="animate-spin" />}
                                </div>
                                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>
                                    {info.status.charAt(0).toUpperCase() + info.status.slice(1)}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {info.status === 'running' ? 'Ingesting...' : info.message}
                                </div>

                                {info.logs && info.logs.length > 0 && (
                                    <div style={{
                                        marginTop: '12px',
                                        padding: '12px',
                                        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                                        borderRadius: '10px',
                                        minHeight: '200px',
                                        maxHeight: '300px',
                                        overflowY: 'auto',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '4px',
                                        boxShadow: info.status === 'running' ? '0 0 20px rgba(59, 130, 246, 0.3)' : 'none',
                                        border: info.status === 'running' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid #334155'
                                    }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
                                            <Terminal size={14} color={info.status === 'running' ? '#3b82f6' : '#94a3b8'} />
                                            <span style={{ fontSize: '0.75rem', color: info.status === 'running' ? '#3b82f6' : '#94a3b8', fontWeight: 700, letterSpacing: '0.05em' }}>LIVE LOGS</span>
                                            {info.status === 'running' && (
                                                <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: '#22c55e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', animation: 'pulse 1.5s infinite' }}></span>
                                                    Processing
                                                </span>
                                            )}
                                        </div>
                                        {info.logs.slice(-15).map((log: string, i: number) => (
                                            <div key={i} style={{
                                                fontSize: '0.7rem',
                                                fontFamily: 'ui-monospace, monospace',
                                                color: i === info.logs.slice(-15).length - 1 ? '#22d3ee' : '#e2e8f0',
                                                opacity: i === info.logs.slice(-15).length - 1 ? 1 : 0.75,
                                                lineHeight: 1.5,
                                                paddingLeft: '8px',
                                                borderLeft: i === info.logs.slice(-15).length - 1 ? '2px solid #22d3ee' : '2px solid transparent'
                                            }}>
                                                {log}
                                            </div>
                                        ))}
                                        <div ref={(el) => { if (el) el.scrollIntoView({ behavior: 'smooth' }); }} />
                                    </div>
                                )}
                            </div>
                        )).reverse()
                    )}
                </div>
            </div>

            {/* Exercise Modal */}
            {showExerciseModal && (
                <ExerciseModal
                    exercise={editingExercise}
                    onClose={() => {
                        setShowExerciseModal(false);
                        setEditingExercise(null);
                    }}
                    onSave={handleSaveExercise}
                />
            )}

            {/* Content Edit Modal */}
            {showContentEditModal && editingContent && (
                <ChunkEditor
                    content={editingContent}
                    onClose={() => {
                        setShowContentEditModal(false);
                        setEditingContent(null);
                    }}
                    onSave={handleSaveContent}
                />
            )}

            {/* Content Regenerate Modal */}
            {showRegenerateModal && selectedContent && (
                <ContentRegenerateModal
                    options={regenerateOptions}
                    setOptions={setRegenerateOptions}
                    onConfirm={handleRegenerateContent}
                    onClose={() => setShowRegenerateModal(false)}
                    regenerating={regeneratingContent[selectedContent.subtopic_id] || false}
                />
            )}

        </div>
    );
};

const cardStyle = {
    background: 'white',
    padding: '32px',
    borderRadius: '24px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
};

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
const DatabaseFilesystemTree = ({ subjects, loadingSubjects, onRefresh, onDeleteSubject, onRenameSubject }: {
    subjects: any[];
    loadingSubjects: boolean;
    onRefresh: () => void;
    onDeleteSubject: (id: string) => void;
    onRenameSubject: (id: string, newName: string) => void;
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
        <div style={cardStyle}>
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

                        // Filter: if searching, only show levels with matching subjects
                        const visibleSubjects = Object.entries(subjectsMap).filter(([name]) => filterMatches(name));
                        if (searchQuery && visibleSubjects.length === 0) return null;

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
const SubjectExerciseBrowser = ({ subject, onSelectSubtopic, selectedSubtopicId }: any) => {
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
                <span>{expanded ? 'â–¼' : 'â–¶'}</span>
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
                <span style={{ fontSize: '0.7rem' }}>{expanded ? 'â–¼' : 'â–¶'}</span>
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
