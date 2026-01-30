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

interface MCQQuestion {
    question: string;
    options: string[];
    correct_answer: string;
    explanation: string;
    question_type: 'mcq';
}

interface ShortQuestion {
    question: string;
    expected_answer: string;
    key_points: string[];
    difficulty: string;
    question_type: 'short';
}

type MixedQuestion = MCQQuestion | ShortQuestion;

interface ValidationResult {
    is_correct: boolean;
    score: number;
    feedback: string;
    missing_points: string[];
    correct_points: string[];
}

export default function MixedQuiz({
    questions,
    quizId,
    onFinished,
    onReset,
    onTryAnotherType
}: {
    questions: MixedQuestion[],
    quizId: string,
    onFinished: (score: number, total: number) => void,
    onReset: () => void,
    onTryAnotherType: () => void
}) {
    const router = useRouter();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [userAnswer, setUserAnswer] = useState('');
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);
    const [isFinished, setIsFinished] = useState(false);
    const [showReview, setShowReview] = useState(false);
    const [userResponses, setUserResponses] = useState<any[]>([]);
    const [startTime] = useState<number>(Date.now());
    const [endTime, setEndTime] = useState<number | null>(null);
    const [elapsedTime, setElapsedTime] = useState<number>(0);
    const [isValidating, setIsValidating] = useState(false);
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

    useEffect(() => {
        if (!isFinished) {
            const timer = setInterval(() => {
                setElapsedTime(Date.now() - startTime);
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [isFinished, startTime]);

    const currentQuestion = questions[currentIndex];
    const isMCQ = currentQuestion?.question_type === 'mcq';

    const formatTime = (ms: number) => {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    const validateShortAnswer = async () => {
        if (!userAnswer.trim()) return;

        setIsValidating(true);
        const shortQ = currentQuestion as ShortQuestion;

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/validate-short-answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: shortQ.question,
                    expected_answer: shortQ.expected_answer,
                    key_points: shortQ.key_points,
                    user_answer: userAnswer
                })
            });

            const result = await response.json();
            setValidationResult(result);
            setShowResult(true);

            // Score is 0-100, so 70+ is passing
            if (result.score >= 70) {
                setScore(prev => prev + 1);
            }
        } catch (error) {
            console.error('Validation failed:', error);
            setValidationResult({
                is_correct: false,
                score: 0,
                feedback: 'Failed to validate answer. Please try again.',
                missing_points: [],
                correct_points: []
            });
            setShowResult(true);
        } finally {
            setIsValidating(false);
        }
    };

    const handleMCQConfirm = () => {
        if (isMCQ && selectedOption) {
            const mcqQ = currentQuestion as MCQQuestion;
            if (selectedOption === mcqQ.correct_answer) {
                setScore(prev => prev + 1);
            }
            setShowResult(true);
        }
    };

    const handleNext = () => {
        // Store the user's response for review
        const response = isMCQ
            ? { type: 'mcq', answer: selectedOption, question: currentQuestion }
            : { type: 'short', answer: userAnswer, validation: validationResult, question: currentQuestion };

        setUserResponses(prev => [...prev, response]);

        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
            setSelectedOption(null);
            setUserAnswer('');
            setShowResult(false);
            setValidationResult(null);
        } else {
            setEndTime(Date.now());
            setIsFinished(true);
            onFinished(score, questions.length);
        }
    };

    const getScoreColor = (score: number) => {
        // Score is 0-100 scale
        if (score >= 80) return 'text-success';
        if (score >= 50) return 'text-amber-500';
        return 'text-error';
    };

    if (isFinished) {
        const timeTaken = endTime && startTime ? endTime - startTime : 0;
        return (
            <div className="max-w-4xl mx-auto py-8 md:py-12 animate-fade-in text-center px-4">
                <div className="mb-6 md:mb-8 flex justify-center">
                    <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] bg-gradient-to-br from-blue-100 to-amber-100 text-primary">
                        <Award size={56} className="md:w-16 md:h-16 lg:w-20 lg:h-20" />
                    </div>
                </div>
                <h2 className="text-3xl md:text-5xl lg:text-6xl font-extrabold mb-4 text-primary tracking-tight">Mixed Session Complete</h2>
                <p className="text-lg md:text-xl text-slate-500 mb-8 md:mb-12 font-medium">
                    Great work! You scored <span className="text-primary font-bold">{score} / {questions.length}</span> across both formats.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6 mb-12 md:mb-16">
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Accuracy</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">{Math.round((score / questions.length) * 100)}%</div>
                    </div>
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Duration</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">{formatTime(timeTaken)}</div>
                    </div>
                    <div className="premium-card p-6 md:p-8 bg-white/60">
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Format</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">Mixed</div>
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 md:gap-6 justify-center max-w-2xl mx-auto">
                    <button
                        onClick={() => window.location.reload()}
                        className="flex-1 px-8 py-4 rounded-2xl bg-primary text-white font-bold hover:bg-primary-light shadow-xl transition-all flex items-center justify-center gap-3 active:scale-95"
                    >
                        <RotateCcw size={20} /> Try Again
                    </button>
                    {!showReview && (
                        <button
                            onClick={() => setShowReview(true)}
                            className="flex-1 px-8 py-4 rounded-2xl border-2 border-primary/10 text-primary font-bold hover:bg-white transition-all active:scale-95"
                        >
                            Detailed Review
                        </button>
                    )}
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

                {showReview && (
                    <div className="mt-12 md:mt-16 text-left space-y-6 md:space-y-8 pb-20">
                        <div className="flex items-center gap-3 mb-6 md:mb-8">
                            <div className="h-8 md:h-10 w-1 px-1 bg-accent rounded-full"></div>
                            <h3 className="text-xl md:text-2xl font-black text-primary">In-Depth Review</h3>
                        </div>
                        {userResponses.map((resp, idx) => (
                            <div key={idx} className="premium-card p-6 md:p-8 bg-white/60">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${resp.type === 'mcq'
                                        ? resp.answer === (resp.question as MCQQuestion).correct_answer ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                                        : resp.validation?.score >= 70 ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                                        }`}>
                                        {idx + 1}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${resp.type === 'mcq' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                                                }`}>
                                                {resp.type === 'mcq' ? 'MCQ' : 'Short Answer'}
                                            </span>
                                        </div>
                                        <h4 className="text-lg md:text-xl font-bold text-primary leading-tight">{resp.question.question}</h4>
                                    </div>
                                </div>

                                {resp.type === 'mcq' ? (
                                    <>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                                            {(resp.question as MCQQuestion).options.map((opt: string, oIdx: number) => (
                                                <div
                                                    key={oIdx}
                                                    className={`p-4 rounded-xl border text-sm font-medium ${opt === (resp.question as MCQQuestion).correct_answer
                                                        ? 'border-success bg-success/5 text-success'
                                                        : opt === resp.answer
                                                            ? 'border-error bg-error/5 text-error'
                                                            : 'border-slate-100 bg-slate-50 opacity-50'
                                                        }`}
                                                >
                                                    <span className="opacity-60 mr-2">{String.fromCharCode(65 + oIdx)}.</span> {opt}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
                                            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">
                                                <Lightbulb size={14} /> Explanation
                                            </div>
                                            <p className="text-slate-600 text-sm leading-relaxed">{(resp.question as MCQQuestion).explanation}</p>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="mb-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
                                            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Your Answer</div>
                                            <p className="text-slate-700">{resp.answer}</p>
                                        </div>
                                        <div className="mb-4 p-4 rounded-xl bg-success/5 border border-success/20">
                                            <div className="text-xs font-bold text-success uppercase tracking-widest mb-2">Expected Answer</div>
                                            <p className="text-slate-700">{(resp.question as ShortQuestion).expected_answer}</p>
                                        </div>
                                        {resp.validation && (
                                            <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
                                                <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">
                                                    <Sparkles size={14} /> AI Feedback
                                                </div>
                                                <p className="text-slate-600 text-sm leading-relaxed">{resp.validation.feedback}</p>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-6 md:py-10 px-4 md:px-6">
            {/* Progress Track */}
            <div className="mb-8 md:mb-12">
                <div className="flex justify-between items-end mb-4">
                    <div className="flex flex-col">
                        <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${isMCQ ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                                }`}>
                                {isMCQ ? 'Multiple Choice' : 'Short Answer'}
                            </span>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-base md:text-lg font-extrabold text-primary">Item {currentIndex + 1} <span className="text-slate-300 font-medium">/ {questions.length}</span></span>
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
                <div className="w-full h-2 md:h-3 bg-gradient-to-r from-blue-100 to-amber-100 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-amber-500 transition-all duration-700"
                        style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                    ></div>
                </div>
            </div>

            {/* Question Canvas */}
            <div className="premium-card p-6 md:p-10 lg:p-16 mb-8 md:mb-10 shadow-lg border-primary-muted/50 animate-fade-in bg-white/80">
                <h2 className="text-xl md:text-3xl lg:text-4xl font-extrabold mb-8 md:mb-12 text-primary leading-[1.2] tracking-tight">
                    {currentQuestion.question}
                </h2>

                {isMCQ ? (
                    /* MCQ Options */
                    <div className="grid grid-cols-1 gap-3 md:gap-5 mb-8 md:mb-12">
                        {(currentQuestion as MCQQuestion).options.map((option, idx) => (
                            <button
                                key={idx}
                                onClick={() => !showResult && setSelectedOption(option)}
                                className={`p-4 md:p-6 rounded-xl md:rounded-2xl border-2 text-left transition-all flex items-center justify-between group
                                    ${selectedOption === option
                                        ? 'border-primary bg-primary/5 shadow-inner'
                                        : 'border-card-border hover:border-primary/20 hover:bg-primary-muted'}
                                    ${showResult && option === (currentQuestion as MCQQuestion).correct_answer ? 'border-success bg-success/5 text-success' : ''}
                                    ${showResult && selectedOption === option && option !== (currentQuestion as MCQQuestion).correct_answer ? 'border-error bg-error/5 text-error' : ''}
                                `}
                                disabled={showResult}
                            >
                                <div className="flex items-center gap-4 md:gap-6">
                                    <div className={`w-7 h-7 md:w-8 md:h-8 rounded-lg flex items-center justify-center text-xs md:text-sm font-bold border-2 transition-colors
                                        ${selectedOption === option ? 'bg-primary border-primary text-white' : 'border-card-border text-slate-400 group-hover:border-primary/20'}
                                        ${showResult && option === (currentQuestion as MCQQuestion).correct_answer ? 'bg-success border-success text-white' : ''}
                                        ${showResult && selectedOption === option && option !== (currentQuestion as MCQQuestion).correct_answer ? 'bg-error border-error text-white' : ''}
                                    `}>
                                        {String.fromCharCode(65 + idx)}
                                    </div>
                                    <span className="text-base md:text-lg font-semibold pr-4">{option}</span>
                                </div>
                                {showResult && option === (currentQuestion as MCQQuestion).correct_answer && <CheckIcon size={20} className="text-success flex-shrink-0" />}
                                {showResult && selectedOption === option && option !== (currentQuestion as MCQQuestion).correct_answer && <XCircle size={20} className="text-error flex-shrink-0" />}
                            </button>
                        ))}
                    </div>
                ) : (
                    /* Short Answer Input */
                    <div className="mb-8 md:mb-12">
                        <div className="relative">
                            <textarea
                                value={userAnswer}
                                onChange={(e) => setUserAnswer(e.target.value)}
                                placeholder="Type your answer here..."
                                className="w-full p-6 rounded-2xl border-2 border-card-border focus:border-primary focus:ring-4 focus:ring-primary-muted transition-all outline-none text-lg font-medium resize-none min-h-[150px]"
                                disabled={showResult || isValidating}
                            />
                        </div>

                        {/* Key Points Hint */}
                        <div className="mt-4 p-4 rounded-xl bg-amber-50 border border-amber-200">
                            <div className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-2">Key Points to Cover</div>
                            <div className="flex flex-wrap gap-2">
                                {(currentQuestion as ShortQuestion).key_points.map((point, idx) => (
                                    <span key={idx} className="px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-sm font-medium">
                                        {point}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Validation Result for Short Answer */}
                {showResult && !isMCQ && validationResult && (
                    <div className={`p-6 md:p-8 rounded-2xl md:rounded-3xl mb-8 md:mb-10 animate-fade-in ${validationResult.score >= 70 ? 'bg-success/10 border border-success/20' : 'bg-amber-50 border border-amber-200'
                        }`}>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-extrabold text-sm uppercase tracking-widest flex items-center gap-2">
                                <Sparkles size={16} /> AI Assessment
                            </h4>
                            <span className={`text-2xl font-black ${getScoreColor(validationResult.score)}`}>
                                {Math.round(validationResult.score)}%
                            </span>
                        </div>
                        <p className="text-slate-700 text-base leading-relaxed mb-4">{validationResult.feedback}</p>

                        <div className="p-4 rounded-xl bg-white/80 border border-slate-200">
                            <div className="text-xs font-bold text-success uppercase tracking-widest mb-2">Expected Answer</div>
                            <p className="text-slate-600">{(currentQuestion as ShortQuestion).expected_answer}</p>
                        </div>
                    </div>
                )}

                {/* MCQ Explanation */}
                {showResult && isMCQ && (
                    <div className="p-6 md:p-8 rounded-2xl md:rounded-3xl bg-primary text-white mb-8 md:mb-10 animate-fade-in overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-6 md:p-8 opacity-10">
                            <Lightbulb size={120} />
                        </div>
                        <h4 className="font-extrabold text-sm uppercase tracking-widest mb-3 md:mb-4 flex items-center gap-2 opacity-70">
                            <Lightbulb size={16} /> Deep Insight
                        </h4>
                        <p className="text-base md:text-xl font-medium leading-relaxed">
                            {(currentQuestion as MCQQuestion).explanation}
                        </p>
                    </div>
                )}

                <div className="flex justify-end">
                    {!showResult ? (
                        isMCQ ? (
                            <button
                                onClick={handleMCQConfirm}
                                disabled={!selectedOption}
                                className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-primary text-white font-extrabold disabled:opacity-30 disabled:grayscale hover:bg-primary-light transition-all shadow-xl active:scale-95"
                            >
                                Confirm Selection
                            </button>
                        ) : (
                            <button
                                onClick={validateShortAnswer}
                                disabled={!userAnswer.trim() || isValidating}
                                className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-amber-500 text-white font-extrabold disabled:opacity-30 disabled:grayscale hover:bg-amber-600 transition-all shadow-xl active:scale-95 flex items-center justify-center gap-2"
                            >
                                {isValidating ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" /> Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Send size={18} /> Submit Answer
                                    </>
                                )}
                            </button>
                        )
                    ) : (
                        <button
                            onClick={handleNext}
                            className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-accent text-white font-extrabold hover:bg-accent-light transition-all shadow-xl flex items-center justify-center gap-2 md:gap-3 active:scale-95"
                        >
                            {currentIndex < questions.length - 1 ? 'Continue' : 'Finish Session'} <ArrowRight size={22} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
