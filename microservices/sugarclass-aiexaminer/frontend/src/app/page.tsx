'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import UploadSection from '@/components/UploadSection';
import QuizInterface from '@/components/QuizInterface';
import { Sparkles, Trophy, Database, Zap, ArrowRight, BookOpen } from 'lucide-react';

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const materialId = searchParams.get('mid');

  const [quizData, setQuizData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (materialId) {
      handleGenerateFromMaterial(materialId);
    }
  }, [materialId]);

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
          difficulty: 'medium'
        }),
      });
      const data = await response.json();
      setQuizData(data);
    } catch (error: any) {
      console.error('Quiz generation failed:', error);
      setError(error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUploadComplete = async (uploadResponse: any) => {
    setIsGenerating(true);
    setError(null);
    const token = localStorage.getItem('sugarclass_token');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/quiz/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          text: uploadResponse.full_text,
          material_id: uploadResponse.id,
          topic: uploadResponse.filename.split('.')[0],
          num_questions: 5,
          difficulty: 'medium'
        }),
      });
      const data = await response.json();
      setQuizData(data);
    } catch (error) {
      console.error('Quiz generation failed:', error);
      setError("Failed to generate quiz. Please try again.");
    } finally {
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
          quiz_id: quizData.id,
          score: score,
          total: total,
          user_id: 'default_user'
        }),
      });
    } catch (error) {
      console.error('Failed to submit score:', error);
    }
  };

  return (
    <div className="container mx-auto px-6 py-12 md:px-10 lg:py-20">
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
                Turn your notes <br />
                into <span className="text-secondary-foreground opacity-30">perfect</span> <span className="text-accent italic">scores.</span>
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

          <UploadSection onUploadComplete={handleUploadComplete} />

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
            {[
              { label: 'Session Analytics', title: 'Smart Progress', desc: 'Track your weak areas with AI-driven insights.', icon: Zap, color: 'bg-amber-50 text-amber-600', link: '/history' },
              { label: 'Content Sync', title: 'Source Library', desc: 'Manage your textbooks and handwritten papers.', icon: Database, color: 'bg-blue-50 text-blue-600', link: '/materials' },
              { label: 'Global Ranking', title: 'Merit List', desc: 'Compare your mastery score with students worldwide.', icon: Trophy, color: 'bg-emerald-50 text-emerald-600', link: '/history' },
            ].map((stat, i) => (
              <div key={i} className="premium-card p-10 group hover:border-primary-muted h-full flex flex-col justify-between">
                <div>
                  <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-6">{stat.label}</div>
                  <div className="flex items-center gap-4 mb-4">
                    <div className={`p-4 rounded-2xl ${stat.color}`}>
                      <stat.icon size={24} />
                    </div>
                    <h3 className="text-2xl font-extrabold text-primary tracking-tight">{stat.title}</h3>
                  </div>
                  <p className="text-slate-500 font-medium leading-relaxed mb-8">{stat.desc}</p>
                </div>
                <button
                  onClick={() => router.push(stat.link)}
                  className="flex items-center gap-2 text-sm font-bold text-primary group-hover:gap-4 transition-all duration-500"
                >
                  View {stat.title} <ArrowRight size={18} />
                </button>
              </div>
            ))}
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
            Gemini is distilling your content into high-fidelity practice items. This usually takes around 10-15 seconds.
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
              <div className="status-badge bg-success/10 text-success border border-success/20">
                Syncing Progress
              </div>
            </div>
          </div>
          <QuizInterface questions={quizData.questions} quizId={quizData.id} onFinished={handleQuizFinished} />
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
