"use client";

import React from 'react';
import {
    Library,
    Users,
    Server,
    Settings,
    ArrowRight,
    Search,
    Activity,
    Database,
    ShieldCheck
} from 'lucide-react';
import Link from 'next/link';
import AdminHub from '@/components/AdminHub';

export default function AdminDashboard() {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            {/* Real-time Status Overlay (Subtle) */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 24px',
                background: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)',
                borderRadius: '16px',
                color: 'white',
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: '#10b981',
                        boxShadow: '0 0 10px #10b981'
                    }} className="animate-pulse" />
                    <div>
                        <p style={{ fontSize: '0.8rem', opacity: 0.8, margin: 0 }}>System Health</p>
                        <p style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0 }}>All Microservices Operational</p>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '24px' }}>
                    <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: '0.8rem', opacity: 0.8, margin: 0 }}>Active Users</p>
                        <p style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0 }}>128</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: '0.8rem', opacity: 0.8, margin: 0 }}>API Requests (1h)</p>
                        <p style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0 }}>4.2k</p>
                    </div>
                </div>
            </div>

            {/* Main Hub Section */}
            <AdminHub />

            {/* Direct Deep Links Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                <Link href="/admin/aimaterials" style={cardLinkStyle}>
                    <div style={{ ...iconWrapperStyle, background: '#f3e8ff', color: '#7e22ce' }}>
                        <Library size={20} />
                    </div>
                    <div>
                        <h3 style={cardTitleStyle}>Content Ingestion</h3>
                        <p style={cardDescStyle}>Upload textbooks and syllabus files for AI processing.</p>
                    </div>
                    <ArrowRight size={18} className="arrow-icon" style={arrowIconStyle} />
                </Link>

                <Link href="/admin/aimaterials?tab=database" style={cardLinkStyle}>
                    <div style={{ ...iconWrapperStyle, background: '#dcfce7', color: '#16a34a' }}>
                        <Database size={20} />
                    </div>
                    <div>
                        <h3 style={cardTitleStyle}>Knowledge Base</h3>
                        <p style={cardDescStyle}>Browse and refine the generated subject hierarchies.</p>
                    </div>
                    <ArrowRight size={18} className="arrow-icon" style={arrowIconStyle} />
                </Link>

                <Link href="/admin/logs" style={cardLinkStyle}>
                    <div style={{ ...iconWrapperStyle, background: '#fee2e2', color: '#dc2626' }}>
                        <Activity size={20} />
                    </div>
                    <div>
                        <h3 style={cardTitleStyle}>Microservice Health</h3>
                        <p style={cardDescStyle}>View logs and error traces across all services.</p>
                    </div>
                    <ArrowRight size={18} className="arrow-icon" style={arrowIconStyle} />
                </Link>

                <Link href="/admin/users" style={cardLinkStyle}>
                    <div style={{ ...iconWrapperStyle, background: '#e0f2fe', color: '#0284c7' }}>
                        <Users size={20} />
                    </div>
                    <div>
                        <h3 style={cardTitleStyle}>User Directory</h3>
                        <p style={cardDescStyle}>Manage teacher accounts and student permissions.</p>
                    </div>
                    <ArrowRight size={18} className="arrow-icon" style={arrowIconStyle} />
                </Link>
            </div>

            <style>{`
                .arrow-icon {
                    transition: transform 0.2s ease;
                }
                a:hover .arrow-icon {
                    transform: translateX(4px);
                }
            `}</style>
        </div>
    );
}

const cardLinkStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '20px',
    background: 'white',
    borderRadius: '16px',
    border: '1px solid #e2e8f0',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'all 0.2s ease',
    position: 'relative',
    boxShadow: '0 1px 3px rgba(0,0,0,0.02)'
};

const iconWrapperStyle: React.CSSProperties = {
    padding: '12px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
};

const cardTitleStyle: React.CSSProperties = {
    fontSize: '1rem',
    fontWeight: 700,
    margin: 0,
    color: '#1e293b'
};

const cardDescStyle: React.CSSProperties = {
    fontSize: '0.85rem',
    color: '#64748b',
    margin: '4px 0 0 0',
    lineHeight: 1.4
};

const arrowIconStyle: React.CSSProperties = {
    marginLeft: 'auto',
    color: '#cbd5e1'
};
