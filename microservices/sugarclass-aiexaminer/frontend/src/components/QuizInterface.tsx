'use client';

import { useState } from 'react';
import { CheckCircle2, XCircle, ArrowRight, RotateCcw, Award, Lightbulb, Check } from 'lucide-react';

interface Question {
    question: string;
    options: string[];
    correct_answer: string;
    explanation: string;
}

export default function QuizInterface({
    questions,
    quizId,
    onFinished
}: {
    questions: Question[],
    quizId: string,
    onFinished: (score: number, total: number) => void
}) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [showResult, setShowResult] = useState(false);
    const [score, setScore] = useState(0);
    const [isFinished, setIsFinished] = useState(false);

    const currentQuestion = questions[currentIndex];

    const handleNext = () => {
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
            setIsFinished(true);
            onFinished(finalScore, questions.length);
        }
    };

    if (isFinished) {
        return (
            <div className="max-w-3xl mx-auto py-12 animate-fade-in text-center">
                <div className="mb-8 flex justify-center">
                    <div className="p-8 rounded-[40px] bg-accent/10 text-accent">
                        <Award size={72} />
                    </div>
                </div>
                <h2 className="text-5xl font-extrabold mb-4 text-primary tracking-tight">Practice Complete</h2>
                <p className="text-xl text-slate-500 mb-12 font-medium">
                    Excellent progress! You achieved <span className="text-primary font-bold">{score} / {questions.length}</span> correct answers.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16 px-4">
                    <div className="premium-card p-8 bg-white/60">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Accuracy</div>
                        <div className="text-4xl font-black text-primary">{Math.round((score / questions.length) * 100)}%</div>
                    </div>
                    <div className="premium-card p-8 bg-white/60">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Duration</div>
                        <div className="text-4xl font-black text-primary">04:32</div>
                    </div>
                    <div className="premium-card p-8 bg-white/60">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Efficiency</div>
                        <div className="text-4xl font-black text-primary">High</div>
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-6 justify-center">
                    <button
                        onClick={() => window.location.reload()}
                        className="px-10 py-4 rounded-2xl bg-primary text-white font-bold hover:bg-primary-light shadow-xl transition-all flex items-center justify-center gap-3 active:scale-95"
                    >
                        <RotateCcw size={22} /> Repeat Exercise
                    </button>
                    <button className="px-10 py-4 rounded-2xl border-2 border-primary/10 text-primary font-bold hover:bg-white transition-all active:scale-95">
                        Detailed Review
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto py-10 px-4">
            {/* Progress Track */}
            <div className="mb-12">
                <div className="flex justify-between items-end mb-4">
                    <div className="flex flex-col">
                        <span className="text-xs font-bold text-accent uppercase tracking-widest mb-1">Knowledge Check</span>
                        <span className="text-lg font-extrabold text-primary">Item {currentIndex + 1} <span className="text-slate-300 font-medium">/ {questions.length}</span></span>
                    </div>
                    <span className="text-2xl font-black text-primary">{Math.round(((currentIndex + 1) / questions.length) * 100)}%</span>
                </div>
                <div className="w-full h-3 bg-primary-muted rounded-full overflow-hidden">
                    <div
                        className="h-full bg-primary transition-all duration-700 cubic-bezier(0.16, 1, 0.3, 1)"
                        style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
                    ></div>
                </div>
            </div>

            {/* Question Canvas */}
            <div className="premium-card p-10 md:p-16 mb-10 shadow-lg border-primary-muted/50 animate-fade-in">
                <h2 className="text-3xl md:text-4xl font-extrabold mb-12 text-primary leading-[1.2] tracking-tight">
                    {currentQuestion.question}
                </h2>

                <div className="grid grid-cols-1 gap-5 mb-12">
                    {currentQuestion.options.map((option, idx) => (
                        <button
                            key={idx}
                            onClick={() => !showResult && setSelectedOption(option)}
                            className={`p-6 rounded-2xl border-2 text-left transition-all flex items-center justify-between group
                ${selectedOption === option
                                    ? 'border-primary bg-primary/5 shadow-inner'
                                    : 'border-card-border hover:border-primary/20 hover:bg-primary-muted'}
                ${showResult && option === currentQuestion.correct_answer ? 'border-success bg-success/5 text-success' : ''}
                ${showResult && selectedOption === option && option !== currentQuestion.correct_answer ? 'border-error bg-error/5 text-error' : ''}
              `}
                            disabled={showResult}
                        >
                            <div className="flex items-center gap-6">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold border-2 transition-colors
                    ${selectedOption === option ? 'bg-primary border-primary text-white' : 'border-card-border text-slate-400 group-hover:border-primary/20'}
                    ${showResult && option === currentQuestion.correct_answer ? 'bg-success border-success text-white' : ''}
                    ${showResult && selectedOption === option && option !== currentQuestion.correct_answer ? 'bg-error border-error text-white' : ''}
                `}>
                                    {String.fromCharCode(65 + idx)}
                                </div>
                                <span className="text-lg font-semibold">{option}</span>
                            </div>
                            {showResult && option === currentQuestion.correct_answer && <Check size={24} className="text-success" />}
                            {showResult && selectedOption === option && option !== currentQuestion.correct_answer && <XCircle size={24} className="text-error" />}
                        </button>
                    ))}
                </div>

                {showResult && (
                    <div className="p-8 rounded-3xl bg-primary text-white mb-10 animate-fade-in overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-8 opacity-10">
                            <Lightbulb size={120} />
                        </div>
                        <h4 className="font-extrabold text-sm uppercase tracking-[0.2em] mb-4 flex items-center gap-3 opacity-70">
                            <Lightbulb size={18} /> Deep Insight
                        </h4>
                        <p className="text-xl font-medium leading-relaxed">
                            {currentQuestion.explanation}
                        </p>
                    </div>
                )}

                <div className="flex justify-end">
                    {!showResult ? (
                        <button
                            onClick={() => setShowResult(true)}
                            disabled={!selectedOption}
                            className="px-12 py-4 rounded-xl bg-primary text-white font-extrabold disabled:opacity-30 disabled:grayscale hover:bg-primary-light transition-all shadow-xl active:scale-95"
                        >
                            Confirm Selection
                        </button>
                    ) : (
                        <button
                            onClick={handleNext}
                            className="px-12 py-4 rounded-xl bg-accent text-white font-extrabold hover:bg-accent-light transition-all shadow-xl flex items-center gap-3 active:scale-95"
                        >
                            {currentIndex < questions.length - 1 ? 'Continue' : 'Finish Session'} <ArrowRight size={22} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
