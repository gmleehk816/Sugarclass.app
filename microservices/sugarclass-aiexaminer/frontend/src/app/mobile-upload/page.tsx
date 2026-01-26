'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Camera, Upload, CheckCircle2, AlertCircle, Sparkles, GraduationCap } from 'lucide-react';

function MobileUploadContent() {
    const searchParams = useSearchParams();
    const sessionId = searchParams.get('sid');
    const [isUploading, setIsUploading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');

    const handleCapture = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.[0]) return;

        setIsUploading(true);
        setStatus('idle');

        const formData = new FormData();
        formData.append('file', e.target.files[0]);
        formData.append('session_id', sessionId || '');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`, {
                method: 'POST',
                body: formData,
            });
            if (response.ok) {
                setStatus('success');
            } else {
                setStatus('error');
            }
        } catch (error) {
            console.error('Mobile upload failed:', error);
            setStatus('error');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-primary flex flex-col items-center justify-center px-6 py-12 relative overflow-hidden">
            {/* Decorative Blobs */}
            <div className="fixed top-[-100px] right-[-100px] w-[400px] h-[400px] bg-accent-muted/30 rounded-full blur-[100px] -z-10 pointer-events-none" />
            <div className="fixed bottom-[-100px] left-[-100px] w-[300px] h-[300px] bg-primary-muted/20 rounded-full blur-[100px] -z-10 pointer-events-none" />

            <div className="w-full max-w-md space-y-10 text-center animate-fade-in">
                <div className="space-y-4">
                    <div className="h-16 w-16 rounded-[24px] bg-primary mx-auto flex items-center justify-center text-white shadow-xl">
                        <GraduationCap size={32} />
                    </div>
                    <div>
                        <h1 className="text-4xl font-black tracking-tight text-primary">Quiz Master</h1>
                        <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px] mt-2">Mobile Bridge Session</p>
                    </div>
                </div>

                {status === 'success' ? (
                    <div className="p-10 premium-card bg-emerald-50/30 border-emerald-500/20 text-center animate-fade-in">
                        <div className="w-20 h-20 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-200">
                            <CheckCircle2 size={40} />
                        </div>
                        <h2 className="text-3xl font-black mb-3 text-primary">Uploaded!</h2>
                        <p className="text-slate-500 font-medium mb-10 leading-relaxed">Your materials have been synced. Check your iPad or computer dashboard to start the quiz.</p>
                        <button
                            onClick={() => setStatus('idle')}
                            className="w-full py-4 rounded-2xl bg-primary text-white font-bold shadow-xl active:scale-95 transition-all"
                        >
                            Add More Pages
                        </button>
                    </div>
                ) : (
                    <div className="space-y-8">
                        <div className="grid grid-cols-1 gap-6">
                            <label className="flex flex-col items-center justify-center p-14 premium-card bg-white/60 border-2 border-dashed border-card-border hover:border-accent group transition-all duration-500">
                                <div className="w-20 h-20 rounded-[32px] bg-accent-muted text-accent flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                    <Camera size={40} />
                                </div>
                                <span className="text-2xl font-black text-primary">Snap a Photo</span>
                                <span className="text-sm text-slate-400 mt-2 font-bold tracking-tight">Worksheets, Notes, or Textbooks</span>
                                <input
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    className="hidden"
                                    onChange={handleCapture}
                                    disabled={isUploading}
                                />
                            </label>

                            <label className="flex items-center gap-5 p-6 premium-card bg-white/60 hover:bg-white transition-all cursor-pointer group">
                                <div className="p-4 rounded-2xl bg-primary-muted text-primary group-hover:bg-primary group-hover:text-white transition-all">
                                    <Upload size={24} />
                                </div>
                                <div className="flex-1 text-left">
                                    <div className="font-extrabold text-primary">Choose from Files</div>
                                    <div className="text-xs text-slate-400 font-bold">Pick existing PDF or Images</div>
                                </div>
                                <input
                                    type="file"
                                    className="hidden"
                                    onChange={handleCapture}
                                    disabled={isUploading}
                                />
                            </label>
                        </div>

                        {isUploading && (
                            <div className="flex flex-col items-center gap-4 text-primary font-bold animate-pulse">
                                <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                                <span>Syncing with Cloud...</span>
                            </div>
                        )}

                        {status === 'error' && (
                            <div className="p-4 rounded-xl bg-red-50 text-red-600 flex items-center gap-3 justify-center text-sm font-bold border border-red-100">
                                <AlertCircle size={18} />
                                Sync failed. Please try again.
                            </div>
                        )}

                        <p className="text-[10px] text-slate-400 px-8 font-bold uppercase tracking-widest leading-loose">
                            Cloud Sync Active • End-to-End Encrypted • Sugarclass Secure
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default function MobileUploadPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center font-black text-primary animate-pulse">Establishing Secure Bridge...</div>}>
            <MobileUploadContent />
        </Suspense>
    );
}
