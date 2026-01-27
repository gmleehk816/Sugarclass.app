'use client';

import React, { useState, useEffect } from 'react';
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
    Send
} from 'lucide-react';

interface Question {
    question: string;
    options: string[];
    correct_answer: string;
    explanation: string;
}

export default function QuizInterface({
    questions,
    quizId,
    onFinished,
    onReset
}: {
    questions: Question[],
    quizId: string,
    onFinished: (score: number, total: number) => void,
    onReset: () => void
}) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);
    const [isFinished, setIsFinished] = useState(false);
    const [showReview, setShowReview] = useState(false);
    const [userSelections, setUserSelections] = useState<string[]>([]);
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

    const handleNext = () => {
        const finalSelections = [...userSelections, selectedOption || ''];
        setUserSelections(finalSelections);

        let finalScore = score;
        if (selectedOption === currentQuestion.correct_answer) {
            finalScore = score + 1;
            setScore(finalScore);
        }

        if (currentIndex < questions.length - 1) {
            setCurrentIndex(currentIndex + 1);
            setSelectedOption(null);
            setShowResult(false);
        } else {
            setEndTime(Date.now());
            setIsFinished(true);
            onFinished(finalScore, questions.length);
        }
    };

    if (isFinished) {
        const timeTaken = endTime && startTime ? endTime - startTime : 0;
        return (
            <div className="max-w-4xl mx-auto py-8 md:py-12 animate-fade-in text-center px-4">
                <div className="mb-6 md:mb-8 flex justify-center">
                    <div className="p-6 md:p-8 rounded-[32px] md:rounded-[40px] bg-accent/10 text-accent">
                        <Award size={56} className="md:w-16 md:h-16 lg:w-20 lg:h-20" />
                    </div>
                </div>
                <h2 className="text-3xl md:text-5xl lg:text-6xl font-extrabold mb-4 text-primary tracking-tight">Practice Complete</h2>
                <p className="text-lg md:text-xl text-slate-500 mb-8 md:mb-12 font-medium">
                    Excellent progress! You achieved <span className="text-primary font-bold">{score} / {questions.length}</span> correct answers.
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
                        <div className="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Pace</div>
                        <div className="text-3xl md:text-4xl font-black text-primary">{Math.round((timeTaken / 1000) / questions.length)}s/q</div>
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
                        {questions.map((q, qIdx) => (
                            <div key={qIdx} className="premium-card p-6 md:p-8 bg-white/60">
                                <div className="flex items-start gap-4 mb-6">
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${userSelections[qIdx] === q.correct_answer ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>
                                        {qIdx + 1}
                                    </div>
                                    <h4 className="text-lg md:text-xl font-bold text-primary leading-tight">{q.question}</h4>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                                    {q.options.map((opt, oIdx) => (
                                        <div
                                            key={oIdx}
                                            className={`p-4 rounded-xl border text-sm font-medium ${opt === q.correct_answer
                                                ? 'border-success bg-success/5 text-success'
                                                : opt === userSelections[qIdx]
                                                    ? 'border-error bg-error/5 text-error'
                                                    : 'border-slate-100 bg-slate-50 opacity-50'
                                                }`}
                                        >
                                            <span className="opacity-60 mr-2">{String.fromCharCode(65 + oIdx)}.</span> {opt}
                                        </div>
                                    ))}
                                </div>
                                <div className="p-4 md:p-5 rounded-2xl bg-primary/5 border border-primary/10">
                                    <div className="flex items-center gap-2 text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-[0.1em] mb-2">
                                        <Lightbulb size={14} /> Explanation
                                    </div>
                                    <p className="text-slate-600 text-sm leading-relaxed">{q.explanation}</p>
                                </div>
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
                        <span className="text-[10px] md:text-xs font-bold text-accent uppercase tracking-widest mb-1">Knowledge Check</span>
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
                <div className="w-full h-2 md:h-3 bg-primary-muted rounded-full overflow-hidden">
                    <div
                        className="h-full bg-primary transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1)"
                        style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                    ></div>
                </div>
            </div>

            {/* Question Canvas */}
            <div className="premium-card p-6 md:p-10 lg:p-16 mb-8 md:mb-10 shadow-lg border-primary-muted/50 animate-fade-in bg-white/80">
                <h2 className="text-xl md:text-3xl lg:text-4xl font-extrabold mb-8 md:mb-12 text-primary leading-[1.2] tracking-tight">
                    {currentQuestion.question}
                </h2>

                <div className="grid grid-cols-1 gap-3 md:gap-5 mb-8 md:mb-12">
                    {currentQuestion.options.map((option, idx) => (
                        <button
                            key={idx}
                            onClick={() => !showResult && setSelectedOption(option)}
                            className={`p-4 md:p-6 rounded-xl md:rounded-2xl border-2 text-left transition-all flex items-center justify-between group
                ${selectedOption === option
                                    ? 'border-primary bg-primary/5 shadow-inner'
                                    : 'border-card-border hover:border-primary/20 hover:bg-primary-muted'}
                ${showResult && option === currentQuestion.correct_answer ? 'border-success bg-success/5 text-success' : ''}
                ${showResult && selectedOption === option && option !== currentQuestion.correct_answer ? 'border-error bg-error/5 text-error' : ''}
              `}
                            disabled={showResult}
                        >
                            <div className="flex items-center gap-4 md:gap-6">
                                <div className={`w-7 h-7 md:w-8 md:h-8 rounded-lg flex items-center justify-center text-xs md:text-sm font-bold border-2 transition-colors
                    ${selectedOption === option ? 'bg-primary border-primary text-white' : 'border-card-border text-slate-400 group-hover:border-primary/20'}
                    ${showResult && option === currentQuestion.correct_answer ? 'bg-success border-success text-white' : ''}
                    ${showResult && selectedOption === option && option !== currentQuestion.correct_answer ? 'bg-error border-error text-white' : ''}
                `}>
                                    {String.fromCharCode(65 + idx)}
                                </div>
                                <span className="text-base md:text-lg font-semibold pr-4">{option}</span>
                            </div>
                            {showResult && option === currentQuestion.correct_answer && <CheckIcon size={20} className="text-success flex-shrink-0" />}
                            {showResult && selectedOption === option && option !== currentQuestion.correct_answer && <XCircle size={20} className="text-error flex-shrink-0" />}
                        </button>
                    ))}
                </div>

                {showResult && (
                    <div className="p-6 md:p-8 rounded-2xl md:rounded-3xl bg-primary text-white mb-8 md:mb-10 animate-fade-in overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-6 md:p-8 opacity-10">
                            <Lightbulb size={120} className="w-16 h-16 md:w-30 md:h-30" />
                        </div>
                        <h4 className="font-extrabold text-[10px] md:text-sm uppercase tracking-[0.2em] mb-3 md:mb-4 flex items-center gap-2 md:gap-3 opacity-70">
                            <Lightbulb size={16} /> Deep Insight
                        </h4>
                        <p className="text-base md:text-xl font-medium leading-relaxed">
                            {currentQuestion.explanation}
                        </p>
                    </div>
                )}

                <div className="flex justify-end">
                    {!showResult ? (
                        <button
                            onClick={() => setShowResult(true)}
                            disabled={!selectedOption}
                            className="w-full sm:w-auto px-10 md:px-12 py-3.5 md:py-4 rounded-xl bg-primary text-white font-extrabold disabled:opacity-30 disabled:grayscale hover:bg-primary-light transition-all shadow-xl active:scale-95"
                        >
                            Confirm Selection
                        </button>
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
