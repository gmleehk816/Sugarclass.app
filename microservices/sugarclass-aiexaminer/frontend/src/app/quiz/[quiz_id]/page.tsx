'use client';

import { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import QuizInterface from '@/components/QuizInterface';
import ShortAnswerQuiz from '@/components/ShortAnswerQuiz';
import MixedQuiz from '@/components/MixedQuiz';
import { Sparkles } from 'lucide-react';

function QuizReplayContent() {
    const params = useParams();
    const router = useRouter();
    const quiz_id = params.quiz_id as string;

    const [quizData, setQuizData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (quiz_id) {
            fetchQuiz();
        }
    }, [quiz_id]);

    const fetchQuiz = async () => {
        try {
            setIsLoading(true);
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/${quiz_id}`);

            if (!response.ok) {
                throw new Error('Quiz not found');
            }

            const data = await response.json();

            // Determine question type from the questions structure
            // Check if questions have individual question_type fields (mixed mode)
            const hasMixedTypes = data.questions.some((q: any) => q.question_type === 'mcq') &&
                data.questions.some((q: any) => q.question_type === 'short');

            let questionType: 'mcq' | 'short' | 'mixed';
            if (hasMixedTypes) {
                questionType = 'mixed';
            } else if (data.questions[0]?.question_type === 'short' || !data.questions[0]?.options) {
                questionType = 'short';
            } else {
                questionType = 'mcq';
            }

            setQuizData({
                ...data,
                question_type: questionType
            });
        } catch (error: any) {
            console.error('Failed to fetch quiz:', error);
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuizFinished = async (score: number, total: number) => {
        const token = localStorage.getItem('sugarclass_token');
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    quiz_id: quiz_id,
                    score: score,
                    total: total,
                    user_id: 'default_user',
                    question_type: quizData?.question_type
                }),
            });
        } catch (error) {
            console.error('Failed to submit score:', error);
        }
    };

    return (
        <div className="container mx-auto px-6 py-12 md:px-10 lg:py-20">
            {isLoading ? (
                <div className="min-h-[60vh] flex flex-col items-center justify-center text-center animate-fade-in">
                    <div className="relative mb-12">
                        <div className="w-32 h-32 rounded-full border-[6px] border-primary-muted border-t-primary animate-spin"></div>
                        <div className="absolute inset-0 flex items-center justify-center text-primary">
                            <Sparkles className="animate-pulse" size={40} />
                        </div>
                    </div>
                    <h2 className="text-4xl font-extrabold mb-4 text-primary tracking-tight">Loading Quiz</h2>
                    <p className="text-xl text-slate-400 max-w-md mx-auto font-medium leading-relaxed">
                        Retrieving your practice assessment...
                    </p>
                </div>
            ) : error ? (
                <div className="min-h-[60vh] flex flex-col items-center justify-center text-center">
                    <div className="p-8 rounded-2xl bg-red-50 border border-red-200 max-w-md">
                        <h2 className="text-2xl font-black text-red-600 mb-4">Quiz Not Found</h2>
                        <p className="text-red-500 mb-6">{error}</p>
                        <button
                            onClick={() => router.push('/')}
                            className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95"
                        >
                            Back to Exercises
                        </button>
                    </div>
                </div>
            ) : quizData ? (
                <div className="animate-fade-in max-w-6xl mx-auto">
                    <div className="flex flex-col sm:flex-row items-center justify-between mb-12 gap-6">
                        <button
                            onClick={() => router.push('/')}
                            className="flex items-center gap-3 px-6 py-2.5 rounded-xl border border-card-border hover:bg-white text-slate-500 hover:text-primary font-bold transition-all active:scale-95 shadow-sm"
                        >
                            &larr; Back to Exercises
                        </button>
                        <div className="flex items-center gap-4">
                            <div className={`status-badge border ${quizData.question_type === 'mixed'
                                    ? 'bg-gradient-to-r from-blue-50 to-amber-50 text-purple-600 border-purple-200'
                                    : quizData.question_type === 'short'
                                        ? 'bg-amber-50 text-amber-600 border-amber-200'
                                        : 'bg-blue-50 text-blue-600 border-blue-200'
                                }`}>
                                {quizData.question_type === 'mixed' ? 'Mixed Format' : quizData.question_type === 'short' ? 'Short Answer Mode' : 'Multiple Choice Mode'}
                            </div>
                            <div className="status-badge bg-purple-50 text-purple-600 border border-purple-200">
                                Replay Mode
                            </div>
                        </div>
                    </div>

                    {quizData.question_type === 'mixed' ? (
                        <MixedQuiz
                            questions={quizData.questions}
                            quizId={quiz_id}
                            onFinished={handleQuizFinished}
                            onReset={() => router.push('/')}
                            onTryAnotherType={() => {/* Not applicable in replay mode */ }}
                        />
                    ) : quizData.question_type === 'short' ? (
                        <ShortAnswerQuiz
                            questions={quizData.questions}
                            quizId={quiz_id}
                            onFinished={handleQuizFinished}
                            onReset={() => router.push('/')}
                            onTryAnotherType={() => {/* Not applicable in replay mode */ }}
                        />
                    ) : (
                        <QuizInterface
                            questions={quizData.questions}
                            quizId={quiz_id}
                            onFinished={handleQuizFinished}
                            onReset={() => router.push('/')}
                            onTryAnotherType={() => {/* Not applicable in replay mode */ }}
                        />
                    )}
                </div>
            ) : null}
        </div>
    );
}

export default function QuizReplayPage() {
    return (
        <main className="min-h-screen bg-background relative overflow-hidden">
            {/* Decorative Blobs */}
            <div className="fixed top-[-100px] right-[-100px] w-[600px] h-[600px] bg-accent-muted/30 rounded-full blur-[120px] -z-10 pointer-events-none" />
            <div className="fixed bottom-[-100px] left-[-100px] w-[500px] h-[500px] bg-primary-muted/20 rounded-full blur-[120px] -z-10 pointer-events-none" />

            <Navbar />

            <Suspense fallback={<div className="min-h-screen flex items-center justify-center font-black text-primary animate-pulse">Loading Quiz...</div>}>
                <QuizReplayContent />
            </Suspense>
        </main>
    );
}
