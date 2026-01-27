'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import UploadSection from '@/components/UploadSection';
import QuizInterface from '@/components/QuizInterface';
import ShortAnswerQuiz from '@/components/ShortAnswerQuiz';
import PageSelector from '@/components/PageSelector';
import { Sparkles, Trophy, Database, Zap, ArrowRight, BookOpen, FileText, MessageSquare, CheckSquare, Clock, Award, GraduationCap, History } from 'lucide-react';

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

  const [quizData, setQuizData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [questionType, setQuestionType] = useState<'mcq' | 'short'>('mcq');
  const [numQuestions, setNumQuestions] = useState(15); // Default to 15 questions

  // Page selection and configuration state
  const [pendingUpload, setPendingUpload] = useState<UploadResponse | null>(null);
  const [showPageSelector, setShowPageSelector] = useState(false);

  // Progress stats
  const [stats, setStats] = useState<{ quizzes_taken: number, average_accuracy: string } | null>(null);
  const [recentHistory, setRecentHistory] = useState<any[]>([]);

  useEffect(() => {
    if (materialId) {
      handleGenerateFromMaterial(materialId);
    }
    fetchStats();
  }, [materialId]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/progress/`);
      const data = await response.json();
      setStats({
        quizzes_taken: data.quizzes_taken,
        average_accuracy: data.average_accuracy
      });
      setRecentHistory(data.history?.slice(0, 3) || []);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleGenerateFromMaterial = async (id: string) => {
    setIsGenerating(true);
    setError(null);
    try {
      // 1. Fetch material details
      const token = localStorage.getItem('sugarclass_token');
      const matRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const materials = await matRes.json();
      const material = materials.find((m: any) => m.id === id);

      if (!material) throw new Error("Material not found");

      // 2. Generate quiz
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          text: material.extracted_text,
          material_id: id,
          topic: material.filename.split('.')[0],
          num_questions: 5,
          difficulty: 'medium',
          question_type: questionType
        }),
      });
      const data = await response.json();
      setQuizData({ ...data, question_type: questionType });
    } catch (error: any) {
      console.error('Quiz generation failed:', error);
      setError(error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUploadComplete = async (uploadResponse: UploadResponse) => {
    if (showPageSelector || quizData || isGenerating) return;

    setPendingUpload(uploadResponse);
    setShowPageSelector(true);
  };

  const handlePageSelection = async (selectedPages: number[], selectedQuestionType: 'mcq' | 'short', selectedNumQuestions: number) => {
    if (!pendingUpload) return;

    setShowPageSelector(false);
    setIsGenerating(true);
    setError(null);
    setQuestionType(selectedQuestionType);
    setNumQuestions(selectedNumQuestions);

    try {
      const token = localStorage.getItem('sugarclass_token');
      let processedData = pendingUpload;

      // Only call process-pages if we actually did selection (large PDF)
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

      // Validate text content
      if (!processedData.full_text || processedData.full_text.trim() === '') {
        throw new Error("No text content could be extracted. Please try a different document.");
      }

      // Generate the quiz
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
    } catch (error) {
      console.error('Failed to submit score:', error);
    }
  };

  return (
    <div className="container mx-auto px-6 py-12 md:px-10 lg:py-20">
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
          }}
        />
      )}


      {!quizData && !isGenerating ? (
        <div className="animate-fade-in max-w-6xl mx-auto">
          {/* Context Header */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-muted text-accent text-xs font-black uppercase tracking-widest mb-8">
            <Sparkles size={14} />
            <span>Personalized Assessment Engine</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start mb-24">
            <div className="lg:col-span-12">
              <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tight text-primary leading-[0.9]">
                AI <span className="text-secondary-foreground opacity-30">Examiner</span> <br />
                <span className="text-accent italic">Smart Mastery.</span>
              </h1>
              <p className="text-xl md:text-2xl text-slate-500 max-w-3xl leading-relaxed font-medium">
                Upload your study materials and let our refined AI generate expert-level practice assessments designed for deep retention and mastery.
              </p>
            </div>
          </div>

          {error && (
            <div className="mb-12 p-6 rounded-2xl bg-red-50 border border-red-100 text-red-600 font-bold animate-fade-in flex items-center justify-between">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">&times;</button>
            </div>
          )}

          {/* Page Limit Notice */}
          <div className="mb-8 p-6 rounded-2xl bg-primary-muted border border-primary/10 flex items-start gap-4">
            <div className="p-3 rounded-xl bg-primary/10 text-primary">
              <FileText size={24} />
            </div>
            <div>
              <h3 className="font-bold text-primary mb-1">Smart Page Processing</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                For optimal AI performance, we process up to <span className="font-bold text-primary">20 pages</span> per document.
                For larger PDFs, you'll be able to select which pages to focus on.
              </p>
            </div>
          </div>

          <UploadSection onUploadComplete={handleUploadComplete} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-24 items-stretch">
            {/* Recent Activity Column */}
            <div className="lg:col-span-1 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-primary flex items-center gap-2">
                  <Clock size={20} className="text-accent" />
                  Recent Sessions
                </h3>
                <Link href="/history" className="text-xs font-bold text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
                  View All <ArrowRight size={12} />
                </Link>
              </div>
              <div className="premium-card flex-1 bg-white/40 border-card-border/50 divide-y divide-card-border/30">
                {recentHistory.length > 0 ? (
                  recentHistory.map((item, i) => (
                    <div key={i} className="p-5 hover:bg-white/60 transition-colors flex items-center justify-between group">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${parseInt(item.accuracy) >= 80 ? 'bg-success/10 text-success' : 'bg-primary/5 text-primary'}`}>
                          <Award size={20} />
                        </div>
                        <div>
                          <div className="text-sm font-bold text-primary group-hover:text-accent transition-colors line-clamp-1">{item.title}</div>
                          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{new Date(item.completed_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-black text-primary">{item.accuracy}</div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">{item.score}/{item.total}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-12 text-center flex flex-col items-center justify-center h-full opacity-40">
                    <History size={32} className="mb-3" />
                    <p className="text-xs font-bold uppercase tracking-widest">No sessions yet</p>
                  </div>
                )}
              </div>
            </div>

            {/* Neural Insights Column */}
            <div className="lg:col-span-1 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-primary flex items-center gap-2">
                  <Sparkles size={20} className="text-accent" />
                  AI Insights
                </h3>
              </div>
              <div className="premium-card flex-1 bg-gradient-to-br from-primary/5 to-accent/5 p-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-8 opacity-5 text-accent group-hover:scale-110 transition-transform duration-700">
                  <Sparkles size={160} />
                </div>

                <div className="relative z-10 h-full flex flex-col">
                  {stats ? (
                    <>
                      <div className="p-4 rounded-2xl bg-white/80 border border-card-border/50 mb-6 group-hover:shadow-lg transition-all duration-500">
                        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-accent mb-2">Mastery Feedback</div>
                        <p className="text-sm font-medium text-slate-600 leading-relaxed italic">
                          "{parseInt(stats.average_accuracy) >= 80
                            ? "Your high accuracy shows strong conceptual retention. Try harder materials to maintain your edge."
                            : "Consistency is key. Focus on reviewing the explanation cards after each incorrect answer."}"
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mt-auto">
                        <div className="p-4 rounded-2xl bg-white/40 border border-card-border/30">
                          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Global Rank</div>
                          <div className="text-xl font-black text-primary">Top 12%</div>
                        </div>
                        <div className="p-4 rounded-2xl bg-white/40 border border-card-border/30">
                          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Star Badges</div>
                          <div className="text-xl font-black text-primary">{Math.floor(stats.quizzes_taken / 5)} Earned</div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="animate-pulse flex flex-col gap-4">
                      <div className="h-20 bg-white/40 rounded-2xl"></div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="h-16 bg-white/40 rounded-2xl"></div>
                        <div className="h-16 bg-white/40 rounded-2xl"></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Metrics Column */}
            <div className="lg:col-span-1 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-primary flex items-center gap-2">
                  <Zap size={20} className="text-accent" />
                  Live Metrics
                </h3>
              </div>
              <div className="grid grid-cols-1 gap-6 flex-1">
                {[
                  { label: 'Total Quizzes', value: stats?.quizzes_taken || 0, icon: GraduationCap, color: 'text-blue-600 bg-blue-50' },
                  { label: 'Avg. Accuracy', value: stats?.average_accuracy || '0%', icon: Trophy, color: 'text-emerald-600 bg-emerald-50' },
                ].map((metric, i) => (
                  <div key={i} className="premium-card p-6 flex items-center gap-6 bg-white/60 hover:bg-white transition-all">
                    <div className={`p-4 rounded-2xl ${metric.color}`}>
                      <metric.icon size={24} />
                    </div>
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-1">{metric.label}</div>
                      <div className="text-3xl font-black text-primary tracking-tight">{metric.value}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Proof Section */}
          <div className="pt-24 border-t border-card-border flex flex-col md:flex-row items-center justify-between gap-8 text-center md:text-left">
            <div className="flex flex-wrap justify-center md:justify-start items-center gap-6 md:gap-12 opacity-40 grayscale">
              <span className="font-extrabold text-2xl tracking-tighter">OXFORD</span>
              <span className="font-extrabold text-2xl tracking-tighter">CAMBRIDGE</span>
              <span className="font-extrabold text-2xl tracking-tighter">IVY LEAGUE</span>
            </div>
            <div className="flex items-center gap-3 text-slate-400 font-bold">
              <BookOpen size={20} />
              <span>Trusted by 45,000+ Students globally</span>
            </div>
          </div>
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
            {questionType === 'short'
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
              <div className={`status-badge border ${quizData.question_type === 'short' ? 'bg-amber-50 text-amber-600 border-amber-200' : 'bg-blue-50 text-blue-600 border-blue-200'}`}>
                {quizData.question_type === 'short' ? 'Short Answer Mode' : 'Multiple Choice Mode'}
              </div>
              <div className="status-badge bg-success/10 text-success border border-success/20">
                Syncing Progress
              </div>
            </div>
          </div>

          {quizData.question_type === 'short' ? (
            <ShortAnswerQuiz
              questions={quizData.questions}
              quizId={quizData.id}
              onFinished={handleQuizFinished}
              onReset={() => setQuizData(null)}
            />
          ) : (
            <QuizInterface
              questions={quizData.questions}
              quizId={quizData.id}
              onFinished={handleQuizFinished}
              onReset={() => setQuizData(null)}
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
