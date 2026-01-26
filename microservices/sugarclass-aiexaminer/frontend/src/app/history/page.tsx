'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { History, Search, Filter, ArrowRight, Award, Calendar } from 'lucide-react';
import Link from 'next/link';

interface Progress {
    id: string;
    quiz_id: string;
    title: string;
    score: number;
    total: number;
    accuracy: string;
    completed_at: string;
}

export default function HistoryPage() {
    const [history, setHistory] = useState<Progress[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/progress/`);
            const data = await response.json();
            setHistory(data.history || []);
        } catch (error) {
            console.error('Failed to fetch history:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredHistory = history.filter(item =>
        item.title?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <main className="min-h-screen bg-background relative overflow-hidden">
            <div className="fixed top-[-100px] right-[-100px] w-[600px] height-[600px] bg-accent-muted/30 rounded-full blur-[120px] -z-10 pointer-events-none" />
            <Navbar />

            <div className="container mx-auto px-6 py-12 md:px-10 max-w-6xl">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-5xl font-black text-primary mb-2 tracking-tight">Performance History</h1>
                        <p className="text-slate-500 font-medium">Review your past exercises and track your mastery progress.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="text"
                                placeholder="Search sessions..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-12 pr-6 py-3 rounded-xl border border-card-border bg-white/50 focus:bg-white focus:ring-4 focus:ring-primary-muted transition-all outline-none w-full md:w-64"
                            />
                        </div>
                    </div>
                </div>

                {isLoading ? (
                    <div className="flex justify-center py-24">
                        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    </div>
                ) : filteredHistory.length === 0 ? (
                    <div className="text-center py-24 premium-card bg-white/40">
                        <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-400">
                            <History size={40} />
                        </div>
                        <h3 className="text-2xl font-black text-primary mb-2">No history recorded</h3>
                        <p className="text-slate-500 mb-8">Complete a quiz to see your performance metrics here.</p>
                        <Link href="/" className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95">
                            Start Learning
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-6">
                        {filteredHistory.map((item) => (
                            <div key={item.id} className="premium-card p-8 group flex flex-col md:flex-row md:items-center justify-between hover:border-primary-muted transition-all bg-white/60">
                                <div className="flex items-center gap-8 mb-6 md:mb-0">
                                    <div className={`w-16 h-16 rounded-[20px] flex items-center justify-center transition-all ${parseInt(item.accuracy) > 70 ? 'bg-success/10 text-success' : 'bg-primary-muted text-primary'}`}>
                                        <Award size={28} />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-extrabold text-primary mb-1 tracking-tight group-hover:text-accent transition-colors">{item.title}</h3>
                                        <div className="flex items-center gap-4 text-sm font-bold text-slate-400">
                                            <div className="flex items-center gap-1.5 uppercase tracking-widest text-[10px]">
                                                <Calendar size={12} />
                                                <span>{new Date(item.completed_at).toLocaleDateString()}</span>
                                            </div>
                                            <span className="w-1 h-1 rounded-full bg-slate-200"></span>
                                            <span className="text-accent uppercase tracking-widest text-[10px]">Accuracy: {item.accuracy}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between md:justify-end gap-12 border-t md:border-t-0 pt-6 md:pt-0 border-slate-100">
                                    <div className="text-right">
                                        <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Items</div>
                                        <div className="text-2xl font-black text-primary">{item.score} / {item.total}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Status</div>
                                        <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${parseInt(item.accuracy) >= 80 ? 'bg-success/10 text-success' : 'bg-amber-50 text-amber-600'}`}>
                                            {parseInt(item.accuracy) >= 80 ? 'Mastery' : 'Improving'}
                                        </div>
                                    </div>
                                    <button className="p-4 rounded-xl bg-primary-muted text-primary group-hover:bg-primary group-hover:text-white transition-all">
                                        <ArrowRight size={20} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className="mt-12 text-center">
                    <Link href="/" className="text-sm font-bold text-slate-400 hover:text-primary transition-colors">
                        Back to Dashboard
                    </Link>
                </div>
            </div>
        </main>
    );
}
