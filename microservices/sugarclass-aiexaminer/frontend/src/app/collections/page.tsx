'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { FolderPlus, Folder, FileText, Trash2, Plus, Edit3, CheckCircle, X, Upload, FolderOpen } from 'lucide-react';

interface Material {
    id: string;
    filename: string;
    extracted_text: string;
    created_at: string;
    collection_id?: string | null;
}

interface Collection {
    id: string;
    name: string;
    description?: string;
    created_at: string;
    updated_at: string;
    materials: Material[];
    material_count: number;
}

export default function CollectionsPage() {
    const router = useRouter();
    const [collections, setCollections] = useState<Collection[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showNewFolderModal, setShowNewFolderModal] = useState(false);
    const [newFolderName, setNewFolderName] = useState('');
    const [newFolderDescription, setNewFolderDescription] = useState('');
    const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
    const [editedFolderName, setEditedFolderName] = useState('');
    const [selectedFolder, setSelectedFolder] = useState<Collection | null>(null);
    const [uploadingToFolder, setUploadingToFolder] = useState<string | null>(null);

    useEffect(() => {
        fetchCollections();
    }, []);

    const fetchCollections = async () => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/`);
            const data = await response.json();
            setCollections(data);
        } catch (error) {
            console.error('Failed to fetch collections:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const createFolder = async () => {
        if (!newFolderName.trim()) return;

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newFolderName,
                    description: newFolderDescription
                }),
            });
            setNewFolderName('');
            setNewFolderDescription('');
            setShowNewFolderModal(false);
            fetchCollections();
        } catch (error) {
            console.error('Failed to create folder:', error);
            alert('Failed to create folder');
        }
    };

    const deleteFolder = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const collection = collections.find(c => c.id === id);
        if (!confirm(`Delete "${collection?.name}" and all its files (${collection?.material_count} files)?`)) return;

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/${id}`, {
                method: 'DELETE',
            });
            fetchCollections();
        } catch (error) {
            console.error('Failed to delete folder:', error);
        }
    };

    const renameFolder = async (id: string) => {
        if (!editedFolderName.trim()) {
            setEditingFolderId(null);
            return;
        }

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: editedFolderName }),
            });
            setEditingFolderId(null);
            fetchCollections();
        } catch (error) {
            console.error('Failed to rename folder:', error);
        }
    };

    const deleteMaterial = async (collectionId: string, materialId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm('Delete this file?')) return;

        try {
            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/${materialId}`, {
                method: 'DELETE',
            });
            fetchCollections();
            if (selectedFolder?.id === collectionId) {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/${collectionId}`);
                const data = await response.json();
                setSelectedFolder(data);
            }
        } catch (error) {
            console.error('Failed to delete file:', error);
        }
    };

    const handleFileUpload = async (collectionId: string, event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        setUploadingToFolder(collectionId);

        for (const file of Array.from(files)) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('collection_id', collectionId);

            try {
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`, {
                    method: 'POST',
                    body: formData,
                });
            } catch (error) {
                console.error('Failed to upload file:', error);
            }
        }

        setUploadingToFolder(null);
        fetchCollections();

        // Refresh selected folder if open
        if (selectedFolder?.id === collectionId) {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/collections/${collectionId}`);
            const data = await response.json();
            setSelectedFolder(data);
        }
    };

    return (
        <main className="min-h-screen bg-background">
            <Navbar />
            <div className="container mx-auto px-6 py-12 md:px-10 max-w-6xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h1 className="text-5xl font-black text-primary mb-2 tracking-tight">Material Folders</h1>
                        <p className="text-slate-500 font-medium">Organize your materials into folders for better management</p>
                    </div>
                    <button
                        onClick={() => setShowNewFolderModal(true)}
                        className="px-6 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95 flex items-center gap-2"
                    >
                        <FolderPlus size={20} />
                        New Folder
                    </button>
                </div>

                {/* New Folder Modal */}
                {showNewFolderModal && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
                        <div className="premium-card p-8 max-w-md w-full bg-white">
                            <h2 className="text-2xl font-black text-primary mb-6">Create New Folder</h2>
                            <input
                                type="text"
                                value={newFolderName}
                                onChange={(e) => setNewFolderName(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && createFolder()}
                                placeholder="Folder name"
                                className="w-full px-4 py-3 rounded-xl border border-card-border mb-4 outline-none focus:ring-2 focus:ring-primary-muted"
                                autoFocus
                            />
                            <textarea
                                value={newFolderDescription}
                                onChange={(e) => setNewFolderDescription(e.target.value)}
                                placeholder="Description (optional)"
                                className="w-full px-4 py-3 rounded-xl border border-card-border mb-6 outline-none focus:ring-2 focus:ring-primary-muted resize-none"
                                rows={3}
                            />
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={createFolder}
                                    disabled={!newFolderName.trim()}
                                    className="flex-1 px-6 py-3 rounded-xl bg-success text-white font-bold hover:bg-success/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Create
                                </button>
                                <button
                                    onClick={() => {
                                        setShowNewFolderModal(false);
                                        setNewFolderName('');
                                        setNewFolderDescription('');
                                    }}
                                    className="flex-1 px-6 py-3 rounded-xl border-2 border-card-border text-slate-600 font-bold hover:bg-slate-50 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Folder Detail Modal */}
                {selectedFolder && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6 overflow-y-auto">
                        <div className="premium-card p-8 max-w-4xl w-full bg-white my-8">
                            <div className="flex items-start justify-between mb-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <FolderOpen size={32} className="text-accent" />
                                        <h2 className="text-3xl font-black text-primary">{selectedFolder.name}</h2>
                                    </div>
                                    {selectedFolder.description && (
                                        <p className="text-slate-500 text-sm">{selectedFolder.description}</p>
                                    )}
                                </div>
                                <button
                                    onClick={() => setSelectedFolder(null)}
                                    className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            {/* Upload Area */}
                            <div className="mb-6">
                                <label
                                    htmlFor={`upload-${selectedFolder.id}`}
                                    className="flex items-center justify-center gap-3 w-full py-4 rounded-xl border-2 border-dashed border-primary/30 bg-primary-muted text-primary font-bold hover:bg-primary hover:text-white transition-all cursor-pointer"
                                >
                                    <Plus size={20} />
                                    Add Files to Folder
                                    <input
                                        id={`upload-${selectedFolder.id}`}
                                        type="file"
                                        multiple
                                        accept=".pdf,.png,.jpg,.jpeg"
                                        onChange={(e) => handleFileUpload(selectedFolder.id, e)}
                                        className="hidden"
                                    />
                                </label>
                            </div>

                            {/* Files List */}
                            <div className="space-y-3">
                                {selectedFolder.materials.length === 0 ? (
                                    <div className="text-center py-12 text-slate-400">
                                        <FileText size={48} className="mx-auto mb-4 opacity-30" />
                                        <p className="font-medium">No files in this folder yet</p>
                                    </div>
                                ) : (
                                    selectedFolder.materials.map((material) => (
                                        <div
                                            key={material.id}
                                            className="flex items-center justify-between p-4 rounded-xl bg-slate-50 hover:bg-slate-100 transition-all group"
                                        >
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <FileText size={20} className="text-slate-400 flex-shrink-0" />
                                                <span className="font-medium text-slate-700 truncate">{material.filename}</span>
                                            </div>
                                            <button
                                                onClick={(e) => deleteMaterial(selectedFolder.id, material.id, e)}
                                                className="p-2 rounded-lg text-slate-300 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
                                                title="Delete File"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Folders Grid */}
                {isLoading ? (
                    <div className="flex justify-center py-24">
                        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    </div>
                ) : collections.length === 0 ? (
                    <div className="text-center py-24 premium-card bg-white/40">
                        <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-6 text-slate-400">
                            <Folder size={40} />
                        </div>
                        <h3 className="text-2xl font-black text-primary mb-2">No folders yet</h3>
                        <p className="text-slate-500 mb-8">Create your first folder to organize materials</p>
                        <button
                            onClick={() => setShowNewFolderModal(true)}
                            className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95"
                        >
                            Create Folder
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {collections.map((collection) => (
                            <div
                                key={collection.id}
                                onClick={() => setSelectedFolder(collection)}
                                className="premium-card p-6 hover:border-accent/30 transition-all bg-white/60 group cursor-pointer"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 rounded-2xl bg-accent-muted text-accent group-hover:bg-accent group-hover:text-white transition-all">
                                        <Folder size={28} />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setEditingFolderId(collection.id);
                                                setEditedFolderName(collection.name);
                                            }}
                                            className="p-2 text-slate-300 hover:text-primary hover:bg-primary-muted rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                            title="Rename folder"
                                        >
                                            <Edit3 size={16} />
                                        </button>
                                        <button
                                            onClick={(e) => deleteFolder(collection.id, e)}
                                            className="p-2 text-slate-300 hover:text-error hover:bg-red-50 rounded-lg transition-all"
                                            title="Delete folder"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>

                                {editingFolderId === collection.id ? (
                                    <div className="flex items-center gap-2 mb-3" onClick={(e) => e.stopPropagation()}>
                                        <input
                                            type="text"
                                            value={editedFolderName}
                                            onChange={(e) => setEditedFolderName(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && renameFolder(collection.id)}
                                            className="flex-1 text-lg font-bold px-3 py-2 rounded-lg border border-primary outline-none focus:ring-2 focus:ring-primary-muted"
                                            autoFocus
                                        />
                                        <button
                                            onClick={() => renameFolder(collection.id)}
                                            className="p-2 rounded-lg bg-success text-white hover:bg-success/90"
                                        >
                                            <CheckCircle size={16} />
                                        </button>
                                        <button
                                            onClick={() => setEditingFolderId(null)}
                                            className="p-2 rounded-lg bg-slate-200 text-slate-600 hover:bg-slate-300"
                                        >
                                            <X size={16} />
                                        </button>
                                    </div>
                                ) : (
                                    <h3 className="text-xl font-black text-primary mb-3 line-clamp-1 group-hover:text-accent transition-colors">
                                        {collection.name}
                                    </h3>
                                )}

                                {collection.description && (
                                    <p className="text-sm text-slate-500 mb-4 line-clamp-2">{collection.description}</p>
                                )}

                                <div className="flex items-center justify-between text-xs">
                                    <span className="px-3 py-1 rounded-full bg-primary-muted text-primary font-black uppercase tracking-widest">
                                        {collection.material_count} {collection.material_count === 1 ? 'File' : 'Files'}
                                    </span>
                                    <span className="text-slate-400 font-medium">
                                        {new Date(collection.created_at).toLocaleDateString()}
                                    </span>
                                </div>

                                {/* Upload input (hidden) */}
                                <label
                                    htmlFor={`folder-upload-${collection.id}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className="mt-4 flex items-center justify-center gap-2 w-full py-2.5 rounded-xl border-2 border-primary/20 text-primary text-sm font-bold hover:bg-primary-muted transition-all cursor-pointer"
                                >
                                    <Plus size={16} />
                                    Add Files
                                    <input
                                        id={`folder-upload-${collection.id}`}
                                        type="file"
                                        multiple
                                        accept=".pdf,.png,.jpg,.jpeg"
                                        onChange={(e) => handleFileUpload(collection.id, e)}
                                        className="hidden"
                                    />
                                </label>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}
