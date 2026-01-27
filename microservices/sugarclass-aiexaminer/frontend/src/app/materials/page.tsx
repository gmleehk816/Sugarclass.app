'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { FileText, Trash2, Play, Search, Clock, FileType } from 'lucide-react';
import Link from 'next/link';

interface Material {
    id: string;
    filename: string;
    extracted_text: string;
    created_at: string;
}

export default function MaterialsPage() {
    const [materials, setMaterials] = useState<Material[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchMaterials();
    }, []);

    const fetchMaterials = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`);
            const data = await response.json();
            setMaterials(data);
        } catch (error) {
            console.error('Failed to fetch materials:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const deleteMaterial = async (id: string) => {
        if (!confirm('Are you sure you want to delete this material?')) return;
        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/${id}`, {
                method: 'DELETE',
            });
            setMaterials(materials.filter(m => m.id !== id));
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const filteredMaterials = materials.filter(m =>
        m.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <main className="min-h-screen bg-background relative overflow-hidden">
            <div className="fixed top-[-100px] right-[-100px] w-[600px] height-[600px] bg-accent-muted/30 rounded-full blur-[120px] -z-10 pointer-events-none" />
            <Navbar />

            <div className="container mx-auto px-6 py-12 md:px-10 max-w-6xl">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-5xl font-black text-primary mb-2 tracking-tight">Source Library</h1>
                        <p className="text-slate-500 font-medium">Manage your uploaded textbooks, notes, and study guides.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="text"
                                placeholder="Search materials..."
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
                ) : filteredMaterials.length === 0 ? (
                    <div className="text-center py-24 premium-card bg-white/40">
                        <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-400">
                            <FileText size={40} />
                        </div>
                        <h3 className="text-2xl font-black text-primary mb-2">No materials found</h3>
                        <p className="text-slate-500 mb-8">Upload your first study material to get started.</p>
                        <Link href="/" className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95">
                            Go to Upload
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredMaterials.map((material) => (
                            <div key={material.id} className="premium-card p-8 flex flex-col justify-between hover:border-accent/30 transition-all bg-white/60 group">
                                <div>
                                    <div className="flex items-start justify-between mb-6">
                                        <div className="p-4 rounded-2xl bg-primary-muted text-primary group-hover:bg-primary group-hover:text-white transition-all">
                                            <FileType size={28} />
                                        </div>
                                        <button
                                            onClick={() => deleteMaterial(material.id)}
                                            className="p-2 text-slate-300 hover:text-error transition-colors"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                    <h3 className="text-xl font-black text-primary mb-2 line-clamp-2 leading-tight group-hover:text-accent transition-colors">{material.filename}</h3>
                                    <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">
                                        <Clock size={14} />
                                        <span>{new Date(material.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-slate-500 text-sm font-medium line-clamp-3 mb-8 italic">
                                        "{material.extracted_text.substring(0, 150)}..."
                                    </p>
                                </div>

                                <Link
                                    href={`/?mid=${material.id}`}
                                    className="flex items-center justify-center gap-3 w-full py-3.5 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-md active:scale-95"
                                >
                                    <Play size={18} fill="currentColor" />
                                    Configure & Start Quiz
                                </Link>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}
