"use client";

import React from 'react';
import {
    Library,
    BookOpen,
    PenTool,
    FileSearch,
    ShieldCheck,
    Zap,
    Clock,
    AlertCircle
} from "lucide-react";

const AdminDashboard = () => {
    const services = [
        {
            name: "AI Materials",
            id: "aimaterials",
            icon: Library,
            status: "active",
            stats: { lessons: 13, exercises: 0, pending: 0 },
            path: "/admin/aimaterials",
            color: "#927559"
        },
        {
            name: "AI Teacher",
            id: "tutor",
            icon: BookOpen,
            status: "coming-soon",
            stats: { users: 0, chats: 0 },
            path: "#",
            color: "#64748b"
        },
        {
            name: "Writing Hub",
            id: "writer",
            icon: PenTool,
            status: "coming-soon",
            stats: { articles: 0, sources: 0 },
            path: "#",
            color: "#64748b"
        },
        {
            name: "AI Examiner",
            id: "examiner",
            icon: FileSearch,
            status: "coming-soon",
            stats: { exams: 0, questions: 0 },
            path: "#",
            color: "#64748b"
        }
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
            {/* Stats Overview */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
                <div style={statCardStyle}>
                    <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '12px', borderRadius: '12px' }}>
                        <Zap size={24} color="#3b82f6" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>99.9%</div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>System Uptime</div>
                    </div>
                </div>
                <div style={statCardStyle}>
                    <div style={{ background: 'rgba(34, 197, 94, 0.1)', padding: '12px', borderRadius: '12px' }}>
                        <Clock size={24} color="#22c55e" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>124 ms</div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>Avg Response Time</div>
                    </div>
                </div>
                <div style={statCardStyle}>
                    <div style={{ background: 'rgba(146, 117, 89, 0.1)', padding: '12px', borderRadius: '12px' }}>
                        <Library size={24} color="#927559" />
                    </div>
                    <div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>13</div>
                        <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>Ingested Lessons</div>
                    </div>
                </div>
            </div>

            {/* Service Grid */}
            <div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '24px', color: '#1e293b' }}>Active & Planned Services</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
                    {services.map((service) => (
                        <div key={service.id} style={{
                            background: 'white',
                            border: '1px solid #e2e8f0',
                            borderRadius: '20px',
                            padding: '32px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '24px',
                            transition: 'all 0.3s ease',
                            cursor: service.status === 'coming-soon' ? 'default' : 'pointer'
                        }}
                            onMouseEnter={(e) => {
                                if (service.status !== 'coming-soon') {
                                    e.currentTarget.style.transform = 'translateY(-4px)';
                                    e.currentTarget.style.boxShadow = '0 12px 30px -5px rgba(0, 0, 0, 0.05)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                            onClick={() => {
                                if (service.status !== 'coming-soon') {
                                    window.location.href = service.path;
                                }
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div style={{
                                    background: `${service.color}15`,
                                    padding: '16px',
                                    borderRadius: '16px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}>
                                    <service.icon size={32} color={service.color} />
                                </div>
                                <div style={{
                                    fontSize: '0.65rem',
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    padding: '4px 10px',
                                    borderRadius: '100px',
                                    background: service.status === 'active' ? '#dcfce7' : '#f1f5f9',
                                    color: service.status === 'active' ? '#166534' : '#64748b',
                                }}>
                                    {service.status === 'active' ? 'Active' : 'Coming Soon'}
                                </div>
                            </div>

                            <div>
                                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>{service.name}</h3>
                                <p style={{ fontSize: '0.9rem', color: '#64748b', lineHeight: 1.5 }}>
                                    {service.status === 'active'
                                        ? `Manage ${service.name} content, users, and background tasks.`
                                        : `Unified management for ${service.name} is currently under development.`}
                                </p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', borderTop: '1px solid #f1f5f9', paddingTop: '16px' }}>
                                {Object.entries(service.stats).map(([k, v]) => (
                                    <div key={k}>
                                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'capitalize' }}>{k}</div>
                                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#334155' }}>{v}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Quick Actions / Activity */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '20px', padding: '32px' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px' }}>Recent Management Actions</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {[
                            { action: "Chemistry Textbook Ingestion", date: "2 hours ago", status: "Completed" },
                            { action: "Modified Topic: Organic Chemistry", date: "5 hours ago", status: "Saved" },
                            { action: "Admin Panel User Session", date: "Today, 4:18 PM", status: "Active" }
                        ].map((log, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', borderRadius: '12px', background: '#f8fafc' }}>
                                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></div>
                                    <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{log.action}</div>
                                </div>
                                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{log.date}</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '20px', padding: '32px', color: 'white' }}>
                    <ShieldCheck size={40} color="#927559" style={{ marginBottom: '20px' }} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>Security Status</h3>
                    <p style={{ fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.6)', marginBottom: '24px' }}>
                        Unified Admin access is restricted to authorized credentials.
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span>Last login</span>
                            <span style={{ color: 'var(--accent)' }}>Today, 4:18 PM</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span>Active Sessions</span>
                            <span style={{ color: 'var(--accent)' }}>1 Active</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const statCardStyle = {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: '20px',
    padding: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '20px'
};

export default AdminDashboard;
