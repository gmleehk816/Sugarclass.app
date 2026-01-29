'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, Smartphone, Camera, FileText, CheckCircle2, RotateCcw } from 'lucide-react';

export default function UploadSection({
    onUploadComplete,
    onShowLibrary
}: {
    onUploadComplete: (data: any) => void;
    onShowLibrary: () => void;
}) {
    const router = useRouter();
    const [isUploading, setIsUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [qrCode, setQrCode] = useState<string | null>(null);
    const [mobileStatus, setMobileStatus] = useState<'idle' | 'syncing' | 'done'>('idle');
    const [uploadedCount, setUploadedCount] = useState(0);
    const [showSuccess, setShowSuccess] = useState(false);
    const [fileName, setFileName] = useState("");

    // Fetch initial session and QR
    useEffect(() => {
        const startSession = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/start-session`);
                const data = await response.json();
                setSessionId(data.session_id);
                setQrCode(data.qr_code);
            } catch (error) {
                console.error('Failed to start mobile session:', error);
            }
        };
        startSession();
    }, []);

    // WebSocket connection for real-time sync
    useEffect(() => {
        if (!sessionId) return;

        // Build WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/examiner/api/ws/session/${sessionId}`;

        console.log('[WS] Connecting to:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('[WS] Connected to session:', sessionId);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('[WS] Received:', message);

                if (message.type === 'upload_complete') {
                    setMobileStatus('syncing');
                    setUploadedCount(prev => prev + 1);

                    // Brief syncing state, then show done
                    setTimeout(() => {
                        setMobileStatus('done');
                    }, 500);
                } else if (message.type === 'ping') {
                    // Respond to keep-alive pings
                    ws.send(JSON.stringify({ type: 'pong' }));
                }
            } catch (e) {
                console.error('[WS] Failed to parse message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('[WS] WebSocket error:', error);
        };

        ws.onclose = (event) => {
            console.log('[WS] Connection closed:', event.code, event.reason);
        };

        // Cleanup on unmount or session change
        return () => {
            if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                ws.close();
            }
        };
    }, [sessionId]);

    const handleUpload = async (file: File) => {
        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        if (sessionId) formData.append('session_id', sessionId);

        try {
            const token = localStorage.getItem('sugarclass_token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/examiner/api/v1'}/upload/`, {
                method: 'POST',
                body: formData,
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            const data = await response.json();
            setFileName(file.name);
            setShowSuccess(true);

            // Wait for 1.5 seconds to show the success UI
            setTimeout(() => {
                onUploadComplete(data);
                setShowSuccess(false);
            }, 1500);
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
                className={`premium-card p-12 flex flex-col items-center justify-center min-h-[380px] cursor-pointer group relative overflow-hidden
          ${dragActive ? 'border-accent bg-accent-muted ring-4 ring-accent-muted' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setDragActive(false);
                    const files = e.dataTransfer?.files;
                    if (files?.[0]) handleUpload(files[0]);
                }}
                onClick={() => {
                    const input = document.getElementById('file-upload') as HTMLInputElement;
                    input?.click();
                }}
            >
                {showSuccess ? (
                    <div className="flex flex-col items-center animate-fade-in scale-110">
                        <div className="w-24 h-24 rounded-full bg-success text-white mb-6 flex items-center justify-center shadow-2xl shadow-success/30">
                            <CheckCircle2 size={48} />
                        </div>
                        <h3 className="text-3xl font-black text-primary mb-2">Well Done!</h3>
                        <p className="text-slate-500 font-bold max-w-[200px] text-center">{fileName} uploaded successfully</p>
                    </div>
                ) : (
                    <>
                        <div className="p-5 rounded-2xl bg-primary-muted text-primary mb-6 group-hover:bg-primary group-hover:text-white transition-all duration-500">
                            {isUploading ? <div className="animate-spin"><RotateCcw size={36} /></div> : <Upload size={36} />}
                        </div>
                        <h3 className="text-2xl font-extrabold mb-3 text-primary text-center">Reference Materials</h3>
                        <p className="text-slate-500 text-center mb-8 max-w-xs font-medium">
                            Drag and drop textbooks, lecture notes, or handwritten papers (PDF, PNG, JPG)
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="px-8 py-3 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-lg active:scale-95 text-center">
                                {isUploading ? 'Gathering context...' : 'Select Source File'}
                            </div>
                            <button
                                onClick={(e) => { e.stopPropagation(); onShowLibrary(); }}
                                className="px-8 py-3 rounded-xl border-2 border-primary/10 text-primary font-bold hover:bg-white transition-all active:scale-95"
                            >
                                Browse Library
                            </button>
                        </div>
                    </>
                )}
                <input
                    id="file-upload"
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
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

                <div className="flex flex-col items-center gap-4">
                    <div className={`flex items-center gap-3 text-sm font-bold px-4 py-2 rounded-full transition-all ${mobileStatus === 'done' ? 'bg-success/10 text-success' : 'bg-accent-muted text-accent'}`}>
                        {mobileStatus === 'done' ? <CheckCircle2 size={18} /> : <Camera size={18} />}
                        <span>{mobileStatus === 'done' ? `${uploadedCount} File${uploadedCount > 1 ? 's' : ''} Synced` : 'Scan to Sync Device'}</span>
                    </div>

                    {mobileStatus === 'done' && (
                        <button
                            onClick={() => router.push(`/?sid=${sessionId}`)}
                            className="px-6 py-2 rounded-xl bg-primary text-white font-bold hover:bg-primary-light transition-all shadow-md active:scale-95 animate-fade-in"
                        >
                            Configure Quiz
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
