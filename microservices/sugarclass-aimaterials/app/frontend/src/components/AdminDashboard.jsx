import React, { useState, useEffect } from 'react';
import { api } from '../api';

const AdminDashboard = () => {
    const [file, setFile] = useState(null);
    const [subjectName, setSubjectName] = useState('IB DP Chemistry');
    const [syllabus, setSyllabus] = useState('IB Diploma');
    const [uploading, setUploading] = useState(false);
    const [tasks, setTasks] = useState({});
    const [statusMessage, setStatusMessage] = useState('');
    const [subtopicId, setSubtopicId] = useState('');

    const fetchTasks = async () => {
        try {
            const res = await api.get('/api/admin/tasks');
            setTasks(res.data);
        } catch (err) {
            console.error('Error fetching tasks', err);
        }
    };

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUploadAndIngest = async () => {
        if (!file) {
            setStatusMessage('Please select a file first.');
            return;
        }

        setUploading(true);
        setStatusMessage('Uploading...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const uploadRes = await api.post('/api/admin/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setStatusMessage('Upload successful. Starting ingestion...');

            const ingestRes = await api.post('/api/admin/ingest', {
                filename: uploadRes.data.filename,
                subject_name: subjectName,
                syllabus: syllabus
            });

            setStatusMessage(`Ingestion started! Task ID: ${ingestRes.data.task_id}`);
            fetchTasks();
        } catch (err) {
            console.error('Error in upload/ingest', err);
            setStatusMessage(`Error: ${err.response?.data?.detail || err.message}`);
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
            const res = await api.post('/api/admin/generate-exercises', {
                subtopic_id: subtopicId,
                generate_images: true
            });
            setStatusMessage(`Exercise generation started! Task ID: ${res.data.task_id}`);
            fetchTasks();
        } catch (err) {
            console.error('Error generating exercises', err);
            setStatusMessage(`Error: ${err.response?.data?.detail || err.message}`);
        }
    };

    return (
        <div className="materials-main">
            <div className="content-header">
                <h1>Admin Dashboard</h1>
                <p>Manage textbooks, ingestion, and exercise generation</p>
            </div>

            <div className="content-body">
                {/* Upload Section */}
                <div className="content-card animate-fade-in" style={{ marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', color: 'var(--primary)' }}>Upload & Ingest Textbook</h2>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Subject Name</label>
                            <input
                                type="text"
                                value={subjectName}
                                onChange={(e) => setSubjectName(e.target.value)}
                                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border)' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Syllabus</label>
                            <input
                                type="text"
                                value={syllabus}
                                onChange={(e) => setSyllabus(e.target.value)}
                                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border)' }}
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Textbook Markdown File</label>
                        <input type="file" accept=".md" onChange={handleFileChange} />
                    </div>

                    <button
                        className="btn-primary"
                        onClick={handleUploadAndIngest}
                        disabled={uploading || !file}
                    >
                        {uploading ? 'Processing...' : 'Upload & Start Ingestion'}
                    </button>
                </div>

                {/* Exercise Generation Section */}
                <div className="content-card animate-fade-in" style={{ marginBottom: '24px' }}>
                    <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', color: 'var(--primary)' }}>Manual Exercise Generation</h2>
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Subtopic ID (e.g. ib_dp_chemistry_3.7)</label>
                        <input
                            type="text"
                            value={subtopicId}
                            onChange={(e) => setSubtopicId(e.target.value)}
                            placeholder="Enter full subtopic ID"
                            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border)' }}
                        />
                    </div>
                    <button className="btn-secondary" onClick={handleGenerateExercises}>
                        Generate 5 MCQs with Images
                    </button>
                </div>

                {statusMessage && (
                    <div style={{
                        padding: '12px',
                        background: 'rgba(14, 165, 233, 0.1)',
                        borderLeft: '4px solid var(--accent)',
                        borderRadius: '4px',
                        marginBottom: '24px'
                    }}>
                        {statusMessage}
                    </div>
                )}

                {/* Task Monitor Section */}
                <div className="content-card animate-fade-in">
                    <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', color: 'var(--primary)' }}>Background Tasks Status</h2>
                    {Object.keys(tasks).length === 0 ? (
                        <p style={{ color: 'var(--primary-light)', fontSize: '0.9rem' }}>No active or past tasks found.</p>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
                                        <th style={{ padding: '8px' }}>Task ID</th>
                                        <th style={{ padding: '8px' }}>Status</th>
                                        <th style={{ padding: '8px' }}>Message</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(tasks).map(([id, info]) => (
                                        <tr key={id} style={{ borderBottom: '1px solid var(--border)' }}>
                                            <td style={{ padding: '8px', fontSize: '0.75rem', fontFamily: 'monospace' }}>{id.slice(0, 8)}...</td>
                                            <td style={{ padding: '8px' }}>
                                                <span style={{
                                                    padding: '2px 8px',
                                                    borderRadius: '12px',
                                                    fontSize: '0.75rem',
                                                    background: info.status === 'completed' ? 'var(--success-muted)' :
                                                        info.status === 'failed' ? 'var(--error-muted)' : 'var(--accent-muted)',
                                                    color: info.status === 'completed' ? 'var(--success)' :
                                                        info.status === 'failed' ? 'var(--error)' : 'var(--accent)'
                                                }}>
                                                    {info.status}
                                                </span>
                                            </td>
                                            <td style={{ padding: '8px' }}>{info.message}</td>
                                        </tr>
                                    )).reverse()}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
