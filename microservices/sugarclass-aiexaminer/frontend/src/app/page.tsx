'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import QuizInterface from '@/components/QuizInterface';
import ShortAnswerQuiz from '@/components/ShortAnswerQuiz';
import MixedQuiz from '@/components/MixedQuiz';
import PageSelector from '@/components/PageSelector';
import { Search, RotateCcw, Play, CheckCircle, Sparkles, Trophy, Zap, ArrowRight, Clock, Award, GraduationCap, History, BookOpen, Upload as UploadIcon, ChevronLeft, ChevronRight, Trash2, Edit3, X, Save, Check } from 'lucide-react';

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

  // Question Review State
  const [previewQuestions, setPreviewQuestions] = useState<any[] | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [isRegeneratingSingle, setIsRegeneratingSingle] = useState<number | null>(null);
  const [quizTitle, setQuizTitle] = useState('');

  // Exercise Rename State
  const [editingQuizId, setEditingQuizId] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');

  // Comprehensive Loading State
  const [processingStep, setProcessingStep] = useState(0);
  const steps = [
    { title: "Reading Material", description: "Extracting text and structure from your document...", icon: <BookOpen className="text-blue-500" /> },
    { title: "Analyzing Context", description: "Identifying key concepts and learning objectives...", icon: <Sparkles className="text-amber-500" /> },
    { title: "Crafting Questions", description: "Developing high-quality personalized quiz items...", icon: <Zap className="text-indigo-500" /> },
    { title: "Finalizing", description: "Organizing your exercise for review...", icon: <CheckCircle className="text-success" /> }
  ];

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
      const quizzesResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/`);
      const quizzesData = await quizzesResponse.json();

      const progressResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/progress/`);
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
    setProcessingStep(0);
    setError(null);
    try {
      const token = localStorage.getItem('sugarclass_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${id}/config`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!res.ok) {
        throw new Error("Material config not found");
      }

      setProcessingStep(1);
      const material = await res.json();

      // Artificial delay for better UX feel
      await new Promise(r => setTimeout(r, 800));
      setProcessingStep(2);

      const hasText = material.full_text && material.full_text.trim() !== '';
      const canSelectPages = material.requires_page_selection && material.total_pages > 0;

      if (!hasText && !canSelectPages) {
        throw new Error("This document appears to be empty or unreadable. Please try a different source.");
      }

      setPendingUpload(material);
      setShowPageSelector(true);
      setProcessingStep(3);
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
    setProcessingStep(0);
    setError(null);
    try {
      const token = localStorage.getItem('sugarclass_token');
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/session/${sid}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });

      if (!res.ok) {
        throw new Error("Mobile session not found");
      }

      setProcessingStep(1);
      const data = await res.json();

      await new Promise(r => setTimeout(r, 800));
      setProcessingStep(2);

      if (data.status !== 'completed' || !data.materials || data.materials.length === 0) {
        throw new Error("Session is not ready or has no documents.");
      }

      // Check the first material for page selection
      const firstMatId = data.materials[0].id;
      const configRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${firstMatId}/config`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const configData = await configRes.json();

      setProcessingStep(3);
      setPendingUpload(configData);
      setShowPageSelector(true);
      setIsGenerating(false);
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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/${id}`, {
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

  const handleRenameQuiz = async (id: string) => {
    if (!newTitle.trim()) {
      setEditingQuizId(null);
      return;
    }

    try {
      const token = localStorage.getItem('sugarclass_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ title: newTitle })
      });

      if (!response.ok) throw new Error('Failed to rename quiz');

      setEditingQuizId(null);
      fetchQuizzes();
    } catch (error) {
      console.error('Rename failed:', error);
      alert('Failed to rename exercise.');
    }
  };

  const handlePageSelection = async (selectedPages: number[], selectedQuestionType: 'mcq' | 'short' | 'mixed', selectedNumQuestions: number) => {
    if (!pendingUpload) return;

    setIsGenerating(true);
    setProcessingStep(0);
    setError(null);
    setQuestionType(selectedQuestionType);
    setNumQuestions(selectedNumQuestions);

    try {
      const token = localStorage.getItem('sugarclass_token');
      let processedData = pendingUpload;

      if (pendingUpload.requires_page_selection) {
        setProcessingStep(1);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/process-pages`, {
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
        setProcessingStep(2);
      }

      setCurrentMaterial(processedData);
      setShowPageSelector(false);

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

      setProcessingStep(3);
      // Use generate-preview to get questions for review
      const quizResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/generate-preview`, {
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

      // Set up for review instead of directly starting quiz
      setPreviewQuestions(responseData.questions);
      setQuizTitle(processedData.filename.split('.')[0]);
      setPendingUpload(null);
      setIsGenerating(false);
      setIsReviewing(true);
    } catch (error: any) {
      console.error('Processing failed:', error);
      setError(error.message);
      setIsGenerating(false);
    }
  };

  // Handler to regenerate a single question
  const handleRegenerateQuestion = async (index: number) => {
    if (!previewQuestions || !currentMaterial) return;

    setIsRegeneratingSingle(index);
    try {
      const token = localStorage.getItem('sugarclass_token');
      const currentQuestion = previewQuestions[index];

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/regenerate-single`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          text: currentMaterial.full_text,
          existing_questions: previewQuestions.map(q => q.question),
          question_type: currentQuestion.question_type,
          difficulty: 'medium'
        })
      });

      if (!response.ok) throw new Error('Failed to regenerate question');

      const newQuestion = await response.json();
      const updatedQuestions = [...previewQuestions];
      updatedQuestions[index] = newQuestion;
      setPreviewQuestions(updatedQuestions);
    } catch (err) {
      console.error(err);
      alert('Failed to regenerate question.');
    } finally {
      setIsRegeneratingSingle(null);
    }
  };

  // Handler to remove a question from preview
  const handleRemoveQuestion = (index: number) => {
    if (!previewQuestions) return;
    const updatedQuestions = [...previewQuestions];
    updatedQuestions.splice(index, 1);
    setPreviewQuestions(updatedQuestions);
  };

  const handlePreviewQuestionChange = (index: number, field: string, value: any) => {
    if (!previewQuestions) return;
    const updated = [...previewQuestions];
    updated[index] = { ...updated[index], [field]: value };
    setPreviewQuestions(updated);
  };

  const handlePreviewOptionChange = (questionIndex: number, optionIndex: number, value: string) => {
    if (!previewQuestions) return;
    const updated = [...previewQuestions];
    const question = { ...updated[questionIndex] };
    if (question.options) {
      const updatedOptions = [...question.options];
      updatedOptions[optionIndex] = value;
      question.options = updatedOptions;
      updated[questionIndex] = question;
      setPreviewQuestions(updated);
    }
  };

  // Helper to save quiz to database
  const saveQuiz = async () => {
    if (!previewQuestions || !currentMaterial || previewQuestions.length === 0) return null;

    const token = localStorage.getItem('sugarclass_token');
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/create-from-preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        title: quizTitle || 'Untitled Quiz',
        questions: previewQuestions,
        material_id: currentMaterial.id,
        source_text: currentMaterial.full_text
      })
    });

    if (!response.ok) throw new Error('Failed to create quiz');
    return await response.json();
  };

  // Handler to save and start quiz
  const handleApproveAndStart = async () => {
    setIsGenerating(true);
    setProcessingStep(0); // Start processing steps for saving
    try {
      const data = await saveQuiz();
      if (data) {
        setProcessingStep(3); // Mark as finalized
        setQuizData({ ...data, question_type: questionType });
        setPreviewQuestions(null);
        setIsReviewing(false);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Handler to save for later (go back to list)
  const handleSaveForLater = async () => {
    setIsGenerating(true);
    setProcessingStep(0); // Start processing steps for saving
    try {
      await saveQuiz();
      setProcessingStep(3); // Mark as finalized
      setIsReviewing(false);
      setPreviewQuestions(null);
      fetchQuizzes();
      router.push('/');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Handler to save and open in full editor
  const handleSaveAndEdit = async () => {
    setIsGenerating(true);
    setProcessingStep(0); // Start processing steps for saving
    try {
      const data = await saveQuiz();
      if (data) {
        setProcessingStep(3); // Mark as finalized
        setIsReviewing(false);
        setPreviewQuestions(null);
        router.push(`/quiz/${data.id}/edit`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleQuizFinished = async (score: number, total: number) => {
    const token = localStorage.getItem('sugarclass_token');
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/quiz/submit`, {
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

      {/* Comprehensive Processing Overlay */}
      {isGenerating && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 sm:p-10 overflow-hidden">
          <div className="absolute inset-0 bg-primary/20 backdrop-blur-3xl animate-pulse"></div>
          <div className="absolute inset-0 bg-gradient-to-tr from-primary/30 via-transparent to-accent/20"></div>

          <div className="relative w-full max-w-xl">
            <div className="premium-card p-8 md:p-12 bg-white/70 shadow-3xl text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1.5 bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary via-accent to-indigo-500 transition-all duration-1000 ease-out"
                  style={{ width: `${((processingStep + 1) / steps.length) * 100}%` }}
                ></div>
              </div>

              <div className="mb-8 relative inline-block">
                <div className="absolute -inset-4 bg-primary/10 rounded-full animate-ping opacity-40"></div>
                <div className="w-20 h-20 md:w-24 md:h-24 rounded-3xl bg-white shadow-xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500">
                  <div className="scale-150 transform transition-all duration-1000">
                    {steps[processingStep]?.icon}
                  </div>
                </div>
              </div>

              <h2 className="text-3xl md:text-4xl font-black text-primary mb-3 tracking-tight animate-fade-in">
                {steps[processingStep]?.title}
              </h2>
              <p className="text-slate-500 font-medium mb-10 max-w-sm mx-auto animate-fade-in delay-100">
                {steps[processingStep]?.description}
              </p>

              <div className="flex justify-center gap-3 mb-8">
                {steps.map((_, i) => (
                  <div
                    key={i}
                    className={`h-1.5 rounded-full transition-all duration-500 ${i === processingStep
                      ? 'w-10 bg-primary shadow-lg shadow-primary/20'
                      : i < processingStep ? 'w-4 bg-success' : 'w-4 bg-slate-200'
                      }`}
                  ></div>
                ))}
              </div>

              <div className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-primary/40">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"></div>
                  Neural Engine Active
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main UI */}
      {!quizData && !isGenerating && !isReviewing ? (
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

                      {editingQuizId === quiz.id ? (
                        <div className="mb-4">
                          <input
                            type="text"
                            value={newTitle}
                            onChange={(e) => setNewTitle(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleRenameQuiz(quiz.id)}
                            className="w-full text-lg font-bold px-3 py-2 rounded-lg border border-primary outline-none focus:ring-2 focus:ring-primary-muted mb-2"
                            autoFocus
                          />
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleRenameQuiz(quiz.id)}
                              className="flex-1 py-2 rounded-lg bg-success text-white hover:bg-success/90 transition-all text-sm font-bold"
                            >
                              <CheckCircle size={16} className="inline mr-1" />
                              Save
                            </button>
                            <button
                              onClick={() => setEditingQuizId(null)}
                              className="flex-1 py-2 rounded-lg bg-slate-200 text-slate-600 hover:bg-slate-300 transition-all text-sm font-bold"
                            >
                              <X size={16} className="inline mr-1" />
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-start gap-2 mb-4">
                          <h3 className="text-2xl font-extrabold text-primary tracking-tight group-hover:text-accent transition-colors line-clamp-2 min-h-[4rem] flex-1">
                            {quiz.title}
                          </h3>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingQuizId(quiz.id);
                              setNewTitle(quiz.title);
                            }}
                            className="p-2 rounded-lg text-slate-300 hover:text-primary hover:bg-primary-muted transition-all opacity-0 group-hover:opacity-100"
                            title="Rename Exercise"
                          >
                            <Edit3 size={16} />
                          </button>
                        </div>
                      )}

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

                    <div className="space-y-3">
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

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/quiz/${quiz.id}/edit`);
                        }}
                        className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl border-2 border-accent/30 bg-accent/5 text-accent font-bold hover:bg-accent hover:text-white transition-all"
                      >
                        <Edit3 size={16} />
                        Edit Questions
                      </button>
                    </div>
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


      ) : isReviewing && previewQuestions ? (
        <div className="animate-fade-in max-w-4xl mx-auto">
          {/* Review Header */}
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-muted text-accent text-xs font-black uppercase tracking-widest mb-6">
              <Sparkles size={14} />
              <span>Review Your Questions</span>
            </div>
            <h2 className="text-4xl font-black text-primary mb-4 tracking-tight">
              {previewQuestions.length} Questions Generated
            </h2>
            <p className="text-lg text-slate-500 mb-6">
              Review the questions below. Remove any you don't like or regenerate them.
            </p>

            {/* Quiz Title Input */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <input
                type="text"
                value={quizTitle}
                onChange={(e) => setQuizTitle(e.target.value)}
                placeholder="Enter quiz title..."
                className="flex-1 px-4 py-3 rounded-xl border border-card-border bg-white focus:ring-4 focus:ring-primary-muted outline-none font-medium text-lg"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSaveForLater}
                  disabled={previewQuestions.length === 0 || isGenerating}
                  className="px-6 py-3 rounded-xl border-2 border-primary/20 bg-white text-primary font-bold hover:bg-primary-muted transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
                  title="Save question set without starting"
                >
                  <Save size={18} />
                  Save
                </button>
                <button
                  onClick={handleSaveAndEdit}
                  disabled={previewQuestions.length === 0 || isGenerating}
                  className="px-6 py-3 rounded-xl border-2 border-accent/20 bg-white text-accent font-bold hover:bg-accent-muted transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
                  title="Open in full editor"
                >
                  <Edit3 size={18} />
                  Edit Details
                </button>
                <button
                  onClick={handleApproveAndStart}
                  disabled={previewQuestions.length === 0 || isGenerating}
                  className="px-8 py-3 rounded-xl bg-success text-white font-bold hover:bg-success/90 transition-all shadow-lg active:scale-95 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <CheckCircle size={18} />
                  Approve & Start Quiz
                </button>
              </div>
            </div>
          </div>

          {/* Question Cards */}
          <div className="space-y-6">
            {previewQuestions.map((question, index) => (
              <div key={index} className="premium-card p-6 bg-white/80 relative group">
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

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRegenerateQuestion(index)}
                      disabled={isRegeneratingSingle !== null}
                      className="p-2 rounded-lg text-slate-400 hover:text-primary hover:bg-primary-muted transition-all disabled:opacity-50"
                      title="Regenerate Question"
                    >
                      <RotateCcw size={18} className={isRegeneratingSingle === index ? 'animate-spin' : ''} />
                    </button>
                    <button
                      onClick={() => handleRemoveQuestion(index)}
                      className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                      title="Remove Question"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                <textarea
                  value={question.question}
                  onChange={(e) => handlePreviewQuestionChange(index, 'question', e.target.value)}
                  className="w-full text-lg font-bold text-primary mb-4 p-3 rounded-lg border border-transparent focus:border-primary/20 focus:ring-4 focus:ring-primary-muted bg-primary-muted/10 outline-none resize-none"
                  rows={2}
                />

                {question.question_type === 'mcq' && question.options && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                    {question.options.map((option: string, optIdx: number) => (
                      <div key={optIdx} className="flex items-center gap-2">
                        <div className="flex-1">
                          <input
                            type="text"
                            value={option}
                            onChange={(e) => handlePreviewOptionChange(index, optIdx, e.target.value)}
                            className={`w-full px-4 py-3 rounded-xl border text-sm font-medium outline-none focus:ring-4 ${option === question.correct_answer
                              ? 'bg-success/10 border-success/30 text-success focus:ring-success/10'
                              : 'bg-slate-50 border-slate-200 text-slate-600 focus:ring-primary-muted'
                              }`}
                          />
                        </div>
                        {option === question.correct_answer && (
                          <div className="w-8 h-8 rounded-full bg-success/20 text-success flex items-center justify-center" title="Correct Answer">
                            <Check size={16} />
                          </div>
                        )}
                        <button
                          onClick={() => handlePreviewQuestionChange(index, 'correct_answer', option)}
                          className={`p-2 rounded-lg transition-all ${option === question.correct_answer ? 'text-success' : 'text-slate-300 hover:text-success'}`}
                          title="Set as correct answer"
                        >
                          <CheckCircle size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {question.question_type === 'short' && question.expected_answer && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-4">
                    <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Expected Answer</div>
                    <textarea
                      value={question.expected_answer || ''}
                      onChange={(e) => handlePreviewQuestionChange(index, 'expected_answer', e.target.value)}
                      className="w-full text-slate-600 font-medium bg-white border border-slate-200 rounded-lg p-3 outline-none focus:ring-4 focus:ring-primary-muted resize-none"
                      rows={3}
                    />
                  </div>
                )}

                {question.explanation && (
                  <div className="text-sm">
                    <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Explanation (Optional)</div>
                    <textarea
                      value={question.explanation || ''}
                      onChange={(e) => handlePreviewQuestionChange(index, 'explanation', e.target.value)}
                      className="w-full text-slate-500 bg-slate-50 px-4 py-3 rounded-lg border border-slate-100 outline-none focus:ring-4 focus:ring-primary-muted resize-none"
                      rows={2}
                    />
                  </div>
                )}

                {/* Loading overlay for regenerating */}
                {isRegeneratingSingle === index && (
                  <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-3xl flex items-center justify-center">
                    <div className="flex items-center gap-3 text-primary font-bold">
                      <RotateCcw size={20} className="animate-spin" />
                      Regenerating...
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Bottom Action Bar */}
          <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 p-6 premium-card bg-primary/5 border-primary/20">
            <div className="text-center sm:text-left">
              <p className="font-bold text-primary">{previewQuestions.length} questions ready</p>
              <p className="text-sm text-slate-500">Click approve when you're satisfied with the questions</p>
            </div>
            <div className="flex flex-wrap justify-center sm:justify-end gap-3">
              <button
                onClick={() => {
                  setIsReviewing(false);
                  setPreviewQuestions(null);
                  router.push('/');
                }}
                className="px-6 py-3 rounded-xl border border-card-border text-slate-500 font-bold hover:bg-white transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveForLater}
                disabled={previewQuestions.length === 0 || isGenerating}
                className="px-6 py-3 rounded-xl border-2 border-primary/20 bg-white text-primary font-bold hover:bg-primary-muted transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
              >
                <Save size={18} />
                Save
              </button>
              <button
                onClick={handleSaveAndEdit}
                disabled={previewQuestions.length === 0 || isGenerating}
                className="px-6 py-3 rounded-xl border-2 border-accent/20 bg-white text-accent font-bold hover:bg-accent-muted transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
              >
                <Edit3 size={18} />
                Full Editor
              </button>
              <button
                onClick={handleApproveAndStart}
                disabled={previewQuestions.length === 0 || isGenerating}
                className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play size={18} fill="currentColor" />
                Start Quiz
              </button>
            </div>
          </div>
        </div>
      ) : quizData ? (
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
      ) : null}
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
