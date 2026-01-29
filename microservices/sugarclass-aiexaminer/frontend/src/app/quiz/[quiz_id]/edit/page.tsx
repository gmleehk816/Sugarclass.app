'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Edit3, Save, X, Trash2, Plus, RotateCcw, CheckCircle } from 'lucide-react';
import Navbar from '@/components/Navbar';

interface Question {
    question: string;
    question_type: 'mcq' | 'short';
    options?: string[];
    correct_answer?: string;
    expected_answer?: string;
    key_points?: string[];
    explanation?: string;
}

interface Quiz {
    id: string;
    title: string;
    questions: Question[];
    material_id?: string;
    created_at: string;
}

export default function QuizEditorPage({ params }: { params: { quiz_id: string } }) {
    const router = useRouter();
    const [quiz, setQuiz] = useState<Quiz | null>(null);
    const [editedTitle, setEditedTitle] = useState('');
    const [editedQuestions, setEditedQuestions] = useState<Question[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [editingIndex, setEditingIndex] = useState<number | null>(null);

    useEffect(() => {
        fetchQuiz();
    }, [params.quiz_id]);

    const fetchQuiz = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/${params.quiz_id}`);
            if (!response.ok) throw new Error('Quiz not found');
            const data = await response.json();
            setQuiz(data);
            setEditedTitle(data.title);
            setEditedQuestions(JSON.parse(JSON.stringify(data.questions))); // Deep copy
        } catch (error) {
            console.error('Failed to fetch quiz:', error);
            alert('Quiz not found');
            router.push('/');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/${params.quiz_id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: editedTitle,
                    questions: editedQuestions
                }),
            });

            if (!response.ok) throw new Error('Failed to save');

            alert('Quiz saved successfully!');
            router.push('/');
        } catch (error) {
            console.error('Save failed:', error);
            alert('Failed to save quiz');
        } finally {
            setIsSaving(false);
        }
    };

    const handleQuestionChange = (index: number, field: string, value: any) => {
        const updated = [...editedQuestions];
        (updated[index] as any)[field] = value;
        setEditedQuestions(updated);
    };

    const handleOptionChange = (questionIndex: number, optionIndex: number, value: string) => {
        const updated = [...editedQuestions];
        if (updated[questionIndex].options) {
            updated[questionIndex].options![optionIndex] = value;
            setEditedQuestions(updated);
        }
    };

    const handleDeleteQuestion = (index: number) => {
        if (!confirm('Delete this question?')) return;
        setEditedQuestions(editedQuestions.filter((_, i) => i !== index));
    };

    const handleAddQuestion = (type: 'mcq' | 'short') => {
        const newQuestion: Question = type === 'mcq'
            ? {
                question: 'New question',
                question_type: 'mcq',
                options: ['Option A', 'Option B', 'Option C', 'Option D'],
                correct_answer: 'Option A',
                explanation: ''
            }
            : {
                question: 'New question',
                question_type: 'short',
                expected_answer: '',
                key_points: [],
                explanation: ''
            };
        setEditedQuestions([...editedQuestions, newQuestion]);
        setEditingIndex(editedQuestions.length);
    };

    if (isLoading) {
        return (
            <main className="min-h-screen bg-background">
                <Navbar />
                <div className="container mx-auto px-6 py-12 flex justify-center">
                    <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-background">
            <Navbar />
            <div className="container mx-auto px-6 py-12 md:px-10 max-w-5xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex-1">
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-muted text-accent text-xs font-black uppercase tracking-widest mb-4">
                            <Edit3 size={14} />
                            <span>Exercise Editor</span>
                        </div>
                        <input
                            type="text"
                            value={editedTitle}
                            onChange={(e) => setEditedTitle(e.target.value)}
                            className="text-4xl font-black text-primary mb-2 tracking-tight w-full border-0 border-b-2 border-transparent focus:border-primary outline-none bg-transparent"
                        />
                        <p className="text-slate-500 text-sm">{editedQuestions.length} questions • Click on any field to edit</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => router.push('/')}
                            className="px-6 py-3 rounded-xl border border-card-border bg-white text-slate-600 font-bold hover:bg-slate-50 transition-all"
                        >
                            <X size={18} className="inline mr-2" />
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="px-6 py-3 rounded-xl bg-success text-white font-bold hover:bg-success/90 transition-all shadow-lg active:scale-95 disabled:opacity-50 flex items-center gap-2"
                        >
                            <Save size={18} />
                            {isSaving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>

                {/* Questions List */}
                <div className="space-y-6 mb-8">
                    {editedQuestions.map((question, index) => (
                        <div key={index} className="premium-card p-6 bg-white/80 group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center font-black text-sm">
                                        {index + 1}
                                    </span>
                                    <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest ${question.question_type === 'short'
                                        ? 'bg-amber-100 text-amber-600'
                                        : 'bg-blue-100 text-blue-600'
                                        }`}>
                                        {question.question_type === 'short' ? 'Short Answer' : 'Multiple Choice'}
                                    </span>
                                </div>
                                <button
                                    onClick={() => handleDeleteQuestion(index)}
                                    className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                                    title="Delete Question"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>

                            {/* Question Text */}
                            <textarea
                                value={question.question}
                                onChange={(e) => handleQuestionChange(index, 'question', e.target.value)}
                                className="w-full text-lg font-bold text-primary mb-4 p-3 rounded-lg border border-card-border focus:border-primary focus:ring-2 focus:ring-primary-muted outline-none resize-none"
                                rows={2}
                            />

                            {/* MCQ Options */}
                            {question.question_type === 'mcq' && question.options && (
                                <div className="space-y-3 mb-4">
                                    {question.options.map((option, optIdx) => (
                                        <div key={optIdx} className="flex items-center gap-3">
                                            <input
                                                type="radio"
                                                checked={question.correct_answer === option}
                                                onChange={() => handleQuestionChange(index, 'correct_answer', option)}
                                                className="w-4 h-4 text-success"
                                            />
                                            <input
                                                type="text"
                                                value={option}
                                                onChange={(e) => handleOptionChange(index, optIdx, e.target.value)}
                                                className={`flex-1 px-4 py-3 rounded-xl border text-sm font-medium outline-none focus:ring-2 ${option === question.correct_answer
                                                    ? 'bg-success/10 border-success/30 text-success focus:ring-success/20'
                                                    : 'bg-slate-50 border-slate-200 text-slate-600 focus:ring-primary-muted'
                                                    }`}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Short Answer */}
                            {question.question_type === 'short' && (
                                <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-4">
                                    <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Expected Answer</div>
                                    <textarea
                                        value={question.expected_answer || ''}
                                        onChange={(e) => handleQuestionChange(index, 'expected_answer', e.target.value)}
                                        className="w-full text-slate-600 font-medium bg-white border border-slate-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-primary-muted resize-none"
                                        rows={3}
                                    />
                                </div>
                            )}

                            {/* Explanation */}
                            <div className="text-sm">
                                <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Explanation (Optional)</div>
                                <textarea
                                    value={question.explanation || ''}
                                    onChange={(e) => handleQuestionChange(index, 'explanation', e.target.value)}
                                    placeholder="Add an explanation..."
                                    className="w-full text-slate-500 bg-slate-50 px-4 py-3 rounded-lg border border-slate-100 outline-none focus:ring-2 focus:ring-primary-muted resize-none"
                                    rows={2}
                                />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Add Question Buttons */}
                <div className="flex items-center gap-4 justify-center">
                    <button
                        onClick={() => handleAddQuestion('mcq')}
                        className="px-6 py-3 rounded-xl border-2 border-dashed border-primary/30 bg-primary-muted text-primary font-bold hover:bg-primary hover:text-white transition-all flex items-center gap-2"
                    >
                        <Plus size={18} />
                        Add Multiple Choice
                    </button>
                    <button
                        onClick={() => handleAddQuestion('short')}
                        className="px-6 py-3 rounded-xl border-2 border-dashed border-amber-400/30 bg-amber-50 text-amber-600 font-bold hover:bg-amber-400 hover:text-white transition-all flex items-center gap-2"
                    >
                        <Plus size={18} />
                        Add Short Answer
                    </button>
                </div>
            </div>
        </main>
    );
}
