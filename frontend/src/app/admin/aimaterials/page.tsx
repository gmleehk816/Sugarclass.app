"use client";

import React, { useState, useEffect } from 'react';
import { serviceFetch } from '@/lib/microservices';
import {
    Upload,
    Book,
    Zap,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Clock,
    Search,
    Terminal,
    LayoutDashboard,
    Database,
    Trash2,
    AlertTriangle
} from "lucide-react";

const AIMaterialsAdmin = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [subjectName, setSubjectName] = useState('IB DP Chemistry');
    const [syllabus, setSyllabus] = useState('IB Diploma');
    const [uploading, setUploading] = useState(false);
    const [tasks, setTasks] = useState<Record<string, any>>({});
    const [statusMessage, setStatusMessage] = useState('');
    const [subtopicId, setSubtopicId] = useState('');
    const [loadingTasks, setLoadingTasks] = useState(false);
    const [activeTab, setActiveTab] = useState<'uploader' | 'database'>('uploader');
    const [subjects, setSubjects] = useState<any[]>([]);
    const [loadingSubjects, setLoadingSubjects] = useState(false);

    const fetchTasks = async () => {
        try {
            const data = await serviceFetch('aimaterials', '/api/admin/tasks');
            setTasks(data);
        } catch (err) {
            console.error('Error fetching tasks', err);
        }
    };

    const fetchSubjects = async () => {
        setLoadingSubjects(true);
        try {
            const data = await serviceFetch('aimaterials', '/api/db/subjects');
            setSubjects(data);
        } catch (err) {
            console.error('Error fetching subjects', err);
        } finally {
            setLoadingSubjects(false);
        }
    };

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (activeTab === 'database') {
            fetchSubjects();
        }
    }, [activeTab]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleUploadAndIngest = async () => {
        if (files.length === 0) {
            setStatusMessage('Please select at least one markdown file.');
            return;
        }

        const mdFile = files.find(f => f.name.endsWith('.md'));
        if (!mdFile) {
            setStatusMessage('At least one .md file is required for ingestion.');
            return;
        }

        setUploading(true);
        setStatusMessage('Uploading files...');

        try {
            const formData = new FormData();
            files.forEach(f => {
                formData.append('files', f);
            });

            const uploadRes = await serviceFetch('aimaterials', '/api/admin/upload', {
                method: 'POST',
                body: formData
            });

            // Extract suggested metadata from upload response
            const extractedSubject = uploadRes.suggested_subject || subjectName;
            const extractedSyllabus = uploadRes.suggested_syllabus || syllabus;

            // Auto-populate form fields for visual feedback
            if (uploadRes.suggested_subject) {
                setSubjectName(uploadRes.suggested_subject);
            }
            if (uploadRes.suggested_syllabus) {
                setSyllabus(uploadRes.suggested_syllabus);
            }

            setStatusMessage('Upload successful. Starting ingestion...');

            // Use the extracted values directly (not state, which updates async)
            const ingestRes = await serviceFetch('aimaterials', '/api/admin/ingest', {
                method: 'POST',
                body: JSON.stringify({
                    batch_id: uploadRes.batch_id,
                    filename: uploadRes.main_markdown || mdFile.name,
                    subject_name: extractedSubject,
                    syllabus: extractedSyllabus
                })
            });

            setStatusMessage(`Ingestion started! Task ID: ${ingestRes.task_id}`);
            fetchTasks();
            setFiles([]); // Clear after success
        } catch (err: any) {
            console.error('Error in upload/ingest', err);
            setStatusMessage(`Error: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleGenerateExercises = async () => {
        if (!subtopicId) {
            setStatusMessage('Please enter a subtopic ID.');
            return;
        }

        try {
            const res = await serviceFetch('aimaterials', '/api/admin/generate-exercises', {
                method: 'POST',
                body: JSON.stringify({
                    subtopic_id: subtopicId,
                    generate_images: true
                })
            });
            setStatusMessage(`Exercise generation started! Task ID: ${res.task_id}`);
            fetchTasks();
        } catch (err: any) {
            console.error('Error generating exercises', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    const handleDeleteSubject = async (subjectId: string) => {
        if (!confirm(`Are you sure you want to delete "${subjectId}"? This will recursively delete all topics, subtopics, content, and exercises. This action CANNOT be undone.`)) {
            return;
        }

        try {
            const res = await serviceFetch('aimaterials', `/api/admin/db/subjects/${subjectId}`, {
                method: 'DELETE'
            });
            setStatusMessage(`Subject deleted: ${res.message}`);
            fetchSubjects();
        } catch (err: any) {
            console.error('Error deleting subject', err);
            setStatusMessage(`Error: ${err.message}`);
        }
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 350px', gap: '40px', alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                {/* Tab Navigation */}
                <div style={{ display: 'flex', gap: '8px', background: '#f1f5f9', padding: '6px', borderRadius: '12px', width: 'fit-content' }}>
                    <button
                        onClick={() => setActiveTab('uploader')}
                        style={{
                            ...tabButtonStyle,
                            background: activeTab === 'uploader' ? 'white' : 'transparent',
                            boxShadow: activeTab === 'uploader' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                            color: activeTab === 'uploader' ? '#1e293b' : '#64748b'
                        }}
                    >
                        <Upload size={16} /> Uploader
                    </button>
                    <button
                        onClick={() => setActiveTab('database')}
                        style={{
                            ...tabButtonStyle,
                            background: activeTab === 'database' ? 'white' : 'transparent',
                            boxShadow: activeTab === 'database' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                            color: activeTab === 'database' ? '#1e293b' : '#64748b'
                        }}
                    >
                        <Database size={16} /> Database
                    </button>
                </div>

                {activeTab === 'uploader' ? (
                    <>
                        {/* Upload & Ingest Section */}
                        <div style={cardStyle}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                <div style={{ background: '#fef3c7', padding: '8px', borderRadius: '8px' }}>
                                    <Book size={20} color="#d97706" />
                                </div>
                                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Ingest New Textbook</h2>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                                <div style={inputGroupStyle}>
                                    <label style={labelStyle}>Subject Name</label>
                                    <input
                                        style={inputStyle}
                                        type="text"
                                        value={subjectName}
                                        onChange={(e) => setSubjectName(e.target.value)}
                                    />
                                </div>
                                <div style={inputGroupStyle}>
                                    <label style={labelStyle}>Syllabus</label>
                                    <input
                                        style={inputStyle}
                                        type="text"
                                        value={syllabus}
                                        onChange={(e) => setSyllabus(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div style={{ marginBottom: '24px' }}>
                                <label style={labelStyle}>Textbook Markdown (.md)</label>
                                <div style={{
                                    border: '2px dashed #e2e8f0',
                                    borderRadius: '12px',
                                    padding: '32px',
                                    textAlign: 'center',
                                    cursor: 'pointer',
                                    transition: 'border-color 0.2s',
                                }}>
                                    <input
                                        type="file"
                                        accept=".md,.json"
                                        multiple
                                        onChange={handleFileChange}
                                        style={{ display: 'none' }}
                                        id="file-upload"
                                    />
                                    <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
                                        <Upload size={40} color="#94a3b8" style={{ marginBottom: '12px' }} />
                                        <div style={{ fontWeight: 600, color: '#475569' }}>
                                            {files.length > 0 ? (
                                                <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0' }}>
                                                    {files.map((f, i) => (
                                                        <li key={i} style={{ fontSize: '0.9rem', color: '#1e293b' }}>
                                                            {f.name.endsWith('.md') ? '📖 ' : '⚙️ '} {f.name}
                                                        </li>
                                                    ))}
                                                </ul>
                                            ) : "Click to select markdown & structure JSON"}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Select textbook (.md) and optionally .structure.json</div>
                                    </label>
                                </div>
                            </div>

                            <button
                                onClick={handleUploadAndIngest}
                                disabled={uploading || files.length === 0}
                                style={{
                                    ...buttonStyle,
                                    background: uploading || files.length === 0 ? '#94a3b8' : '#1e293b',
                                }}
                            >
                                {uploading ? (
                                    <><RefreshCw size={18} className="animate-spin" /> Processing...</>
                                ) : (
                                    <><Zap size={18} /> Upload & Process Content</>
                                )}
                            </button>
                        </div>

                        {/* Status Message */}
                        {statusMessage && (
                            <div style={{
                                padding: '16px',
                                background: '#f0f9ff',
                                borderLeft: '4px solid #0ea5e9',
                                borderRadius: '8px',
                                fontSize: '0.9rem',
                                fontWeight: 500,
                                color: '#0369a1'
                            }}>
                                {statusMessage}
                            </div>
                        )}

                        {/* Exercise Generation Section */}
                        <div style={cardStyle}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                <div style={{ background: '#dcfce7', padding: '8px', borderRadius: '8px' }}>
                                    <Zap size={20} color="#166534" />
                                </div>
                                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Exercise Generation</h2>
                            </div>

                            <div style={{ ...inputGroupStyle, marginBottom: '24px' }}>
                                <label style={labelStyle}>Subtopic ID</label>
                                <div style={{ position: 'relative' }}>
                                    <Search size={18} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '13px' }} />
                                    <input
                                        style={{ ...inputStyle, paddingLeft: '40px' }}
                                        type="text"
                                        placeholder="e.g. ib_dp_chemistry_3.7"
                                        value={subtopicId}
                                        onChange={(e) => setSubtopicId(e.target.value)}
                                    />
                                </div>
                            </div>

                            <button
                                onClick={handleGenerateExercises}
                                style={{ ...buttonStyle, background: '#927559' }}
                            >
                                Generate MCQs with AI Images
                            </button>
                        </div>
                    </>
                ) : (
                    /* Database Management Section */
                    <div style={cardStyle}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div style={{ background: '#dbeafe', padding: '8px', borderRadius: '8px' }}>
                                    <Database size={20} color="#2563eb" />
                                </div>
                                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Database Management</h2>
                            </div>
                            <button
                                onClick={fetchSubjects}
                                style={{ padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0', background: 'white', cursor: 'pointer' }}
                                disabled={loadingSubjects}
                            >
                                <RefreshCw size={16} color="#64748b" className={loadingSubjects ? "animate-spin" : ""} />
                            </button>
                        </div>

                        {/* HIGH IMPORTANCE WARNING */}
                        <div style={{
                            background: '#fff7ed',
                            border: '1px solid #ffedd5',
                            borderRadius: '12px',
                            padding: '16px',
                            marginBottom: '24px',
                            display: 'flex',
                            gap: '12px',
                            alignItems: 'start'
                        }}>
                            <AlertTriangle size={20} color="#ea580c" style={{ marginTop: '2px', flexShrink: 0 }} />
                            <div>
                                <h4 style={{ color: '#9a3412', fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>Unified Database Warning</h4>
                                <p style={{ color: '#c2410c', fontSize: '0.85rem', lineHeight: '1.4' }}>
                                    This database is unified between <strong>AI Materials</strong> and <strong>AI Tutor</strong>.
                                    Deleting subjects here will remove them from the AI Tutor as well.
                                </p>
                            </div>
                        </div>

                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                                        <th style={{ padding: '12px 8px', fontSize: '0.85rem', color: '#64748b' }}>SUBJECT NAME</th>
                                        <th style={{ padding: '12px 8px', fontSize: '0.85rem', color: '#64748b' }}>TOPICS</th>
                                        <th style={{ padding: '12px 8px', fontSize: '0.85rem', color: '#64748b' }}>SUBTOPICS</th>
                                        <th style={{ padding: '12px 8px', fontSize: '0.85rem', color: '#64748b', textAlign: 'right' }}>ACTIONS</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {subjects.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} style={{ padding: '32px', textAlign: 'center', color: '#94a3b8' }}>
                                                {loadingSubjects ? "Loading subjects..." : "No subjects found in database."}
                                            </td>
                                        </tr>
                                    ) : (
                                        subjects.map((sub: any) => (
                                            <tr key={sub.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                <td style={{ padding: '16px 8px', fontWeight: 600, fontSize: '0.9rem' }}>{sub.name}</td>
                                                <td style={{ padding: '16px 8px', fontSize: '0.85rem', color: '#475569' }}>{sub.topic_count}</td>
                                                <td style={{ padding: '16px 8px', fontSize: '0.85rem', color: '#475569' }}>{sub.subtopic_count}</td>
                                                <td style={{ padding: '16px 8px', textAlign: 'right' }}>
                                                    <button
                                                        onClick={() => handleDeleteSubject(sub.id)}
                                                        style={{
                                                            padding: '8px',
                                                            borderRadius: '8px',
                                                            border: 'none',
                                                            background: '#fee2e2',
                                                            color: '#dc2626',
                                                            cursor: 'pointer',
                                                            display: 'inline-flex',
                                                            alignItems: 'center',
                                                            gap: '6px',
                                                            fontSize: '0.8rem',
                                                            fontWeight: 600
                                                        }}
                                                    >
                                                        <Trash2 size={14} /> Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* Task monitor on the right */}
            <div style={{ ...cardStyle, border: 'none', background: '#f8fafc', position: 'sticky', top: '120px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Task Monitor</h3>
                    <RefreshCw size={16} color="#64748b" style={{ cursor: 'pointer' }} onClick={fetchTasks} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {Object.keys(tasks).length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <Clock size={32} color="#cbd5e1" style={{ marginBottom: '12px' }} />
                            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>No active tasks</div>
                        </div>
                    ) : (
                        Object.entries(tasks).map(([id, info]: [string, any]) => (
                            <div key={id} style={{
                                background: 'white',
                                padding: '16px',
                                borderRadius: '12px',
                                border: '1px solid #e2e8f0',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '8px'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'monospace', color: '#94a3b8' }}>#{id.slice(0, 8)}</span>
                                    {info.status === 'completed' && <CheckCircle2 size={16} color="#22c55e" />}
                                    {info.status === 'failed' && <XCircle size={16} color="#ef4444" />}
                                    {info.status === 'running' && <RefreshCw size={16} color="#3b82f6" className="animate-spin" />}
                                </div>
                                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>
                                    {info.status.charAt(0).toUpperCase() + info.status.slice(1)}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {info.status === 'running' ? 'Ingesting...' : info.message}
                                </div>

                                {info.logs && info.logs.length > 0 && (
                                    <div style={{
                                        marginTop: '12px',
                                        padding: '12px',
                                        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                                        borderRadius: '10px',
                                        minHeight: '200px',
                                        maxHeight: '300px',
                                        overflowY: 'auto',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '4px',
                                        boxShadow: info.status === 'running' ? '0 0 20px rgba(59, 130, 246, 0.3)' : 'none',
                                        border: info.status === 'running' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid #334155'
                                    }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
                                            <Terminal size={14} color={info.status === 'running' ? '#3b82f6' : '#94a3b8'} />
                                            <span style={{ fontSize: '0.75rem', color: info.status === 'running' ? '#3b82f6' : '#94a3b8', fontWeight: 700, letterSpacing: '0.05em' }}>LIVE LOGS</span>
                                            {info.status === 'running' && (
                                                <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: '#22c55e', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', animation: 'pulse 1.5s infinite' }}></span>
                                                    Processing
                                                </span>
                                            )}
                                        </div>
                                        {info.logs.slice(-15).map((log: string, i: number) => (
                                            <div key={i} style={{
                                                fontSize: '0.7rem',
                                                fontFamily: 'ui-monospace, monospace',
                                                color: i === info.logs.slice(-15).length - 1 ? '#22d3ee' : '#e2e8f0',
                                                opacity: i === info.logs.slice(-15).length - 1 ? 1 : 0.75,
                                                lineHeight: 1.5,
                                                paddingLeft: '8px',
                                                borderLeft: i === info.logs.slice(-15).length - 1 ? '2px solid #22d3ee' : '2px solid transparent'
                                            }}>
                                                {log}
                                            </div>
                                        ))}
                                        <div ref={(el) => { if (el) el.scrollIntoView({ behavior: 'smooth' }); }} />
                                    </div>
                                )}
                            </div>
                        )).reverse()
                    )}
                </div>
            </div>

        </div>
    );
};

const cardStyle = {
    background: 'white',
    padding: '32px',
    borderRadius: '24px',
    border: '1px solid #e2e8f0',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
};

const inputGroupStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
};

const labelStyle = {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#475569',
};

const inputStyle = {
    padding: '12px 16px',
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
    fontSize: '0.95rem',
    fontFamily: 'inherit',
    outline: 'none',
    transition: 'border-color 0.2s',
};

const buttonStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    padding: '14px 24px',
    borderRadius: '12px',
    color: 'white',
    fontWeight: 600,
    fontSize: '0.95rem',
    border: 'none',
    width: '100%',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

const tabButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    fontWeight: 600,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

export default AIMaterialsAdmin;
