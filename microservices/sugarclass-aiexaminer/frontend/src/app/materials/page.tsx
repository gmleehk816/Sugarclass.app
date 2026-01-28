'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import UploadSection from '@/components/UploadSection';
import { FileText, Trash2, Play, Search, Clock, FileType } from 'lucide-react';
import Link from 'next/link';

interface Material {
    id: string;
    filename: string;
    extracted_text: string;
    created_at: string;
    session_id: string | null;
}

interface MaterialGroup {
    sessionId: string | null;
    materials: Material[];
    createdAt: string;
    title: string;
}

export default function MaterialsPage() {
    const router = useRouter();
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

    const deleteMaterial = async (id: string, e?: React.MouseEvent) => {
        e?.stopPropagation();
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

    const deleteGroup = async (group: MaterialGroup, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm(`Are you sure you want to delete all ${group.materials.length} materials in this session?`)) return;

        try {
            for (const material of group.materials) {
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/${material.id}`, {
                    method: 'DELETE',
                });
            }
            const idsToDelete = new Set(group.materials.map(m => m.id));
            setMaterials(materials.filter(m => !idsToDelete.has(m.id)));
        } catch (error) {
            console.error('Group delete failed:', error);
        }
    };

    const handleUploadComplete = (uploadResponse: any) => {
        fetchMaterials();
        setTimeout(() => {
            const listElement = document.getElementById('materials-list');
            listElement?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    const filteredMaterials = materials.filter(m =>
        m.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Grouping logic
    const groups: MaterialGroup[] = [];
    const sessionMap = new Map<string, Material[]>();
    const noSessionMaterials: Material[] = [];

    filteredMaterials.forEach(m => {
        if (m.session_id) {
            if (!sessionMap.has(m.session_id)) {
                sessionMap.set(m.session_id, []);
            }
            sessionMap.get(m.session_id)?.push(m);
        } else {
            noSessionMaterials.push(m);
        }
    });

    // Add session groups
    sessionMap.forEach((mats, sid) => {
        groups.push({
            sessionId: sid,
            materials: mats,
            createdAt: mats[0].created_at,
            title: mats.length > 1 ? `Session Bundle (${mats.length} files)` : mats[0].filename
        });
    });

    // Add individual materials
    noSessionMaterials.forEach(m => {
        groups.push({
            sessionId: null,
            materials: [m],
            createdAt: m.created_at,
            title: m.filename
        });
    });

    // Sort groups by date
    groups.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

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

                {/* Upload Section */}
                <UploadSection
                    onUploadComplete={handleUploadComplete}
                    onShowLibrary={() => {
                        // Already on materials page, just scroll to list
                        const listElement = document.getElementById('materials-list');
                        listElement?.scrollIntoView({ behavior: 'smooth' });
                    }}
                />

                {/* Materials List */}
                <div id="materials-list">
                    <h2 className="text-3xl font-black text-primary mb-6">Your Study Materials</h2>
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
                        {groups.map((group, idx) => (
                            <div key={group.sessionId || idx} className="premium-card p-8 flex flex-col justify-between hover:border-accent/30 transition-all bg-white/60 group">
                                <div>
                                    <div className="flex items-start justify-between mb-6">
                                        <div className={`p-4 rounded-2xl transition-all ${group.materials.length > 1 ? 'bg-accent-muted text-accent group-hover:bg-accent group-hover:text-white' : 'bg-primary-muted text-primary group-hover:bg-primary group-hover:text-white'}`}>
                                            <FileType size={28} />
                                        </div>
                                        <button
                                            onClick={(e) => group.sessionId ? deleteGroup(group, e) : deleteMaterial(group.materials[0].id, e)}
                                            className="p-2 text-slate-300 hover:text-error transition-colors"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                    <h3 className="text-xl font-black text-primary mb-2 line-clamp-2 leading-tight group-hover:text-accent transition-colors">{group.title}</h3>
                                    <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">
                                        <Clock size={14} />
                                        <span>{new Date(group.createdAt).toLocaleDateString()}</span>
                                    </div>

                                    {group.materials.length > 1 ? (
                                        <div className="space-y-2 mb-8">
                                            {group.materials.slice(0, 3).map(m => (
                                                <div key={m.id} className="text-xs font-bold text-slate-500 flex items-center gap-2 truncate">
                                                    <div className="w-1 h-1 rounded-full bg-slate-300" />
                                                    {m.filename}
                                                </div>
                                            ))}
                                            {group.materials.length > 3 && (
                                                <div className="text-[10px] text-slate-400 font-bold italic">
                                                    + {group.materials.length - 3} more files
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-slate-500 text-sm font-medium line-clamp-3 mb-8 italic">
                                            "{group.materials[0].extracted_text.substring(0, 150)}..."
                                        </p>
                                    )}
                                </div>

                                <Link
                                    href={group.materials.length > 1
                                        ? `/?sid=${group.sessionId}`
                                        : `/?mid=${group.materials[0].id}`
                                    }
                                    className="flex items-center justify-center gap-3 w-full py-3.5 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-md active:scale-95"
                                >
                                    <Play size={18} fill="currentColor" />
                                    {group.materials.length > 1 ? 'Start Session Quiz' : 'Configure & Start Quiz'}
                                </Link>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}
