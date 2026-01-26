'use client';

import { useState, useEffect, useCallback } from 'react';
import { Upload, Smartphone, Camera, FileText, CheckCircle2, RotateCcw } from 'lucide-react';

export default function UploadSection({ onUploadComplete }: { onUploadComplete: (data: any) => void }) {
    const [isUploading, setIsUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [qrCode, setQrCode] = useState<string | null>(null);
    const [isPolling, setIsPolling] = useState(false);
    const [mobileStatus, setMobileStatus] = useState<'idle' | 'syncing' | 'done'>('idle');

    // Fetch initial session and QR
    useEffect(() => {
        const startSession = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/start-session`);
                const data = await response.json();
                setSessionId(data.session_id);
                setQrCode(data.qr_code);
                setIsPolling(true);
            } catch (error) {
                console.error('Failed to start mobile session:', error);
            }
        };
        startSession();
    }, []);

    const pollSession = useCallback(async () => {
        if (!sessionId || !isPolling) return;

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/session/${sessionId}`);
            const data = await response.json();

            if (data.status === 'completed' && data.materials?.length > 0) {
                setIsPolling(false);
                setMobileStatus('done');
                // Trigger upload complete with the first material for now
                onUploadComplete(data.materials[0]);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, [sessionId, isPolling, onUploadComplete]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isPolling) {
            interval = setInterval(pollSession, 3000);
        }
        return () => clearInterval(interval);
    }, [isPolling, pollSession]);

    const handleUpload = async (file: File) => {
        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        if (sessionId) formData.append('session_id', sessionId);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/aiexaminer/api/v1'}/upload/`, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            onUploadComplete(data);
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
            {/* Desktop Upload */}
            <div
                className={`premium-card p-12 flex flex-col items-center justify-center min-h-[380px] cursor-pointer group
          ${dragActive ? 'border-accent bg-accent-muted ring-4 ring-accent-muted' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => { e.preventDefault(); setDragActive(false); if (e.target instanceof HTMLInputElement && e.target.files?.[0]) handleUpload(e.target.files[0]); }}
                onClick={() => {
                    const input = document.getElementById('file-upload') as HTMLInputElement;
                    input?.click();
                }}
            >
                <div className="p-5 rounded-2xl bg-primary-muted text-primary mb-6 group-hover:bg-primary group-hover:text-white transition-all duration-500">
                    {isUploading ? <div className="animate-spin"><RotateCcw size={36} /></div> : <Upload size={36} />}
                </div>
                <h3 className="text-2xl font-extrabold mb-3 text-primary text-center">Reference Materials</h3>
                <p className="text-slate-500 text-center mb-8 max-w-xs font-medium">
                    Drag and drop textbooks, lecture notes, or handwritten papers (PDF, PNG, JPG)
                </p>
                <div className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95">
                    {isUploading ? 'Processing...' : 'Select Source File'}
                </div>
                <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
                />
            </div>

            {/* Mobile Integration Handoff */}
            <div className="premium-card p-12 flex flex-col items-center justify-center relative overflow-hidden bg-white/40">
                <div className="absolute -top-10 -right-10 opacity-5">
                    <Smartphone size={240} />
                </div>

                <div className="p-5 rounded-2xl bg-accent-muted text-accent mb-6">
                    <Smartphone size={36} />
                </div>
                <h3 className="text-2xl font-extrabold mb-3 text-primary">Mobile Bridge</h3>
                <p className="text-slate-500 text-center mb-10 max-w-xs font-medium">
                    Instantly digitize physical worksheets using your phone's high-res camera.
                </p>

                <div className={`bg-white p-5 rounded-[32px] shadow-2xl shadow-accent-muted border border-accent-muted mb-8 group hover:scale-105 transition-transform duration-500 ${mobileStatus === 'done' ? 'border-success' : ''}`}>
                    {qrCode ? (
                        <div className="w-36 h-36 flex items-center justify-center rounded-2xl overflow-hidden shadow-inner bg-slate-50 relative">
                            {mobileStatus === 'done' ? (
                                <div className="absolute inset-0 bg-success/10 flex items-center justify-center text-success animate-fade-in">
                                    <CheckCircle2 size={48} />
                                </div>
                            ) : null}
                            <img src={qrCode} alt="Sync QR Code" className={`w-full h-full object-contain p-2 ${mobileStatus === 'done' ? 'opacity-20 blur-sm' : ''}`} />
                        </div>
                    ) : (
                        <div className="w-36 h-36 bg-slate-50 flex items-center justify-center rounded-2xl border-2 border-dashed border-accent-muted animate-pulse">
                            <div className="grid grid-cols-3 gap-2 p-4">
                                {[...Array(9)].map((_, i) => (
                                    <div key={i} className="w-6 h-6 bg-primary/20 rounded-md"></div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <div className={`flex items-center gap-3 text-sm font-bold px-4 py-2 rounded-full transition-all ${mobileStatus === 'done' ? 'bg-success/10 text-success' : 'bg-accent-muted text-accent'}`}>
                    {mobileStatus === 'done' ? <CheckCircle2 size={18} /> : <Camera size={18} />}
                    <span>{mobileStatus === 'done' ? 'Sync Completed' : 'Scan to Sync Device'}</span>
                </div>
            </div>
        </div>
    );
}
