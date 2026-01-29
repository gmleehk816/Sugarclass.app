'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    CheckCircle2,
    XCircle,
    ArrowRight,
    RotateCcw,
    Award,
    Lightbulb,
    Check as CheckIcon,
    Clock,
    Loader2,
    MessageSquare,
    Sparkles,
    AlertCircle,
    Send,
    CheckSquare,
    Edit3
} from 'lucide-react';

interface ShortQuestion {
    question: string;
    expected_answer: string;
    key_points: string[];
    difficulty: string;
}

interface ValidationResult {
    is_correct: boolean;
    score: number; // 0-100
    feedback: string;
    missing_points: string[];
    correct_points: string[];
}

export default function ShortAnswerQuiz({
    questions,
    quizId,
    onFinished,
    onReset,
    onTryAnotherType
}: {
    questions: ShortQuestion[],
    quizId: string,
    onFinished: (score: number, total: number) => void,
    onReset: () => void,
    onTryAnotherType: () => void
}) {
    const router = useRouter();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [isValidating, setIsValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [answers, setAnswers] = useState<{ answer: string; result: ValidationResult }[]>([]);
    const [isFinished, setIsFinished] = useState(false);
    const [startTime] = useState<number>(Date.now());
    const [endTime, setEndTime] = useState<number | null>(null);
    const [elapsedTime, setElapsedTime] = useState<number>(0);

    useEffect(() => {
        if (!isFinished) {
            const timer = setInterval(() => {
                setElapsedTime(Date.now() - startTime);
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [isFinished, startTime]);

    const currentQuestion = questions[currentIndex];

    const formatTime = (ms: number) => {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    const validateAnswer = async () => {
        if (!userAnswer.trim()) return;

        setIsValidating(true);
        try {
            const token = localStorage.getItem('sugarclass_token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/validate-short-answer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    question: currentQuestion.question,
                    expected_answer: currentQuestion.expected_answer,
                    key_points: currentQuestion.key_points,
                    user_answer: userAnswer
                })
            });

            const result = await response.json();
            setValidationResult(result);
            setAnswers(prev => [...prev, { answer: userAnswer, result }]);
        } catch (error) {
            console.error('Validation failed:', error);
            // Fallback basic validation
            setValidationResult({
                is_correct: false,
                score: 0,
                feedback: 'Unable to validate answer. Please try again.',
                missing_points: [],
                correct_points: []
            });
        } finally {
            setIsValidating(false);
        }
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
            setUserAnswer('');
            setValidationResult(null);
        } else {
            setEndTime(Date.now());
            setIsFinished(true);
            const totalScore = answers.reduce((sum, a) => sum + a.result.score, 0);
            const avgScore = Math.round(totalScore / answers.length);
            const correctCount = answers.filter(a => a.result.is_correct).length;
            onFinished(correctCount, questions.length);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-success bg-success/10 border-success';
        if (score >= 50) return 'text-amber-600 bg-amber-50 border-amber-400';
        return 'text-error bg-error/10 border-error';
    };

    const getScoreLabel = (score: number) => {
        if (score >= 90) return 'Excellent!';
        if (score >= 80) return 'Great Job!';
        if (score >= 60) return 'Good Effort';
        if (score >= 40) return 'Needs Work';
        return 'Keep Trying';
    };

    if (isFinished) {
        const timeTaken = endTime && startTime ? endTime - startTime : 0;
        const totalScore = answers.reduce((sum, a) => sum + a.result.score, 0);
        const avgScore = Math.round(totalScore / answers.length);
        const correctCount = answers.filter(a => a.result.is_correct).length;

        return (
            <div className="max-w-4xl mx-auto py-8 md:py-12 animate-fade-in text-center px-4">
                <div className="mb-6 md:mb-8 flex justify-center">
                    <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] bg-accent/10 text-accent">
                        <Award size={56} className="md:w-16 md:h-16 lg:w-20 lg:h-20" />
                    </div>
                </div>
                <h2 className="text-3xl md:text-5xl font-extrabold mb-4 text-primary tracking-tight">Short Answer Complete</h2>
                <p className="text-lg md:text-xl text-slate-500 mb-8 md:mb-12 font-medium">
                    Great effort! You correctly answered <span className="text-primary font-bold">{correctCount} / {questions.length}</span> questions.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 mb-12 md:mb-16">
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Avg Score</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">{avgScore}%</div>
                    </div>
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Duration</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">{formatTime(timeTaken)}</div>
                    </div>
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Performance</div>
                        <div className="text-2xl md:text-3xl font-black text-primary">{getScoreLabel(avgScore)}</div>
                    </div>
                </div>

                {/* Answer Review */}
                <div className="text-left mb-12 md:mb-16">
                    <h3 className="text-xl md:text-2xl font-black text-primary mb-6 flex items-center gap-3">
                        <div className="h-8 w-1 bg-accent rounded-full"></div>
                        Detailed Review
                    </h3>
                    <div className="space-y-4 md:space-y-6">
                        {answers.map((a, idx) => (
                            <div key={idx} className={`premium-card p-6 border-l-4 transition-all hover:scale-[1.01] ${getScoreColor(a.result.score)}`}>
                                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                                    <p className="font-bold text-primary text-base md:text-lg">{questions[idx].question}</p>
                                    <span className={`inline-flex items-center justify-center px-4 py-1 rounded-full text-xs font-bold ${getScoreColor(a.result.score)}`}>
                                        {a.result.score}% Match
                                    </span>
                                </div>
                                <div className="space-y-3">
                                    <p className="text-slate-600 text-sm italic bg-white/40 p-3 rounded-lg border border-white/60">
                                        <span className="font-bold text-primary not-italic">Your Response:</span> {a.answer}
                                    </p>
                                    <p className="text-slate-500 text-sm leading-relaxed">{a.result.feedback}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 md:gap-6 justify-center max-w-2xl mx-auto">
                    <button
                        onClick={() => window.location.reload()}
                        className="flex-1 px-8 py-4 rounded-2xl bg-primary text-white font-bold hover:bg-primary-light shadow-xl transition-all flex items-center justify-center gap-3 active:scale-95"
                    >
                        <RotateCcw size={20} /> Try Again
                    </button>
                    <button
                        onClick={onTryAnotherType}
                        className="flex-1 px-8 py-4 rounded-2xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-xl transition-all active:scale-95 flex items-center justify-center gap-3"
                    >
                        <CheckSquare size={20} /> Try Another Format
                    </button>
                    <button
                        onClick={() => router.push(`/quiz/${quizId}/edit`)}
                        className="flex-1 px-8 py-4 rounded-2xl border-2 border-accent/20 bg-white text-accent font-bold hover:bg-accent-muted transition-all active:scale-95 flex items-center justify-center gap-2"
                    >
                        <Edit3 size={20} /> Edit Questions
                    </button>
                    <button
                        onClick={onReset}
                        className="flex-1 px-8 py-4 rounded-2xl bg-accent text-white font-bold hover:bg-accent-light shadow-xl transition-all active:scale-95"
                    >
                        New Quiz
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-6 md:py-10 px-4 md:px-6">
            {/* Progress Track */}
            <div className="mb-8 md:mb-12">
                <div className="flex justify-between items-end mb-4">
                    <div className="flex flex-col">
                        <span className="text-[10px] md:text-xs font-bold text-accent uppercase tracking-widest mb-1 flex items-center gap-2">
                            <MessageSquare size={14} /> Short Answer Question
                        </span>
                        <div className="flex items-center gap-4">
                            <span className="text-base md:text-lg font-extrabold text-primary">
                                Question {currentIndex + 1} <span className="text-slate-300 font-medium">/ {questions.length}</span>
                            </span>
                            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary/5 border border-primary/10 text-[10px] font-bold text-primary/60">
                                <Clock size={12} /> {formatTime(elapsedTime)}
                            </div>
                        </div>
                    </div>
                    <div className="flex flex-col items-end">
                        <span className="sm:hidden text-[10px] font-bold text-primary/40 mb-1">{formatTime(elapsedTime)}</span>
                        <span className="text-xl md:text-2xl font-black text-primary">{Math.round(((currentIndex + 1) / questions.length) * 100)}%</span>
                    </div>
                </div>
                <div className="w-full h-2 md:h-3 bg-primary-muted rounded-full overflow-hidden">
                    <div
                        className="h-full bg-primary transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1)"
                        style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                    ></div>
                </div>
            </div>

            {/* Question Canvas */}
            <div className="premium-card p-6 md:p-10 lg:p-16 mb-8 md:mb-10 shadow-lg border-primary-muted/50 animate-fade-in bg-white/80">
                {/* Difficulty Badge */}
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] md:text-xs font-bold uppercase tracking-wider mb-6
                    ${currentQuestion.difficulty === 'hard' ? 'bg-error/10 text-error' :
                        currentQuestion.difficulty === 'medium' ? 'bg-amber-50 text-amber-600' :
                            'bg-success/10 text-success'}`}>
                    <Sparkles size={12} />
                    {currentQuestion.difficulty} difficulty
                </div>

                <h2 className="text-xl md:text-3xl lg:text-4xl font-extrabold mb-8 md:mb-12 text-primary leading-[1.2] tracking-tight">
                    {currentQuestion.question}
                </h2>

                {/* Answer Input */}
                <div className="mb-8 overflow-hidden">
                    <label className="block text-[10px] md:text-xs font-bold text-slate-500 mb-3 uppercase tracking-wider">
                        Your Response
                    </label>
                    <textarea
                        value={userAnswer}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        disabled={validationResult !== null}
                        placeholder="Type your answer here... Be detailed and include key concepts."
                        className={`w-full p-4 md:p-6 rounded-xl md:rounded-2xl border-2 text-base md:text-lg transition-all resize-none min-h-[120px] md:min-h-[150px]
                            ${validationResult
                                ? validationResult.is_correct
                                    ? 'border-success bg-success/5'
                                    : 'border-amber-400 bg-amber-50'
                                : 'border-slate-200 focus:border-primary focus:ring-4 focus:ring-primary-muted'
                            }
                        `}
                    />
                </div>

                {/* AI Validation Result */}
                {validationResult && (
                    <div className="animate-fade-in space-y-6 mb-10">
                        {/* Score Card */}
                        <div className={`p-6 md:p-8 rounded-2xl md:rounded-3xl border-2 ${getScoreColor(validationResult.score)}`}>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3 md:gap-4">
                                    {validationResult.is_correct ? (
                                        <CheckCircle2 size={28} className="text-success md:w-8 md:h-8" />
                                    ) : (
                                        <AlertCircle size={28} className="text-amber-600 md:w-8 md:h-8" />
                                    )}
                                    <div>
                                        <h3 className="text-lg md:text-xl font-bold">{getScoreLabel(validationResult.score)}</h3>
                                        <p className="text-[10px] md:text-xs opacity-80 uppercase font-bold tracking-widest">AI Evaluation</p>
                                    </div>
                                </div>
                                <div className="text-3xl md:text-4xl font-black">{validationResult.score}%</div>
                            </div>
                            <p className="text-base md:text-lg leading-relaxed">{validationResult.feedback}</p>
                        </div>

                        {/* Detailed Feedback */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                            {validationResult.correct_points.length > 0 && (
                                <div className="p-5 md:p-6 rounded-2xl bg-success/5 border border-success/20">
                                    <h4 className="font-bold text-success mb-3 flex items-center gap-2 text-sm md:text-base">
                                        <CheckCircle2 size={16} /> Key Strengths
                                    </h4>
                                    <ul className="space-y-2">
                                        {validationResult.correct_points.map((point, i) => (
                                            <li key={i} className="text-xs md:text-sm text-slate-600 flex items-start gap-2">
                                                <CheckIcon size={14} className="text-success mt-0.5 flex-shrink-0" />
                                                {point}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {validationResult.missing_points.length > 0 && (
                                <div className="p-5 md:p-6 rounded-2xl bg-amber-50 border border-amber-200">
                                    <h4 className="font-bold text-amber-700 mb-3 flex items-center gap-2 text-sm md:text-base">
                                        <Lightbulb size={16} /> Growth Areas
                                    </h4>
                                    <ul className="space-y-2">
                                        {validationResult.missing_points.map((point, i) => (
                                            <li key={i} className="text-xs md:text-sm text-slate-600 flex items-start gap-2">
                                                <ArrowRight size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
                                                {point}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        {/* Expected Answer */}
                        <div className="p-6 md:p-8 rounded-2xl md:rounded-3xl bg-primary text-white relative overflow-hidden shadow-xl">
                            <div className="absolute top-0 right-0 p-6 md:p-8 opacity-10">
                                <Lightbulb size={120} className="w-16 h-16 md:w-30 md:h-30" />
                            </div>
                            <h4 className="font-extrabold text-[10px] md:text-sm uppercase tracking-[0.2em] mb-3 flex items-center gap-3 opacity-70">
                                <Lightbulb size={16} /> Reference Answer
                            </h4>
                            <p className="text-base md:text-lg font-medium leading-relaxed relative z-10">
                                {currentQuestion.expected_answer}
                            </p>
                        </div>
                    </div>
                )}

                <div className="flex justify-end">
                    {!validationResult ? (
                        <button
                            onClick={validateAnswer}
                            disabled={!userAnswer.trim() || isValidating}
                            className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-primary text-white font-extrabold disabled:opacity-30 disabled:grayscale hover:bg-primary-light transition-all shadow-xl active:scale-95 flex items-center justify-center gap-3"
                        >
                            {isValidating ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    AI Analyzing...
                                </>
                            ) : (
                                <>
                                    <Send size={20} />
                                    Submit Answer
                                </>
                            )}
                        </button>
                    ) : (
                        <button
                            onClick={handleNext}
                            className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-accent text-white font-extrabold hover:bg-accent-light transition-all shadow-xl flex items-center justify-center gap-3 active:scale-95"
                        >
                            {currentIndex < questions.length - 1 ? 'Next Question' : 'Finish Session'} <ArrowRight size={22} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
