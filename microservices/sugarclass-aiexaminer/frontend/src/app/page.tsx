'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import QuizInterface from '@/components/QuizInterface';
import ShortAnswerQuiz from '@/components/ShortAnswerQuiz';
import MixedQuiz from '@/components/MixedQuiz';
import PageSelector from '@/components/PageSelector';
import { Search, RotateCcw, Play, CheckCircle, Sparkles, Trophy, Zap, ArrowRight, Clock, Award, GraduationCap, History, BookOpen, Upload as UploadIcon, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';

interface PagePreview {
  page: number;
  title: string;
  preview: string;
  char_count: number;
  is_title_page: boolean;
}

interface UploadResponse {
  id: string;
  filename: string;
  text_preview: string;
  full_text: string;
  total_pages: number;
  processed_pages: number[];
  requires_page_selection: boolean;
  max_pages_limit: number;
  page_previews: PagePreview[];
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const materialId = searchParams.get('mid');
  const sessionId = searchParams.get('sid');

  const [quizData, setQuizData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questionType, setQuestionType] = useState<'mcq' | 'short' | 'mixed'>('mixed');
  const [numQuestions, setNumQuestions] = useState(15); // Default to 15 questions

  // Page selection and configuration state
  const [pendingUpload, setPendingUpload] = useState<UploadResponse | null>(null);
  const [currentMaterial, setCurrentMaterial] = useState<UploadResponse | null>(null);
  const [showPageSelector, setShowPageSelector] = useState(false);

  // State for Exercises List
  const [quizzes, setQuizzes] = useState<any[]>([]);
  const [isLoadingQuizzes, setIsLoadingQuizzes] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 9;

  useEffect(() => {
    if (materialId) {
      handleGenerateFromMaterial(materialId);
    } else if (sessionId) {
      handleGenerateFromSession(sessionId);
    }
    fetchQuizzes();
  }, [materialId, sessionId]);

  const fetchQuizzes = async () => {
    try {
      setIsLoadingQuizzes(true);
      const quizzesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/`);
      const quizzesData = await quizzesResponse.json();

      const progressResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/progress/`);
      const progressData = await progressResponse.json();

      const quizzesWithProgress = quizzesData.map((quiz: any) => {
        const progressEntries = progressData.history?.filter((p: any) => p.quiz_id === quiz.id) || [];
        const lastAttempt = progressEntries.length > 0 ? progressEntries[0] : null;

        return {
          ...quiz,
          attempts: progressEntries.length,
          lastScore: lastAttempt?.score,
          lastAccuracy: lastAttempt?.accuracy
        };
      });

      setQuizzes(quizzesWithProgress);
    } catch (error) {
      console.error('Failed to fetch quizzes:', error);
    } finally {
      setIsLoadingQuizzes(false);
    }
  };

  const filteredQuizzes = quizzes.filter(quiz =>
    quiz.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredQuizzes.length / ITEMS_PER_PAGE);
  const currentQuizzes = filteredQuizzes.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  const handleGenerateFromMaterial = async (id: string) => {
    setIsGenerating(true);
    setError(null);
    try {
      const token = localStorage.getItem('sugarclass_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/${id}/config`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!res.ok) {
        throw new Error("Material config not found");
      }

      const material = await res.json();
      const hasText = material.full_text && material.full_text.trim() !== '';
      const canSelectPages = material.requires_page_selection && material.total_pages > 0;

      if (!hasText && !canSelectPages) {
        throw new Error("This document appears to be empty or unreadable. Please try a different source.");
      }

      setPendingUpload(material);
      setShowPageSelector(true);
      setIsGenerating(false);
    } catch (error: any) {
      console.error('Quiz configuration failed:', error);
      setError(error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateFromSession = async (sid: string) => {
    setIsGenerating(true);
    setError(null);
    try {
      const token = localStorage.getItem('sugarclass_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/session/${sid}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!res.ok) throw new Error("Session not found");

      const data = await res.json();
      if (!data.materials || data.materials.length === 0) {
        throw new Error("No materials found in this session.");
      }

      // Combine text from all materials in the session
      const combinedText = data.materials.map((m: any) => m.extracted_text).join('\n\n');
      const firstMaterial = data.materials[0];

      const virtualMaterial: UploadResponse = {
        id: `session-${sid}`,
        filename: `Session Bundle (${data.materials.length} files)`,
        text_preview: combinedText.substring(0, 500),
        full_text: combinedText,
        total_pages: data.materials.reduce((acc: number, m: any) => acc + (m.total_pages || 1), 0),
        processed_pages: [],
        requires_page_selection: false, // For bundles, we use combined text directly
        max_pages_limit: 20,
        page_previews: []
      };

      setPendingUpload(virtualMaterial);
      setShowPageSelector(true);
    } catch (error: any) {
      console.error('Session generation failed:', error);
      setError(error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTryAnotherType = () => {
    if (currentMaterial) {
      setPendingUpload(currentMaterial);
      setShowPageSelector(true);
      setQuizData(null);
    }
  };

  const handleDeleteQuiz = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this exercise? This action cannot be undone.')) return;

    try {
      const token = localStorage.getItem('sugarclass_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/${id}`, {
        method: 'DELETE',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      });

      if (!response.ok) throw new Error('Failed to delete quiz');

      // Refresh the quiz list
      fetchQuizzes();
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete exercise. Please try again.');
    }
  };

  const handlePageSelection = async (selectedPages: number[], selectedQuestionType: 'mcq' | 'short' | 'mixed', selectedNumQuestions: number) => {
    if (!pendingUpload) return;

    setShowPageSelector(false);
    setIsGenerating(true);
    setError(null);
    setQuestionType(selectedQuestionType);
    setNumQuestions(selectedNumQuestions);

    try {
      const token = localStorage.getItem('sugarclass_token');
      let processedData = pendingUpload;

      if (pendingUpload.requires_page_selection) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/process-pages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            material_id: pendingUpload.id,
            selected_pages: selectedPages
          })
        });

        if (!response.ok) {
          throw new Error('Failed to process selected pages');
        }

        processedData = await response.json();
      }

      if (!processedData.full_text || processedData.full_text.trim() === '') {
        throw new Error("No text content could be extracted. Please try a different document.");
      }

      const requestBody = {
        text: processedData.full_text,
        material_id: processedData.id,
        topic: processedData.filename.split('.')[0],
        num_questions: selectedNumQuestions,
        difficulty: 'medium',
        question_type: selectedQuestionType
      };

      const quizResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestBody),
      });

      const responseData = await quizResponse.json();

      if (!quizResponse.ok) {
        throw new Error(responseData.detail || `Server error: ${quizResponse.status}`);
      }

      setQuizData({ ...responseData, question_type: selectedQuestionType });
      setCurrentMaterial(processedData);
      setPendingUpload(null);
      setIsGenerating(false);
    } catch (error: any) {
      console.error('Processing failed:', error);
      setError(error.message);
      setIsGenerating(false);
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
          quiz_id: quizData?.id,
          score: score,
          total: total,
          user_id: 'default_user',
          question_type: quizData?.question_type
        }),
      });

      fetchQuizzes();
    } catch (error) {
      console.error('Failed to submit score:', error);
    }
  };

  return (
    <div className="container mx-auto px-6 py-12 md:px-10 max-w-6xl">
      {/* Page Selector Modal */}
      {showPageSelector && pendingUpload && (
        <PageSelector
          totalPages={pendingUpload.total_pages}
          maxPages={pendingUpload.max_pages_limit}
          pagePreviews={pendingUpload.page_previews}
          contentPreview={pendingUpload.text_preview}
          requiresSelection={pendingUpload.requires_page_selection}
          onConfirm={handlePageSelection}
          onCancel={() => {
            setShowPageSelector(false);
            setPendingUpload(null);
            router.push('/');
          }}
        />
      )}

      {error && (
        <div className="mb-12 p-6 rounded-2xl bg-red-50 border border-red-100 text-red-600 font-bold animate-fade-in flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => { setError(null); router.push('/'); }} className="text-red-400 hover:text-red-600">&times;</button>
        </div>
      )}

      {!quizData && !isGenerating ? (
        <div className="animate-fade-in">
          {/* Hero Section */}
          <div className="mb-20">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-muted text-accent text-xs font-black uppercase tracking-widest mb-8">
              <Sparkles size={14} />
              <span>Personalized Assessment Engine</span>
            </div>

            <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tight text-primary leading-[0.9]">
              AI <span className="text-secondary-foreground opacity-30">Examiner</span> <br />
              <span className="text-accent italic">Smart Mastery.</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-500 max-w-3xl leading-relaxed font-medium">
              Take control of your learning with expert-level practice assessments designed for deep retention and conceptual mastery.
            </p>
          </div>

          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <h2 className="text-3xl font-black text-primary mb-2 tracking-tight">Your Exercises</h2>
              <p className="text-slate-500 font-medium text-sm">Review your generated quizzes and track your progress.</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
                <input
                  type="text"
                  placeholder="Search exercises..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 pr-6 py-3 rounded-xl border border-card-border bg-white/50 focus:bg-white focus:ring-4 focus:ring-primary-muted transition-all outline-none w-full md:w-64"
                />
              </div>
            </div>
          </div>

          {isLoadingQuizzes ? (
            <div className="flex justify-center py-24">
              <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            </div>
          ) : filteredQuizzes.length === 0 ? (
            <div className="text-center py-24 premium-card bg-white/40">
              <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-400">
                <BookOpen size={40} />
              </div>
              <h3 className="text-2xl font-black text-primary mb-2">No exercises yet</h3>
              <p className="text-slate-500 mb-8">Upload study materials and generate quizzes to start practicing.</p>
              <Link href="/materials" className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95">
                Go to Materials
              </Link>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {currentQuizzes.map((quiz) => (
                  <div key={quiz.id} className="premium-card p-8 group flex flex-col justify-between hover:border-primary transition-all bg-white/60 hover:shadow-xl hover:-translate-y-1">
                    <div>
                      <div className="flex items-start justify-between mb-8">
                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${quiz.attempts && quiz.attempts > 0
                          ? quiz.lastAccuracy && parseInt(quiz.lastAccuracy) >= 70
                            ? 'bg-success text-white'
                            : 'bg-amber-500 text-white'
                          : 'bg-primary text-white'
                          }`}>
                          {quiz.attempts && quiz.attempts > 0 ? <CheckCircle size={28} /> : <BookOpen size={28} />}
                        </div>

                        <div className="flex flex-col items-end gap-2">
                          {quiz.attempts && quiz.attempts > 0 && quiz.lastAccuracy && (
                            <div className="text-right">
                              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Accuracy</div>
                              <div className="text-2xl font-black text-primary">{quiz.lastAccuracy}</div>
                            </div>
                          )}
                          <button
                            onClick={(e) => handleDeleteQuiz(quiz.id, e)}
                            className="p-2 rounded-lg text-slate-300 hover:text-red-500 hover:bg-red-50 transition-all"
                            title="Delete Exercise"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>

                      <h3 className="text-2xl font-extrabold text-primary mb-4 tracking-tight group-hover:text-accent transition-colors line-clamp-2 min-h-[4rem]">
                        {quiz.title}
                      </h3>

                      <div className="space-y-4 mb-10">
                        <div className="flex items-center gap-3 text-slate-400 font-bold uppercase tracking-widest text-[10px]">
                          <Clock size={14} className="text-slate-300" />
                          <span>{new Date(quiz.created_at).toLocaleDateString()}</span>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <span className="px-3 py-1 rounded-full bg-accent-muted text-accent text-[10px] font-black uppercase tracking-widest">
                            {quiz.questions?.length || 0} Questions
                          </span>
                          {quiz.attempts && quiz.attempts > 0 && (
                            <span className="px-3 py-1 rounded-full bg-primary-muted text-primary text-[10px] font-black uppercase tracking-widest">
                              {quiz.attempts} Attempts
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => router.push(`/quiz/${quiz.id}`)}
                      className="flex items-center justify-center gap-2 w-full py-4 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-md active:scale-95"
                    >
                      {quiz.attempts && quiz.attempts > 0 ? (
                        <>
                          <RotateCcw size={18} />
                          Replay Session
                        </>
                      ) : (
                        <>
                          <Play size={18} fill="currentColor" />
                          Begin Session
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="mt-16 flex items-center justify-center gap-4">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="p-3 rounded-xl border border-card-border bg-white/50 text-slate-500 hover:text-primary hover:border-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    <ChevronLeft size={20} />
                  </button>

                  <div className="flex items-center gap-2">
                    {[...Array(totalPages)].map((_, i) => (
                      <button
                        key={i}
                        onClick={() => setCurrentPage(i + 1)}
                        className={`w-10 h-10 rounded-xl font-bold transition-all ${currentPage === i + 1
                          ? 'bg-primary text-white shadow-md shadow-primary/20'
                          : 'bg-white/50 text-slate-400 hover:text-primary hover:bg-white border border-card-border'
                          }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="p-3 rounded-xl border border-card-border bg-white/50 text-slate-500 hover:text-primary hover:border-primary disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>


      ) : isGenerating ? (
        <div className="min-h-[60vh] flex flex-col items-center justify-center text-center animate-fade-in">
          <div className="relative mb-12">
            <div className="w-32 h-32 rounded-full border-[6px] border-primary-muted border-t-primary animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-primary">
              <Sparkles className="animate-pulse" size={40} />
            </div>
          </div>
          <h2 className="text-4xl font-extrabold mb-4 text-primary tracking-tight">Synthesizing Materials</h2>
          <p className="text-xl text-slate-400 max-w-md mx-auto font-medium leading-relaxed">
            {questionType === 'mixed'
              ? 'Creating a balanced mix of MCQ and short-answer questions...'
              : questionType === 'short'
                ? 'Generating thoughtful short-answer questions...'
                : 'Distilling your content into high-fidelity practice items...'}
          </p>
        </div>
      ) : (
        <div className="animate-fade-in max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-between mb-12 gap-6">
            <button
              onClick={() => { setQuizData(null); router.push('/'); }}
              className="flex items-center gap-3 px-6 py-2.5 rounded-xl border border-card-border hover:bg-white text-slate-500 hover:text-primary font-bold transition-all active:scale-95 shadow-sm"
            >
              &larr; Exit Session
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
              <div className="status-badge bg-success/10 text-success border border-success/20">
                Syncing Progress
              </div>
            </div>
          </div>

          {quizData.question_type === 'mixed' ? (
            <MixedQuiz
              questions={quizData.questions}
              quizId={quizData.id}
              onFinished={handleQuizFinished}
              onReset={() => setQuizData(null)}
              onTryAnotherType={handleTryAnotherType}
            />
          ) : quizData.question_type === 'short' ? (
            <ShortAnswerQuiz
              questions={quizData.questions}
              quizId={quizData.id}
              onFinished={handleQuizFinished}
              onReset={() => setQuizData(null)}
              onTryAnotherType={handleTryAnotherType}
            />
          ) : (
            <QuizInterface
              questions={quizData.questions}
              quizId={quizData.id}
              onFinished={handleQuizFinished}
              onReset={() => setQuizData(null)}
              onTryAnotherType={handleTryAnotherType}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-background relative overflow-hidden">
      {/* Decorative Blobs */}
      <div className="fixed top-[-100px] right-[-100px] w-[600px] h-[600px] bg-accent-muted/30 rounded-full blur-[120px] -z-10 pointer-events-none" />
      <div className="fixed bottom-[-100px] left-[-100px] w-[500px] h-[500px] bg-primary-muted/20 rounded-full blur-[120px] -z-10 pointer-events-none" />

      <Navbar />

      <Suspense fallback={<div className="min-h-screen flex items-center justify-center font-black text-primary animate-pulse">Establishing Environment...</div>}>
        <DashboardContent />
      </Suspense>
    </main>
  );
}
