'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { Trophy, Search, TrendingUp, Award, Calendar, Target } from 'lucide-react';
import Link from 'next/link';

interface Progress {
    id: string;
    quiz_id: string;
    title: string;
    score: number;
    total: number;
    accuracy: string;
    completed_at: string;
    material_id?: string;
}

export default function RankingsPage() {
    const [history, setHistory] = useState<Progress[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [stats, setStats] = useState<any>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/progress/`);
            const data = await response.json();
            setHistory(data.history || []);
            setStats({
                quizzes_taken: data.quizzes_taken,
                average_accuracy: data.average_accuracy
            });
        } catch (error) {
            console.error('Failed to fetch rankings:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredHistory = history.filter(item =>
        item.title?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Sort by accuracy descending
    const sortedHistory = [...filteredHistory].sort((a, b) => {
        return parseFloat(b.accuracy) - parseFloat(a.accuracy);
    });

    return (
        <main className="min-h-screen bg-background relative overflow-hidden">
            <div className="fixed top-[-100px] right-[-100px] w-[600px] height-[600px] bg-accent-muted/30 rounded-full blur-[120px] -z-10 pointer-events-none" />
            <Navbar />

            <div className="container mx-auto px-6 py-12 md:px-10 max-w-6xl">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-5xl font-black text-primary mb-2 tracking-tight">Performance Rankings</h1>
                        <p className="text-slate-500 font-medium">Track your mastery progress and see your best performances.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="text"
                                placeholder="Search rankings..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-12 pr-6 py-3 rounded-xl border border-card-border bg-white/50 focus:bg-white focus:ring-4 focus:ring-primary-muted transition-all outline-none w-full md:w-64"
                            />
                        </div>
                    </div>
                </div>

                {/* Stats Overview */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                        <div className="premium-card p-6 bg-gradient-to-br from-blue-50 to-blue-100/50">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-blue-500 text-white">
                                    <Trophy size={24} />
                                </div>
                                <div className="text-3xl font-black text-primary">{stats.quizzes_taken}</div>
                            </div>
                            <div className="text-sm font-bold text-slate-600 uppercase tracking-widest">Total Quizzes</div>
                        </div>

                        <div className="premium-card p-6 bg-gradient-to-br from-emerald-50 to-emerald-100/50">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-emerald-500 text-white">
                                    <Target size={24} />
                                </div>
                                <div className="text-3xl font-black text-primary">{stats.average_accuracy}</div>
                            </div>
                            <div className="text-sm font-bold text-slate-600 uppercase tracking-widest">Avg. Accuracy</div>
                        </div>

                        <div className="premium-card p-6 bg-gradient-to-br from-amber-50 to-amber-100/50">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-amber-500 text-white">
                                    <TrendingUp size={24} />
                                </div>
                                <div className="text-3xl font-black text-primary">
                                    {parseInt(stats.average_accuracy) >= 90 ? 'Expert' :
                                        parseInt(stats.average_accuracy) >= 70 ? 'Scholar' : 'Learner'}
                                </div>
                            </div>
                            <div className="text-sm font-bold text-slate-600 uppercase tracking-widest">Current Rank</div>
                        </div>
                    </div>
                )}

                {isLoading ? (
                    <div className="flex justify-center py-24">
                        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    </div>
                ) : sortedHistory.length === 0 ? (
                    <div className="text-center py-24 premium-card bg-white/40">
                        <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-400">
                            <Trophy size={40} />
                        </div>
                        <h3 className="text-2xl font-black text-primary mb-2">No rankings yet</h3>
                        <p className="text-slate-500 mb-8">Complete quizzes to see your performance rankings here.</p>
                        <Link href="/materials" className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95">
                            Start Practicing
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-black text-primary mb-6 flex items-center gap-3">
                            <Trophy className="text-accent" size={28} />
                            Top Performances
                        </h2>
                        <div className="grid grid-cols-1 gap-4">
                            {sortedHistory.map((item, index) => (
                                <div
                                    key={item.id}
                                    className={`premium-card p-6 group flex items-center justify-between hover:border-amber-300 transition-all ${index === 0 ? 'bg-gradient-to-r from-amber-50/80 to-yellow-50/80 border-amber-200' :
                                        index === 1 ? 'bg-gradient-to-r from-slate-50/80 to-gray-50/80 border-slate-200' :
                                            index === 2 ? 'bg-gradient-to-r from-orange-50/80 to-amber-50/80 border-orange-200' :
                                                'bg-white/60'
                                        }`}
                                >
                                    <div className="flex items-center gap-6">
                                        {/* Rank Badge */}
                                        <div className={`w-14 h-14 rounded-full flex items-center justify-center font-black text-2xl ${index === 0 ? 'bg-amber-500 text-white' :
                                            index === 1 ? 'bg-slate-400 text-white' :
                                                index === 2 ? 'bg-orange-400 text-white' :
                                                    'bg-primary-muted text-primary'
                                            }`}>
                                            #{index + 1}
                                        </div>

                                        {/* Quiz Info */}
                                        <div>
                                            <h3 className="text-xl font-extrabold text-primary mb-1 tracking-tight group-hover:text-accent transition-colors">
                                                {item.title}
                                            </h3>
                                            <div className="flex items-center gap-4 text-sm font-bold text-slate-400">
                                                <div className="flex items-center gap-1.5 uppercase tracking-widest text-[10px]">
                                                    <Calendar size={12} />
                                                    <span>{new Date(item.completed_at).toLocaleDateString()}</span>
                                                </div>
                                                <span className="w-1 h-1 rounded-full bg-slate-200"></span>
                                                <span className="text-accent uppercase tracking-widest text-[10px]">
                                                    Score: {item.score}/{item.total}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Accuracy Badge */}
                                    <div className="flex items-center gap-6">
                                        <div className="text-right">
                                            <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Accuracy</div>
                                            <div className="text-4xl font-black text-primary">{item.accuracy}</div>
                                        </div>
                                        <Award
                                            size={36}
                                            className={parseInt(item.accuracy) >= 80 ? 'text-success' : 'text-slate-300'}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="mt-12 text-center">
                    <Link href="/" className="text-sm font-bold text-slate-400 hover:text-primary transition-colors">
                        View All Exercises
                    </Link>
                </div>
            </div>
        </main>
    );
}
