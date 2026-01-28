'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Camera, Upload, CheckCircle2, AlertCircle, GraduationCap, FileText, Trash2, X } from 'lucide-react';

interface UploadedFile {
    id: string;
    filename: string;
    uploadedAt: Date;
}

function MobileUploadContent() {
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('sid');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [justUploaded, setJustUploaded] = useState(false);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        // Handle multiple files
        for (let i = 0; i < files.length; i++) {
            await uploadFile(files[i]);
        }

        // Reset input so same file can be selected again
        e.target.value = '';
    };

    const uploadFile = async (file: File) => {
        setIsUploading(true);
        setError(null);
        setJustUploaded(false);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId || '');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setUploadedFiles(prev => [...prev, {
                    id: data.id,
                    filename: file.name,
                    uploadedAt: new Date()
                }]);
                setJustUploaded(true);
                setTimeout(() => setJustUploaded(false), 2000);
            } else {
                setError('Upload failed. Please try again.');
            }
        } catch (error) {
            console.error('Mobile upload failed:', error);
            setError('Network error. Check your connection.');
        } finally {
            setIsUploading(false);
        }
    };

    const removeFile = (fileId: string) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    return (
        <div className="min-h-screen bg-background text-primary flex flex-col px-6 py-8 relative overflow-hidden">
            {/* Decorative Blobs */}
            <div className="fixed top-[-100px] right-[-100px] w-[400px] h-[400px] bg-accent-muted/30 rounded-full blur-[100px] -z-10 pointer-events-none" />
            <div className="fixed bottom-[-100px] left-[-100px] w-[300px] h-[300px] bg-primary-muted/20 rounded-full blur-[100px] -z-10 pointer-events-none" />

            {/* Header */}
            <div className="space-y-4 mb-8 text-center">
                <div className="h-14 w-14 rounded-[20px] bg-primary mx-auto flex items-center justify-center text-white shadow-xl">
                    <GraduationCap size={28} />
                </div>
                <div>
                    <h1 className="text-3xl font-black tracking-tight text-primary">Mobile Bridge</h1>
                    <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px] mt-1">Session Active</p>
                </div>
            </div>

            {/* Success Animation */}
            {justUploaded && (
                <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 animate-fade-in">
                    <div className="w-24 h-24 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-2xl animate-scale-in">
                        <CheckCircle2 size={48} />
                    </div>
                </div>
            )}

            {/* Upload Buttons */}
            <div className="space-y-4 mb-8">
                {/* Camera Button */}
                <label className="flex flex-col items-center justify-center p-10 premium-card bg-white/60 border-2 border-dashed border-card-border hover:border-accent active:scale-95 group transition-all duration-300 cursor-pointer">
                    <div className="w-16 h-16 rounded-[28px] bg-accent-muted text-accent flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <Camera size={32} />
                    </div>
                    <span className="text-xl font-black text-primary">Take Photo</span>
                    <span className="text-xs text-slate-400 mt-1 font-bold">Snap worksheets or notes</span>
                    <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        className="hidden"
                        onChange={handleFileSelect}
                        disabled={isUploading}
                        multiple
                    />
                </label>

                {/* Gallery/Files Button */}
                <label className="flex items-center gap-4 p-5 premium-card bg-white/60 hover:bg-white active:scale-95 transition-all cursor-pointer group">
                    <div className="p-3 rounded-xl bg-primary-muted text-primary group-hover:bg-primary group-hover:text-white transition-all">
                        <Upload size={20} />
                    </div>
                    <div className="flex-1 text-left">
                        <div className="font-extrabold text-primary">Choose from Gallery</div>
                        <div className="text-xs text-slate-400 font-bold">PDFs, images, or documents</div>
                    </div>
                    <input
                        type="file"
                        accept="image/*,.pdf"
                        className="hidden"
                        onChange={handleFileSelect}
                        disabled={isUploading}
                        multiple
                    />
                </label>
            </div>

            {/* Loading State */}
            {isUploading && (
                <div className="flex flex-col items-center gap-3 mb-6 text-primary font-bold animate-pulse">
                    <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    <span className="text-sm">Uploading...</span>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="p-4 rounded-xl bg-red-50 text-red-600 flex items-center gap-3 mb-6 text-sm font-bold border border-red-100">
                    <AlertCircle size={18} />
                    {error}
                    <button onClick={() => setError(null)} className="ml-auto">
                        <X size={18} />
                    </button>
                </div>
            )}

            {/* Uploaded Files List */}
            {uploadedFiles.length > 0 && (
                <div className="space-y-3 mb-6">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-black text-primary uppercase tracking-widest">
                            Uploaded ({uploadedFiles.length})
                        </h3>
                        <div className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-600 text-xs font-black">
                            ✓ Synced
                        </div>
                    </div>

                    <div className="space-y-2">
                        {uploadedFiles.map((file) => (
                            <div key={file.id} className="flex items-center gap-3 p-4 premium-card bg-white/80 group">
                                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                                    <FileText size={20} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-primary text-sm truncate">{file.filename}</div>
                                    <div className="text-xs text-slate-400 font-bold">
                                        {file.uploadedAt.toLocaleTimeString()}
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeFile(file.id)}
                                    className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Info Text */}
            <div className="mt-auto text-center space-y-4">
                {uploadedFiles.length > 0 && (
                    <div className="p-4 premium-card bg-emerald-50/50 border-emerald-200">
                        <p className="text-sm font-bold text-emerald-700 mb-2">
                            ✓ Files synced to your desktop
                        </p>
                        <p className="text-xs text-emerald-600">
                            Keep adding more or check your computer to start the quiz
                        </p>
                    </div>
                )}

                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest leading-loose">
                    Secure Session • Auto-Sync • {sessionId?.slice(0, 8)}
                </p>
            </div>
        </div>
    );
}

export default function MobileUploadPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center font-black text-primary animate-pulse">Connecting...</div>}>
            <MobileUploadContent />
        </Suspense>
    );
}

