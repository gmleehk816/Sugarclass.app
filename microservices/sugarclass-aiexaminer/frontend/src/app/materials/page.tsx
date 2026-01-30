'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import UploadSection from '@/components/UploadSection';
import { FileText, Trash2, Play, Search, Clock, FileType, Edit3, CheckCircle, X, Plus, FolderOpen } from 'lucide-react';
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
    const [editingMaterialId, setEditingMaterialId] = useState<string | null>(null);
    const [newFilename, setNewFilename] = useState('');
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [newSessionName, setNewSessionName] = useState('');
    const [selectedSession, setSelectedSession] = useState<MaterialGroup | null>(null);

    useEffect(() => {
        fetchMaterials();
    }, []);

    const fetchMaterials = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/`);
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
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${id}`, {
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
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${material.id}`, {
                    method: 'DELETE',
                });
            }
            const idsToDelete = new Set(group.materials.map(m => m.id));
            setMaterials(materials.filter(m => !idsToDelete.has(m.id)));
        } catch (error) {
            console.error('Group delete failed:', error);
        }
    };

    const renameMaterial = async (id: string) => {
        if (!newFilename.trim()) {
            setEditingMaterialId(null);
            return;
        }

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: newFilename }),
            });
            setMaterials(materials.map(m => m.id === id ? { ...m, filename: newFilename } : m));
            setEditingMaterialId(null);
        } catch (error) {
            console.error('Rename failed:', error);
            alert('Failed to rename material.');
        }
    };

    const renameSession = async (sessionId: string, newName: string) => {
        if (!newName.trim()) {
            setEditingSessionId(null);
            return;
        }

        try {
            // Update all materials in this session with new naming pattern
            const sessionMaterials = materials.filter(m => m.session_id === sessionId);
            for (const material of sessionMaterials) {
                const extension = material.filename.split('.').pop();
                const baseName = newName.replace(/\s+/g, '_');
                const newFilename = sessionMaterials.length > 1
                    ? `${baseName}_${sessionMaterials.indexOf(material) + 1}.${extension}`
                    : `${baseName}.${extension}`;

                await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/${material.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: newFilename }),
                });
            }
            setEditingSessionId(null);
            fetchMaterials();
        } catch (error) {
            console.error('Failed to rename session:', error);
            alert('Failed to rename folder.');
        }
    };

    const handleAddFilesToSession = async (sessionId: string, files: FileList) => {
        for (const file of Array.from(files)) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', sessionId);

            try {
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/`, {
                    method: 'POST',
                    body: formData,
                });
            } catch (error) {
                console.error('Failed to upload file:', error);
            }
        }
        fetchMaterials();
        setSelectedSession(null);
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
                                        <div className="flex items-center gap-2">
                                            {group.sessionId && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setEditingSessionId(group.sessionId);
                                                        setNewSessionName(group.title.replace(` (${group.materials.length} files)`, '').replace('Session Bundle', 'Folder'));
                                                    }}
                                                    className="p-2 text-slate-300 hover:text-primary hover:bg-primary-muted rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                                    title="Rename folder"
                                                >
                                                    <Edit3 size={18} />
                                                </button>
                                            )}
                                            {!group.sessionId && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setEditingMaterialId(group.materials[0].id);
                                                        setNewFilename(group.materials[0].filename);
                                                    }}
                                                    className="p-2 text-slate-300 hover:text-primary hover:bg-primary-muted rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                                    title="Edit material name"
                                                >
                                                    <Edit3 size={18} />
                                                </button>
                                            )}
                                            {group.sessionId && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedSession(group);
                                                    }}
                                                    className="p-2 text-slate-300 hover:text-accent hover:bg-accent-muted rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                                    title="Manage files"
                                                >
                                                    <FolderOpen size={18} />
                                                </button>
                                            )}
                                            <button
                                                onClick={(e) => group.sessionId ? deleteGroup(group, e) : deleteMaterial(group.materials[0].id, e)}
                                                className="p-2 text-slate-300 hover:text-error hover:bg-red-50 rounded-lg transition-colors"
                                            >
                                                <Trash2 size={20} />
                                            </button>
                                        </div>
                                    </div>

                                    {editingSessionId === group.sessionId ? (
                                        <div className="mb-4">
                                            <input
                                                type="text"
                                                value={newSessionName}
                                                onChange={(e) => setNewSessionName(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && group.sessionId && renameSession(group.sessionId, newSessionName)}
                                                className="w-full text-lg font-bold px-3 py-2 rounded-lg border border-primary outline-none focus:ring-2 focus:ring-primary-muted mb-2"
                                                autoFocus
                                            />
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => group.sessionId && renameSession(group.sessionId, newSessionName)}
                                                    className="flex-1 py-2 rounded-lg bg-success text-white text-sm font-bold hover:bg-success/90 transition-all flex items-center justify-center gap-1"
                                                >
                                                    <CheckCircle size={16} /> Save
                                                </button>
                                                <button
                                                    onClick={() => setEditingSessionId(null)}
                                                    className="flex-1 py-2 rounded-lg bg-slate-200 text-slate-600 text-sm font-bold hover:bg-slate-300 transition-all flex items-center justify-center gap-1"
                                                >
                                                    <X size={16} /> Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : editingMaterialId === group.materials[0]?.id ? (
                                        <div className="mb-4">
                                            <input
                                                type="text"
                                                value={newFilename}
                                                onChange={(e) => setNewFilename(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && renameMaterial(group.materials[0].id)}
                                                className="w-full text-lg font-bold px-3 py-2 rounded-lg border border-primary outline-none focus:ring-2 focus:ring-primary-muted mb-2"
                                                autoFocus
                                            />
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => renameMaterial(group.materials[0].id)}
                                                    className="flex-1 py-2 rounded-lg bg-success text-white text-sm font-bold hover:bg-success/90 transition-all flex items-center justify-center gap-1"
                                                >
                                                    <CheckCircle size={16} /> Save
                                                </button>
                                                <button
                                                    onClick={() => setEditingMaterialId(null)}
                                                    className="flex-1 py-2 rounded-lg bg-slate-200 text-slate-600 text-sm font-bold hover:bg-slate-300 transition-all flex items-center justify-center gap-1"
                                                >
                                                    <X size={16} /> Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <h3 className="text-xl font-black text-primary mb-2 line-clamp-2 leading-tight group-hover:text-accent transition-colors">{group.title}</h3>
                                    )}
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

                {/* Folder Detail Modal */}
                {selectedSession && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
                        <div className="premium-card p-8 max-w-3xl w-full bg-white max-h-[80vh] overflow-y-auto">
                            <div className="flex items-start justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <FolderOpen size={32} className="text-accent" />
                                    <div>
                                        <h2 className="text-2xl font-black text-primary">{selectedSession.title}</h2>
                                        <p className="text-sm text-slate-500">{selectedSession.materials.length} files</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setSelectedSession(null)}
                                    className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            {/* Add Files Button */}
                            <label
                                htmlFor="add-files-input"
                                className="flex items-center justify-center gap-3 w-full py-4 rounded-xl border-2 border-dashed border-primary/30 bg-primary-muted text-primary font-bold hover:bg-primary hover:text-white transition-all cursor-pointer mb-6"
                            >
                                <Plus size={20} />
                                Add More Files
                                <input
                                    id="add-files-input"
                                    type="file"
                                    multiple
                                    accept=".pdf,.png,.jpg,.jpeg"
                                    onChange={(e) => {
                                        if (e.target.files && selectedSession.sessionId) {
                                            handleAddFilesToSession(selectedSession.sessionId, e.target.files);
                                        }
                                    }}
                                    className="hidden"
                                />
                            </label>

                            {/* Files List */}
                            <div className="space-y-3">
                                {selectedSession.materials.map((material) => (
                                    <div
                                        key={material.id}
                                        className="flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-all group"
                                    >
                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                            <FileText size={20} className="text-slate-400 flex-shrink-0" />
                                            <span className="font-medium text-slate-700 truncate">{material.filename}</span>
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                deleteMaterial(material.id, e);
                                                setTimeout(() => {
                                                    if (selectedSession?.sessionId) {
                                                        const updatedMaterials = selectedSession.materials.filter(m => m.id !== material.id);
                                                        setSelectedSession({ ...selectedSession, materials: updatedMaterials });
                                                    }
                                                }, 100);
                                            }}
                                            className="p-2 rounded-lg text-slate-300 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
                                            title="Delete File"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
